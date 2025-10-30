#!/usr/bin/env python3
"""
Azure OpenAI Sora image-to-video via REST (multipart).

Single, clean CLI: upload image + JSON (inpaint_items), poll, download variants.
Auth: API key (api-key header), Bearer token, or AAD (--aad).
"""

import argparse
import datetime as dt
import json
import mimetypes
import os
import sys
import time
from typing import Dict, List, Optional

import requests

from dotenv import load_dotenv
load_dotenv()


API_VERSION = os.getenv("SORA_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION") or "2025-04-01-preview"


def _aad_token() -> str:
    try:
        from azure.identity import DefaultAzureCredential
    except ImportError:
        print("ERROR: --aad requires azure-identity. Install with: pip install azure-identity", file=sys.stderr)
        sys.exit(2)
    cred = DefaultAzureCredential()
    token = cred.get_token("https://cognitiveservices.azure.com/.default")
    return token.token


def _guess_mime(path: str) -> str:
    t, _ = mimetypes.guess_type(path)
    return t or "application/octet-stream"


def _slug(text: str, max_len: int = 40) -> str:
    s = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in text)
    s = "_".join(s.split())
    return s[:max_len].strip("_") or "video"


def build_headers(api_key: Optional[str], bearer: Optional[str], use_aad: bool) -> Dict[str, str]:
    h: Dict[str, str] = {}
    if use_aad:
        h["Authorization"] = f"Bearer {_aad_token()}"
    elif bearer:
        h["Authorization"] = f"Bearer {bearer}"
    else:
        if not api_key:
            print("ERROR: Provide AZURE_OPENAI_API_KEY or use --bearer/--aad.", file=sys.stderr)
            sys.exit(2)
        h["api-key"] = api_key
    return h


def create_job(
    endpoint: str,
    headers: Dict[str, str],
    image_path: str,
    prompt: str,
    width: int,
    height: int,
    n_seconds: int,
    model: str,
    api_version: str,
    variants: int,
) -> Dict:
    url = f"{endpoint}/openai/v1/video/generations/jobs?api-version={api_version}"
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "n_seconds": n_seconds,
        "model": model,
        "inpaint_items": [
            {
                "asset_index": 0,
                "transform": "image_to_video",
            }
        ],
    }
    if variants and variants > 1:
        payload["n_variants"] = variants

    files = [
        ("json", (None, json.dumps(payload), "application/json")),
        ("files", (os.path.basename(image_path), open(image_path, "rb"), _guess_mime(image_path))),
    ]

    r = requests.post(url, headers=headers, files=files)
    if not r.ok:
        print("Create job failed:", r.status_code, r.text, file=sys.stderr)
        # Helpful hint for common API-version mismatches
        if r.status_code in (400, 404, 415, 422):
            print(
                f"Hint: The api-version '{api_version}' may not be supported on this resource/region. "
                "Try --api-version preview or --api-version 2025-04-01-preview, or set AZURE_OPENAI_API_VERSION.",
                file=sys.stderr,
            )
        r.raise_for_status()
    return r.json()


def poll_job(endpoint: str, headers: Dict[str, str], job_id: str, api_version: str) -> Dict:
    url = f"{endpoint}/openai/v1/video/generations/jobs/{job_id}?api-version={api_version}"
    status = None
    last = None
    start = time.time()
    while status not in ("succeeded", "failed", "cancelled"):
        time.sleep(5)
        r = requests.get(url, headers=headers)
        if not r.ok:
            print("Polling failed:", r.status_code, r.text, file=sys.stderr)
            r.raise_for_status()
        data = r.json()
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


def download_all(endpoint: str, headers: Dict[str, str], job_data: Dict, api_version: str, outdir: str, prefix: str) -> List[str]:
    os.makedirs(outdir, exist_ok=True)
    gens = job_data.get("generations", []) or []
    saved: List[str] = []
    for i, g in enumerate(gens, start=1):
        gen_id = g.get("id")
        if not gen_id:
            continue
        url = f"{endpoint}/openai/v1/video/generations/{gen_id}/content/video?api-version={api_version}"
        r = requests.get(url, headers=headers)
        if not r.ok:
            print(f"Download failed for generation {gen_id}:", r.status_code, r.text, file=sys.stderr)
            continue
        suffix = f"_v{i:02d}" if len(gens) > 1 else ""
        fname = os.path.join(outdir, f"{prefix}{suffix}.mp4")
        with open(fname, "wb") as f:
            f.write(r.content)
        print(f"Saved: {fname}")
        saved.append(fname)
    return saved


def main() -> int:
    p = argparse.ArgumentParser(description="Azure OpenAI Sora Image-to-Video via REST (multipart)")
    p.add_argument("--image", required=True, help="Path to input image file")
    p.add_argument("--prompt", required=True, help="Guidance prompt")
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--seconds", type=int, default=5, help="Duration in seconds (1-20)")
    p.add_argument("--model", default="sora")
    p.add_argument("--variants", type=int, default=1, help="Number of variants to request")
    p.add_argument("--outdir", default="videos", help="Output directory")
    p.add_argument("--api-version", default=API_VERSION)
    # Auth options
    p.add_argument("--aad", action="store_true", help="Use AAD (DefaultAzureCredential)")
    p.add_argument("--bearer", default=None, help="Explicit Bearer token to use")
    args = p.parse_args()

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        print("ERROR: AZURE_OPENAI_ENDPOINT env var is required.", file=sys.stderr)
        return 2
    # Normalize endpoint to avoid double slashes when constructing URLs
    endpoint = endpoint.rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not os.path.isfile(args.image):
        print(f"ERROR: Image file not found: {args.image}", file=sys.stderr)
        return 2

    headers = build_headers(api_key, args.bearer, args.aad)

    print(f"Using API version: {args.api_version}")

    created = create_job(
        endpoint=endpoint,
        headers=headers,
        image_path=args.image,
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
        return 1

    ts = dt.datetime.now().strftime('%d%b%Y_%H%M%S')
    prefix = f"image_to_video_{ts}_{_slug(os.path.basename(args.image))}_{_slug(args.prompt)}"
    saved = download_all(endpoint, headers, result, args.api_version, args.outdir, prefix)
    if not saved:
        print("No video files were saved.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
