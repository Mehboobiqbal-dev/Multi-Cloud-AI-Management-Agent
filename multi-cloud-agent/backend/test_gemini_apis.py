import os
import sys
import time
import json
import argparse
from typing import List, Tuple, Dict

import requests

# Optional dotenv load if .env present
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Try to import google-generativeai SDK
try:
    import google.generativeai as genai  # type: ignore
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False

GEN_REST_URL_TMPL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")


def parse_keys(keys_arg: str | None) -> List[str]:
    if keys_arg:
        return [k.strip() for k in keys_arg.split(",") if k.strip()]
    env_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEYS_LIST")
    if env_keys:
        return [k.strip() for k in env_keys.split(",") if k.strip()]
    return []


def rest_generate(api_key: str, prompt: str, model: str, timeout: int = 30) -> Tuple[bool, Dict]:
    url = f"{GEN_REST_URL_TMPL.format(model=model)}?key={api_key}"
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    headers = {"Content-Type": "application/json"}
    start = time.time()
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
    elapsed = time.time() - start
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    ok = r.status_code == 200 and "candidates" in data
    return ok, {"status": r.status_code, "elapsed": elapsed, "data": data}


def sdk_generate(api_key: str, prompt: str, model: str, timeout: int = 30) -> Tuple[bool, Dict]:
    if not HAS_GENAI:
        return False, {"error": "google-generativeai not installed"}
    genai.configure(api_key=api_key)
    start = time.time()
    model_obj = genai.GenerativeModel(model_name=model)
    try:
        resp = model_obj.generate_content(prompt, timeout=timeout)
    except TypeError:
        # Fallback for SDKs that don't support timeout kwarg
        resp = model_obj.generate_content(prompt)
    elapsed = time.time() - start
    ok = hasattr(resp, "text") and bool(resp.text)
    return ok, {"elapsed": elapsed, "text": getattr(resp, "text", ""), "raw": getattr(resp, "candidates", None)}


def obfuscate(key: str) -> str:
    if len(key) <= 6:
        return key[:3] + "***"
    return key[:6] + "..."


def main():
    parser = argparse.ArgumentParser(description="Test Gemini API keys via REST and SDK")
    parser.add_argument("--keys", help="Comma-separated API keys (overrides env GEMINI_API_KEYS)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model to test (default: {DEFAULT_MODEL})")
    parser.add_argument("--mode", choices=["rest", "sdk", "both"], default="both", help="Which API surface to test")
    parser.add_argument("--prompt", default="Write a short poem about the moon.", help="Prompt to send")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    keys = parse_keys(args.keys)
    if not keys:
        print("ERROR: No API keys provided. Set GEMINI_API_KEYS in .env or use --keys.", file=sys.stderr)
        sys.exit(2)

    print(f"Testing {len(keys)} key(s) against model {args.model} (mode={args.mode})\n")

    any_success = False
    results = []

    for key in keys:
        label = obfuscate(key)
        entry = {"key": label, "rest": None, "sdk": None}
        try:
            if args.mode in ("rest", "both"):
                ok, info = rest_generate(key, args.prompt, args.model, args.timeout)
                entry["rest"] = {"ok": ok, **info}
                any_success = any_success or ok
        except Exception as e:
            entry["rest"] = {"ok": False, "error": str(e)}
        try:
            if args.mode in ("sdk", "both"):
                ok, info = sdk_generate(key, args.prompt, args.model, args.timeout)
                entry["sdk"] = {"ok": ok, **info}
                any_success = any_success or ok
        except Exception as e:
            entry["sdk"] = {"ok": False, "error": str(e)}
        results.append(entry)

    # Pretty print summary
    for r in results:
        print(f"Key {r['key']}:")
        if r["rest"] is not None:
            rest = r["rest"]
            if rest.get("ok"):
                text = rest.get("data", {}).get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                print(f"  REST: OK {rest.get('status')} in {rest.get('elapsed'):.2f}s\n    Text: {text[:120].strip()}...")
            else:
                print(f"  REST: FAIL status={rest.get('status')} err={rest.get('error')}\n    data={str(rest.get('data'))[:200]}")
        if r["sdk"] is not None:
            sdk = r["sdk"]
            if sdk.get("ok"):
                text = sdk.get("text", "")
                print(f"  SDK:  OK in {sdk.get('elapsed'):.2f}s\n    Text: {text[:120].strip()}...")
            else:
                print(f"  SDK:  FAIL err={sdk.get('error')} raw={(str(sdk.get('raw'))[:120])}")
        print()

    if not any_success:
        print("No successful responses. Check that the Generative Language API is enabled, the keys are valid, and quotas allow requests.")
        sys.exit(1)


if __name__ == "__main__":
    main()
