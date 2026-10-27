"""Prompt without echo and run a Python script with the key only in its environment."""
import getpass
import os
import subprocess
import sys
if len(sys.argv) < 2:
    sys.exit("Usage: python3 scripts/with_api_key.py demo.py 'Investigate INC-001' OR scripts/live_measure.py aa")
key = getpass.getpass("OpenAI API key (hidden, not saved): ").strip()
if not key:
    sys.exit("No key entered")
env = dict(os.environ, OPENAI_API_KEY=key)
sys.exit(subprocess.call([sys.executable, *sys.argv[1:]], env=env))
