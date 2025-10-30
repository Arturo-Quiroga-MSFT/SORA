#!/usr/bin/env python3
"""
Text-to-Video generation with Azure OpenAI Sora via REST API.

Features:
- Auth: API key (api-key), Bearer token, or AAD via DefaultAzureCredential (--aad)
- Variants: request multiple video variants with --variants
- Polling until completion and downloading all generated videos

Usage examples:
  # API key from env
  AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com" \
  AZURE_OPENAI_API_KEY="<key>" \
  python sora-2/video_rest_cli.py --prompt "A dog playing in a creek" --width 1280 --height 720 --seconds 7 --variants 2

  # AAD auth (requires `azure-identity` and an authenticated dev session)
  AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com" \
  python sora-2/video_rest_cli.py --prompt "Sunset over mountains" --aad
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests


API_VERSION_DEFAULT = "2025-04-01-preview"


def _aad_token() -> str:
    try:
        from azure.identity import DefaultAzureCredential
    except ImportError:
        print("ERROR: azure-identity is required for --aad. Install with: pip install azure-identity", file=sys.stderr)
        sys.exit(2)
    cred = DefaultAzureCredential()
    token = cred.get_token("https://cognitiveservices.azure.com/.default")
    return token.token


def build_headers(
    api_key: Optional[str],
    bearer: Optional[str],
    use_aad: bool,
    is_multipart: bool = False,
) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if use_aad:
        headers["Authorization"] = f"Bearer {_aad_token()}"
    elif bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    else:
        # API key mode
        if not api_key:
            print("ERROR: Provide AZURE_OPENAI_API_KEY env var or use --aad/--bearer.", file=sys.stderr)
            sys.exit(2)
        headers["api-key"] = api_key

    if not is_multipart:
        headers["Content-Type"] = "application/json"
    return headers


def _slug(text: str, max_len: int = 40) -> str:
    s = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in text)
    s = "_".join(s.split())
    return s[:max_len].strip("_") or "video"


def create_job(
    endpoint: str,
    headers: Dict[str, str],
    prompt: str,
    width: int,
    height: int,
    n_seconds: int,
    model: str,
    api_version: str,
    variants: int = 1,
) -> Dict:
    url = f"{endpoint}/openai/v1/video/generations/jobs?api-version={api_version}"
    body: Dict = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "n_seconds": n_seconds,
        "model": model,
    }
    if variants and variants > 1:
        body["n_variants"] = variants

    resp = requests.post(url, headers=headers, json=body)
    if not resp.ok:
        print("Create job failed:", resp.status_code, resp.text, file=sys.stderr)
        resp.raise_for_status()
    return resp.json()


def poll_job(endpoint: str, headers: Dict[str, str], job_id: str, api_version: str) -> Dict:
    status_url = f"{endpoint}/openai/v1/video/generations/jobs/{job_id}?api-version={api_version}"
    status = None
    last = None
    start = time.time()
    while status not in ("succeeded", "failed", "cancelled"):
        time.sleep(5)
        resp = requests.get(status_url, headers=headers)
        if not resp.ok:
            print("Polling failed:", resp.status_code, resp.text, file=sys.stderr)
            resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        if status != last:
            now = dt.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
            print(f"{now} Job status: {status}")
            last = status
        if status == "succeeded":
            total = int(time.time() - start)
            print(f"\n✅ Done. Video generation succeeded in {total}s.")
            return data
        if status in ("failed", "cancelled"):
            print("Job did not complete successfully.")
            return data
    return data  # type: ignore[name-defined]


def download_all(
    endpoint: str,
    headers: Dict[str, str],
    job_data: Dict,
    api_version: str,
    outdir: str,
    filename_prefix: str,
) -> List[str]:
    os.makedirs(outdir, exist_ok=True)
    generations = job_data.get("generations", []) or []
    saved: List[str] = []
    for i, gen in enumerate(generations, start=1):
        gen_id = gen.get("id")
        if not gen_id:
            continue
        url = f"{endpoint}/openai/v1/video/generations/{gen_id}/content/video?api-version={api_version}"
        r = requests.get(url, headers=headers)
        if not r.ok:
            print(f"Download failed for generation {gen_id}:", r.status_code, r.text, file=sys.stderr)
            continue
        suffix = f"_v{i:02d}" if len(generations) > 1 else ""
        fname = os.path.join(outdir, f"{filename_prefix}{suffix}.mp4")
        with open(fname, "wb") as f:
            f.write(r.content)
        print(f"Saved: {fname}")
        saved.append(fname)
    return saved


def main():
    p = argparse.ArgumentParser(description="Azure OpenAI Sora Text-to-Video via REST")
    p.add_argument("--prompt", required=True, help="Text prompt")
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--seconds", type=int, default=5, help="Duration in seconds (1-20)")
    p.add_argument("--model", default="sora")
    p.add_argument("--variants", type=int, default=1, help="Number of variants to request")
    p.add_argument("--outdir", default="videos", help="Output directory")
    p.add_argument("--api-version", default=API_VERSION_DEFAULT)
    # Auth options
    p.add_argument("--aad", action="store_true", help="Use AAD (DefaultAzureCredential)")
    p.add_argument("--bearer", default=None, help="Explicit Bearer token to use")
    args = p.parse_args()

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        print("ERROR: AZURE_OPENAI_ENDPOINT env var is required.", file=sys.stderr)
        sys.exit(2)
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    headers = build_headers(api_key, args.bearer, args.aad, is_multipart=False)

    created = create_job(
        endpoint=endpoint,
        headers=headers,
        prompt=args.prompt,
        width=args.width,
        height=args.height,
        n_seconds=args.seconds,
        model=args.model,
        api_version=args.api_version,
        variants=args.variants,
    )
    job_id = created.get("id")
    now = dt.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
    print(f"{now} Job created: {job_id}")

    result = poll_job(endpoint, headers, job_id, args.api_version)

    if result.get("status") != "succeeded":
        print("Job status:", result.get("status"))
        if result.get("failure_reason"):
            print("Failure reason:", result.get("failure_reason"))
        sys.exit(1)

    ts = dt.datetime.now().strftime('%d%b%Y_%H%M%S')
    prefix = f"sora_{ts}_{_slug(args.prompt)}"
    saved = download_all(endpoint, headers, result, args.api_version, args.outdir, prefix)
    if not saved:
        print("No video files were saved.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Text-to-Video (Sora) REST CLI for Azure AI Foundry

Features
- Async job create → poll → download
- Multiple variants in a single run via --variants
- Auth: API key, raw Bearer, or AAD (DefaultAzureCredential) via --aad

Requirements
- requests
- python-dotenv (optional)
- azure-identity (only if using --aad)

Example
  python video_rest_cli.py \
    --endpoint "$AZURE_OPENAI_ENDPOINT" \
    --api-key "$AZURE_OPENAI_API_KEY" \
    --prompt "A small dog playing in a creek in the forest, during a summer day" \
    --width 1280 --height 720 --seconds 7 --variants 3

  # AAD auth (no api key required)
  python video_rest_cli.py \
    --endpoint "$AZURE_OPENAI_ENDPOINT" \
    --aad \
    --prompt "Reflections in the window of a train traveling through Mexico city suburbs." \
    --width 1280 --height 720 --seconds 10
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # optional

try:
    from azure.identity import DefaultAzureCredential  # type: ignore
except Exception:
    DefaultAzureCredential = None  # only needed if --aad is used


API_VERSION = os.getenv("SORA_API_VERSION", "2025-04-01-preview")
DEFAULT_MODEL = os.getenv("SORA_MODEL", "sora")


def _aad_token() -> Optional[str]:
    if DefaultAzureCredential is None:
        return None
    try:
        cred = DefaultAzureCredential()
        token = cred.get_token("https://cognitiveservices.azure.com/.default")
        return token.token
    except Exception:
        return None


def build_headers(api_key: Optional[str], bearer: Optional[str], use_aad: bool, is_multipart: bool) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if use_aad:
        token = _aad_token()
        if not token:
            raise RuntimeError("--aad requested but could not acquire AAD token. Ensure azure-identity is installed and you're signed in (az login).")
        headers["Authorization"] = f"Bearer {token}"
    elif bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    elif api_key:
        headers["api-key"] = api_key
    else:
        raise RuntimeError("No authentication provided. Use --api-key, --bearer, or --aad.")

    if not is_multipart:
        headers["Content-Type"] = "application/json"
    # For multipart, requests will set the correct boundary, so we omit Content-Type.
    return headers


def create_job(endpoint: str, headers: Dict[str, str], prompt: str, width: int, height: int, seconds: int, model: str, variants: int) -> str:
    url = f"{endpoint}/openai/v1/video/generations/jobs?api-version={API_VERSION}"
    body = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "n_seconds": seconds,
        "model": model,
    }
    if variants and variants > 1:
        body["n_variants"] = variants

    resp = requests.post(url, headers=headers, json=body)
    try:
        resp.raise_for_status()
    except Exception:
        print("Create job failed:", resp.text, file=sys.stderr)
        raise

    payload = resp.json()
    print(dt.datetime.now().strftime('%d-%b-%Y %H:%M:%S'), "Full response JSON:", payload)
    print()
    job_id = payload["id"]
    print(dt.datetime.now().strftime('%d-%b-%Y %H:%M:%S'), f"Job created: {job_id}")
    return job_id


def poll_job(endpoint: str, headers: Dict[str, str], job_id: str) -> Dict:
    url = f"{endpoint}/openai/v1/video/generations/jobs/{job_id}?api-version={API_VERSION}"
    status = None
    last = {}
    while status not in ("succeeded", "failed", "cancelled"):
        time.sleep(5)
        last = requests.get(url, headers=headers).json()
        status = last.get("status")
        print(dt.datetime.now().strftime('%d-%b-%Y %H:%M:%S'), f"Job status: {status}")
    return last


def _slug(text: str, max_len: int = 40) -> str:
    base = (text or "").strip().replace("\n", " ")
    base = base[:max_len]
    for ch in ",.:/\\'\"|?*<>":
        base = base.replace(ch, " ")
    base = "_".join([p for p in base.split() if p])
    return base


def download_all(endpoint: str, headers: Dict[str, str], generations: List[Dict], output_dir: str, prompt: str) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    saved: List[str] = []
    ts = dt.datetime.now().strftime('%d%b%Y_%H%M%S')
    prefix = f"sora_{ts}_{_slug(prompt)}"
    for idx, g in enumerate(generations, 1):
        gen_id = g.get("id")
        if not gen_id:
            continue
        url = f"{endpoint}/openai/v1/video/generations/{gen_id}/content/video?api-version={API_VERSION}"
        r = requests.get(url, headers=headers)
        if not r.ok:
            print(f"Failed to download generation {gen_id}: {r.status_code} {r.text}", file=sys.stderr)
            continue
        filename = os.path.join(output_dir, f"{prefix}_{idx}.mp4")
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"Saved: {filename}")
        saved.append(filename)
    return saved


def main(argv: Optional[List[str]] = None) -> int:
    if load_dotenv:
        load_dotenv()

    p = argparse.ArgumentParser(description="Sora Text-to-Video via REST")
    p.add_argument("--endpoint", required=False, default=os.getenv("AZURE_OPENAI_ENDPOINT"), help="Azure OpenAI endpoint (e.g. https://<resource>.openai.azure.com)")
    p.add_argument("--api-key", required=False, default=os.getenv("AZURE_OPENAI_API_KEY"), help="API key auth")
    p.add_argument("--bearer", required=False, help="Raw Bearer token for Authorization header")
    p.add_argument("--aad", action="store_true", help="Use AAD (DefaultAzureCredential) instead of api key")

    p.add_argument("--prompt", required=True, help="Text prompt for the video")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--seconds", type=int, default=7, help="Duration in seconds (1-20)")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--variants", type=int, default=1, help="Number of variants to generate in a single job")
    p.add_argument("--outdir", default="videos", help="Output directory")

    args = p.parse_args(argv)

    if not args.endpoint:
        print("--endpoint is required (or set AZURE_OPENAI_ENDPOINT)", file=sys.stderr)
        return 2

    headers = build_headers(api_key=args.api_key, bearer=args.bearer, use_aad=args.aad, is_multipart=False)

    start = time.time()
    job_id = create_job(
        endpoint=args.endpoint,
        headers=headers,
        prompt=args.prompt,
        width=args.width,
        height=args.height,
        seconds=args.seconds,
        model=args.model,
        variants=args.variants,
    )

    status_payload = poll_job(args.endpoint, headers, job_id)

    if status_payload.get("status") == "succeeded":
        print()
        print(dt.datetime.now().strftime('%d-%b-%Y %H:%M:%S'), "✅ Done. Video generation succeeded.")
        gens = status_payload.get("generations", [])
        if not gens:
            print("No generations in result.", file=sys.stderr)
            return 1
        saved = download_all(args.endpoint, headers, gens, args.outdir, status_payload.get("prompt") or args.prompt)
        elapsed = time.time() - start
        m, s = divmod(elapsed, 60)
        print(f"Done in {m:.0f} minutes and {s:.0f} seconds")
        return 0 if saved else 1
    else:
        print(f"Job did not succeed. Status: {status_payload.get('status')} Reason: {status_payload.get('failure_reason')}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Minimal CLI to generate a video with Azure OpenAI Sora via REST.

Flow: create job -> poll status -> download generated video to videos/.

Auth options:
- API key: pass --api-key or set AZURE_OPENAI_API_KEY
- Bearer token: pass --bearer-token or set AZURE_OPENAI_AUTH_TOKEN

Endpoint: pass --endpoint or set AZURE_OPENAI_ENDPOINT. Example:
  https://<resource>.openai.azure.com

Usage examples:
  python video_rest_cli.py \
    --prompt "A dog running on a beach at sunset, cinematic, shallow depth of field" \
    --width 1280 --height 720 --n-seconds 5 \
    --endpoint "$AZURE_OPENAI_ENDPOINT" \
    --api-key "$AZURE_OPENAI_API_KEY"

Note: Requires 'requests' package.
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
from typing import Dict, Optional

import requests


API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
DEFAULT_MODEL = os.environ.get("AZURE_OPENAI_SORA_MODEL", "sora")
DEFAULT_OUTPUT_DIR = os.environ.get("SORA_OUTPUT_DIR", "videos")


def _slug(text: str, max_len: int = 30) -> str:
    base = (text or "video").strip().replace("\n", " ")
    base = base[:max_len]
    for ch in [",", ".", ":", ";", "/", "\\", "|", "\"", "'", "?", "!", "(", ")", "[", "]", "{", "}"]:
        base = base.replace(ch, "_")
    base = "_".join(base.split())
    return base or "video"


def _get_aad_token() -> str:
    try:
        from azure.identity import DefaultAzureCredential
    except Exception as e:
        print("--aad requested but azure-identity is not installed. Install with: pip install azure-identity", file=sys.stderr)
        raise
    cred = DefaultAzureCredential()
    token = cred.get_token("https://cognitiveservices.azure.com/.default")
    return token.token


def build_headers(api_key: Optional[str], bearer_token: Optional[str], use_aad: bool) -> Dict[str, str]:
    if use_aad:
        token = _get_aad_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if bearer_token:
        return {"Authorization": f"Bearer {bearer_token}", "Content-Type": "application/json"}
    if api_key:
        return {"api-key": api_key, "Content-Type": "application/json"}
    # Env fallbacks
    env_bearer = os.environ.get("AZURE_OPENAI_AUTH_TOKEN")
    if env_bearer:
        return {"Authorization": f"Bearer {env_bearer}", "Content-Type": "application/json"}
    env_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if env_key:
        return {"api-key": env_key, "Content-Type": "application/json"}
    raise ValueError("No auth provided. Use --api-key, --bearer-token, or --aad, or set AZURE_OPENAI_API_KEY/AZURE_OPENAI_AUTH_TOKEN.")


def create_job(endpoint: str, headers: Dict[str, str], prompt: str, width: int, height: int, n_seconds: int, model: str, n_variants: int) -> str:
    url = f"{endpoint}/openai/v1/video/generations/jobs?api-version={API_VERSION}"
    body = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "n_seconds": n_seconds,
        "model": model,
    }
    if n_variants and int(n_variants) > 1:
        body["n_variants"] = int(n_variants)

    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()

    now = datetime.datetime.today().strftime('%d-%b-%Y %H:%M:%S')
    print(f"{now} Full response JSON:", resp.json())
    print()

    job_id = resp.json()["id"]
    print(f"{now} Job created: {job_id}")
    return job_id


def poll_job(endpoint: str, headers: Dict[str, str], job_id: str, poll_seconds: int = 5) -> Dict:
    url = f"{endpoint}/openai/v1/video/generations/jobs/{job_id}?api-version={API_VERSION}"
    status = None
    while status not in ("succeeded", "failed", "cancelled"):
        time.sleep(poll_seconds)
        status_resp = requests.get(url, headers=headers)
        status_resp.raise_for_status()
        data = status_resp.json()
        status = data.get("status")
        now = datetime.datetime.today().strftime('%d-%b-%Y %H:%M:%S')
        print(f"{now} Job status: {status}")
    return data


def download_all_generations(endpoint: str, headers: Dict[str, str], generations: list, output_dir: str, prompt: str) -> list:
    os.makedirs(output_dir, exist_ok=True)
    idx = datetime.datetime.today().strftime('%d%b%Y_%H%M%S')
    prefix = _slug(prompt)
    saved = []

    for i, gen in enumerate(generations, start=1):
        gen_id = gen.get("id")
        if not gen_id:
            continue
        url = f"{endpoint}/openai/v1/video/generations/{gen_id}/content/video?api-version={API_VERSION}"
        video_resp = requests.get(url, headers=headers)
        video_resp.raise_for_status()
        variant_suffix = f"_{i:02d}" if len(generations) > 1 else ""
        filename = os.path.join(output_dir, f"sora_{idx}_{prefix}{variant_suffix}.mp4")
        with open(filename, "wb") as f:
            f.write(video_resp.content)
        print(f"SORA Generated video saved: '{filename}'")
        saved.append(filename)
    return saved


def main():
    parser = argparse.ArgumentParser(description="Sora Text-to-Video via REST")
    parser.add_argument("--prompt", required=True, help="Text prompt")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--n-seconds", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--variants", type=int, default=1, help="Number of video variants to request")

    parser.add_argument("--endpoint", default=os.environ.get("AZURE_OPENAI_ENDPOINT"), help="Azure OpenAI endpoint")

    # Auth options
    parser.add_argument("--api-key", default=os.environ.get("AZURE_OPENAI_API_KEY"))
    parser.add_argument("--bearer-token", default=os.environ.get("AZURE_OPENAI_AUTH_TOKEN"))
    parser.add_argument("--aad", action="store_true", help="Acquire bearer token via DefaultAzureCredential")

    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)

    args = parser.parse_args()

    if not args.endpoint:
        print("--endpoint or AZURE_OPENAI_ENDPOINT is required", file=sys.stderr)
        sys.exit(2)

    headers = build_headers(args.api_key, args.bearer_token, args.aad)

    start = time.time()
    job_id = create_job(
        args.endpoint,
        headers,
        args.prompt,
        args.width,
        args.height,
        args.n_seconds,
        args.model,
        args.variants,
    )

    status_data = poll_job(args.endpoint, headers, job_id, args.poll_seconds)
    status = status_data.get("status")
    if status == "succeeded":
        gens = status_data.get("generations", [])
        if not gens:
            raise RuntimeError("Error. No generations found in job result.")
        print(f"\n✅ Done. Video generation succeeded.")
        saved = download_all_generations(args.endpoint, headers, gens, args.output_dir, args.prompt)
        elapsed = time.time() - start
        m, s = divmod(elapsed, 60)
        print(f"Done in {m:.0f} minutes and {s:.0f} seconds")
        # Print final list for convenience
        for f in saved:
            print(f)
    else:
        raise RuntimeError(f"Error. Job did not succeed. Status: {status}")


if __name__ == "__main__":
    main()
