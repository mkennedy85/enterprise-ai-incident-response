"""Refresh or verify content hashes; run from repository root."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ["system.py", "incident_agent/__init__.py", "incident_agent/engine.py", "incident_agent/client.py",
             "data/incidents.json", "prompts/investigator-v1.txt", "config/settings.json",
             "config/tools.json", "config/response_schema.json", "eval_gate.py", "scripts/release.py"]

def refresh(check=False):
    manifest = json.loads((ROOT / "manifest.json").read_text())
    hashes = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in ARTIFACTS}
    cases = [json.loads(line) for line in (ROOT / "eval_set.jsonl").read_text().splitlines() if line.strip()]
    canonical = json.dumps(sorted(cases, key=lambda c: c["id"]), sort_keys=True, ensure_ascii=True)
    evaluation_hash = hashlib.sha256(canonical.encode()).hexdigest()[:12]
    if check:
        if manifest["artifacts"] != hashes or manifest["eval_set_hash"] != evaluation_hash:
            raise RuntimeError("Manifest artifacts or evaluation hash are stale; run python3 scripts/release.py and review the diff.")
    else:
        manifest["artifacts"] = hashes
        manifest["eval_set_hash"] = evaluation_hash
        (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return evaluation_hash

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    print(refresh(args.check))
