"""Capture live A/A or gate evidence; never substitutes mock data."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("mode", choices=["aa", "gate"])
a = p.parse_args()
folder = ROOT / "evidence" / "live" / a.mode
folder.mkdir(parents=True, exist_ok=True)
# Fail rather than silently replace previously captured release evidence.
if (folder / "output.txt").exists():
    sys.exit(f"Evidence already exists in {folder}; archive that directory before rerunning.")
result = subprocess.run([sys.executable, "eval_gate.py", "--" + a.mode], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(folder / "output.txt").write_text(result.stdout)
(folder / "exit_code.txt").write_text(str(result.returncode) + "\n")
print(result.stdout)
for name in ["manifest.json", "eval_results.jsonl"] + (["baseline.json"] if a.mode == "aa" and result.returncode == 0 else ["gate_report.json"] if a.mode == "gate" else []):
    if (ROOT / name).exists():
        shutil.copy2(ROOT / name, folder / name)
sys.exit(result.returncode)
