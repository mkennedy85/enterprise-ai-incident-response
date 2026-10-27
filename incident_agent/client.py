"""Small Responses API client; standard library only, no retries or hidden fallbacks."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

class ModelError(RuntimeError):
    pass

def require_key():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ModelError("OPENAI_API_KEY is not set. Configure it locally or as a GitHub Actions secret; no model call was made.")
    return key

def complete(payload, timeout):
    key = require_key()
    request = Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode(),
                      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.load(response)
    except HTTPError as exc:
        # Do not print response bodies or headers; they can contain submitted data.
        raise ModelError(f"OpenAI HTTP {exc.code}; check model access, billing, quota, and credentials.") from None
    except (URLError, TimeoutError, OSError):
        raise ModelError("OpenAI connection failed or timed out; no fallback answer was substituted.") from None
    if body.get("status") != "completed":
        raise ModelError("OpenAI response was not completed (possibly output token limit).")
    parts = [p for item in body.get("output", []) if item.get("type") == "message" for p in item.get("content", [])]
    if any(p.get("type") == "refusal" for p in parts):
        raise ModelError("The model refused this request.")
    try:
        result = json.loads("".join(p["text"] for p in parts if p.get("type") == "output_text"))
    except (ValueError, KeyError):
        raise ModelError("OpenAI returned no valid structured report.") from None
    return result, body.get("usage", {})
