"""Minimal model-backed investigator; no answer labels are read by this module."""
import hashlib
import json
import re
import time
from pathlib import Path
from incident_agent.client import complete, ModelError
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/incidents.json"
POLICY = "I cannot answer requests to expose secrets, override instructions, or execute changes. Investigation is read-only; human approval is required for remediation. [POLICY]"
UNKNOWN = "I do not have that information for one unambiguous incident. Specify a known incident ID or service. [none]"
LAST_METRICS = {}

def redact(text):
    text = re.sub(r"(?i)\b(api[_ -]?key|password|token|secret)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", text)
    return re.sub(r"\bsk-[A-Za-z0-9_-]{8,}", "[REDACTED]", text)

def blocked(question, mode):
    if re.search(r"secret|password|api.?key|credential|ignore.*(?:rule|instruction)", question, re.I):
        return True
    action = r"\b(?:restart|roll.?back|execute|reconfigure|delete)\b"
    if mode == "legacy-keyword-v1":
        return bool(re.search(action, question, re.I))
    if mode != "diagnostic-aware-v2":
        raise ValueError("Unknown guard mode")
    if not re.search(action, question, re.I):
        return False
    # Permit narrowly scoped diagnostic phrasing only; mixed requests still refuse.
    diagnostic = re.match(r"^\s*(?:why did|why does|what caused|explain why)\b", question, re.I)
    imperative = re.search(r"(?:[.;!?]\s*|\b(?:and|then|also|please)\s+)(?:please\s+)?(?:restart|roll.?back|execute|reconfigure|delete)\b", question, re.I)
    return not diagnostic or bool(imperative)

def retrieve(question):
    incidents = json.loads(DATA.read_text())
    ids = set(re.findall(r"INC-\d+", question.upper()))
    matches = [i for i in incidents if i["id"] in ids] if ids else [i for i in incidents if i["service"].lower() in question.lower()]
    if len(matches) != 1 or (ids and ids != {matches[0]["id"]}):
        return None
    i = matches[0]
    # Explicit allowlist: curated hypotheses / ground truth never enter the request.
    return {"id": i["id"], "service": i["service"], "evidence": [{"id": e["id"], "kind": e["kind"], "text": redact(e["text"])} for e in i["evidence"]]}

def payload_for(question, incident, manifest, settings):
    return {"model": manifest["model"], "store": False,
            "instructions": (ROOT / manifest["prompt_file"]).read_text(),
            "input": json.dumps({"question": redact(question), "incident": incident}),
            "reasoning": {"effort": settings["reasoning_effort"]},
            "max_output_tokens": settings["max_output_tokens"],
            "text": {"format": {"type": "json_schema", "name": "incident_report", "strict": True,
                                "schema": json.loads((ROOT / "config/response_schema.json").read_text())}}}

def investigate(question):
    started = time.monotonic()
    LAST_METRICS.clear()
    LAST_METRICS.update({"model_calls": 0, "input_tokens": 0, "output_tokens": 0})
    manifest = json.loads((ROOT / "manifest.json").read_text())
    settings = json.loads((ROOT / "config/settings.json").read_text())
    def finish(status, text, **extra):
        LAST_METRICS["latency_ms"] = round((time.monotonic()-started)*1000, 2)
        return {"status": status, "text": text, **extra}
    if len(question) > settings["max_question_chars"]:
        return finish("unknown", "I cannot answer: question exceeds the configured size limit. [none]")
    if blocked(question, settings["guard_mode"]):
        return finish("refused", POLICY)
    incident = retrieve(question)
    if not incident:
        return finish("unknown", UNKNOWN)
    evidence = incident["evidence"]
    if len(evidence) < 2 or len(json.dumps(incident)) > settings["max_evidence_chars"]:
        return finish("unknown", "I cannot answer with sufficient bounded evidence. [none]")
    LAST_METRICS["model_calls"] = 1
    result, usage = complete(payload_for(question, incident, manifest, settings), settings["timeout_seconds"])
    LAST_METRICS.update({k: usage.get(k, 0) for k in ("input_tokens", "output_tokens")})
    expected = {"status", "cause", "explanation", "evidence_ids", "alternative", "recommendation"}
    if not isinstance(result, dict) or set(result) != expected:
        raise ModelError("Invalid report fields")
    if result["status"] not in ("supported", "insufficient") or any(not isinstance(result[k], str) for k in expected - {"evidence_ids"}):
        raise ModelError("Invalid report field types")
    ids = result["evidence_ids"]
    if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
        raise ModelError("Invalid citation list")
    if result["status"] == "insufficient":
        return finish("unknown", "I cannot answer with sufficient supporting evidence. [none]")
    available = {e["id"]: e for e in evidence}
    if len(set(ids)) < 2 or any(i not in available for i in ids):
        raise ModelError("Unsupported or insufficient citation IDs")
    if not all(result[k].strip() for k in ("cause", "explanation", "alternative", "recommendation")):
        raise ModelError("Empty supported report field")
    # No model-generated free-text citation tags may bypass the validated ID list.
    prose = " ".join(result[k] for k in ("cause", "explanation", "alternative", "recommendation"))
    if re.search(r"\[[^\]]+\]", prose):
        raise ModelError("Citation tags must be supplied through evidence_ids only")
    lines = [f"{incident['id']} / {incident['service']}",
             "Likely cause: " + redact(result["cause"]) + " " + " ".join("["+i+"]" for i in ids),
             "Explanation: " + redact(result["explanation"]),
             "Alternative considered: " + redact(result["alternative"]),
             "Recommendation (human approval required): " + redact(result["recommendation"]),
             "Read-only investigation; no changes executed."]
    lines += ["Evidence: " + available[i]["text"] + " [" + i + "]" for i in ids]
    return finish("ok", "\n".join(lines), evidence_ids=ids)
