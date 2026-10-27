"""Offline investigation prototype. Fixtures and hypotheses are synthetic and curated.
No model, network access, shell execution, or remediation tools are used.
"""
import json
import re
from pathlib import Path
DATA = Path(__file__).resolve().parents[1] / "data" / "incidents.json"

def investigate(question):
    # Conservative input policy for this prototype, not a production security boundary.
    if re.search(r"secret|password|api.?key|credential|ignore.*(?:rule|instruction)|restart|roll.?back|execute|reconfigure|delete", question, re.I):
        return {"status": "refused", "text": "I cannot answer requests to expose secrets, override instructions, or execute changes. Investigation is read-only; human approval is required for remediation. [POLICY]"}
    incidents = json.loads(DATA.read_text())
    ids = set(re.findall(r"INC-\d+", question.upper()))
    if ids:
        matches = [i for i in incidents if i["id"] in ids]
        if ids - {i["id"] for i in matches}:
            matches = []
    else:
        matches = [i for i in incidents if i["service"].lower() in question.lower()]
    if len(matches) != 1:
        return {"status": "unknown", "text": "I do not have that information for one unambiguous incident. Specify a known incident ID or service. [none]"}
    incident = matches[0]
    # Distinct read-only evidence collection stages; no claim of LLM agents yet.
    telemetry = [e for e in incident["evidence"] if e["kind"] in ("metric", "trace")]
    changes = [e for e in incident["evidence"] if e["kind"] == "change"]
    runbooks = [e for e in incident["evidence"] if e["kind"] == "runbook"]
    evidence = telemetry + changes + runbooks
    available = {e["id"] for e in evidence}
    ranked = sorted(incident["hypotheses"], key=lambda h: len(set(h["supports"]) & available), reverse=True)
    top = ranked[0]
    if len(set(top["supports"]) & available) < 2:
        return {"status": "unknown", "text": "I cannot answer with sufficient supporting evidence. [none]"}
    cited = [e for e in evidence if e["id"] in top["supports"]]
    lines = [f"{incident['id']} / {incident['service']}",
             "Likely cause (curated synthetic hypothesis): " + top["cause"] + " " + " ".join("[" + e["id"] + "]" for e in cited)]
    lines += [e["text"] + " [" + e["id"] + "]" for e in cited]
    lines += ["Alternative considered: " + h["cause"] + "; insufficient supporting evidence." for h in ranked[1:]]
    lines += ["Read-only investigation; no changes executed."]
    lines += [e["text"] + " [" + e["id"] + "]" for e in runbooks]
    return {"status": "ok", "incident_id": incident["id"], "hypotheses": ranked,
            "evidence_ids": [e["id"] for e in evidence], "text": "\n".join(lines)}
