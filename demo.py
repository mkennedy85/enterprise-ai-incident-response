import argparse
import json
import sys
from incident_agent.engine import investigate
from incident_agent.client import ModelError
p = argparse.ArgumentParser()
p.add_argument("question", nargs="?", default="Investigate INC-001")
p.add_argument("--json", action="store_true")
a = p.parse_args()
try:
    result = investigate(a.question)
except ModelError as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    sys.exit(2)
print(json.dumps(result, indent=2) if a.json else result["text"])
