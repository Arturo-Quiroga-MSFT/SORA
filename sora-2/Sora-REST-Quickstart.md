# Sora REST Quickstart: Text-to-Video and Image-to-Video

This quickstart shows how to generate videos with the Azure OpenAI Sora model using the REST API from simple Python CLIs. It covers both text-to-video and image-to-video, supports multiple variants, and works with API key, Bearer token, or Azure AD (AAD) authentication.

Links: Azure docs: https://learn.microsoft.com/azure/ai-services/openai/concepts/video-generation

## Prerequisites

- Python 3.9+
- An Azure OpenAI resource with Sora enabled
- Environment variables:
  - AZURE_OPENAI_ENDPOINT: https://<your-resource>.openai.azure.com
  - AZURE_OPENAI_API_KEY: your key (if using API key auth)
- Optional for AAD: `pip install azure-identity` and a signed-in developer session (VS Code Azure extension, Azure CLI az login, etc.)

Install packages used by the CLIs:

```bash
pip install requests python-dotenv azure-identity
```

Note: azure-identity is only required if you use --aad.

## Files

- sora-2/video_rest_cli.py: Text-to-Video via REST
- sora-2/image_to_video_rest.py: Image-to-Video via REST (multipart)

Both CLIs default to api-version=2025-04-01-preview and model=sora.

## Authentication options

Choose one of:

- API key header: set env AZURE_OPENAI_API_KEY; the CLI sends header `api-key: <key>`
- AAD: pass --aad; the CLI uses DefaultAzureCredential with scope https://cognitiveservices.azure.com/.default
- Bearer: pass --bearer <token>

## Text-to-Video

Example with API key:

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
export AZURE_OPENAI_API_KEY="<your-key>"

python sora-2/video_rest_cli.py \
  --prompt "A small dog playing in a creek in the forest during a summer day" \
  --width 1280 --height 720 --seconds 7 --variants 2
```

Example with AAD:

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"

python sora-2/video_rest_cli.py \
  --prompt "Sunset over dramatic mountains, cinematic" \
  --width 1280 --height 720 --seconds 7 --variants 3 \
  --aad
```

Outputs are saved under `videos/` by default. Use `--outdir` to change.

## Image-to-Video (multipart)

The request uploads an image and references it via `inpaint_items` in the JSON part. The CLI builds a multipart request with parts named `json` and `files`.

Example with API key:

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
export AZURE_OPENAI_API_KEY="<your-key>"

python sora-2/image_to_video_rest.py \
  --image sora-2/images/car.jpg \
  --prompt "Turn this into a neon-lit street drifting scene at night" \
  --width 1280 --height 720 --seconds 7 --variants 2
```

Example with AAD:

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"

python sora-2/image_to_video_rest.py \
  --image sora-2/images/face.jpg \
  --prompt "Slow, subtle camera push-in with soft studio lighting" \
  --width 1080 --height 1080 --seconds 6 --variants 2 \
  --aad
```

## Notes and tips

- Supported durations: generally 1–20 seconds.
- Use standard resolution pairs: 480x480, 720x1280, 1280x720, 1080x1920, 1920x1080, etc.
- Variants: `--variants N` sets `n_variants` to request multiple outputs. The CLI will download all of them.
- Do not manually set Content-Type for multipart; the HTTP client sets the boundary. For JSON requests, Content-Type: application/json is used.
- Statuses include queued, preprocessing, running, processing, succeeded, failed, cancelled. The CLI polls until a terminal state.

## Troubleshooting

- 401 Unauthorized: Check API key or AAD login; verify endpoint host and resource permissions.
- 404/400: Confirm api-version and endpoint; ensure your resource has Sora enabled.
- Missing azure-identity: Install it if using --aad: `pip install azure-identity`.
- No videos saved: If job succeeded but no files saved, there may be an API change or transient error; rerun and check stdout for details.
# Sora REST Quickstart (preview)

This guide shows how to use Azure OpenAI Sora via REST from the `sora-2` folder for:
- Text → Video using `video_rest_cli.py`
- Image → Video (seeded) using `image_to_video_rest.py` with multipart `inpaint_items`

It follows the async pattern: create job → poll status → download MP4.

## Prerequisites

- Python 3.10+
- Azure OpenAI resource with a deployed `sora` model in a supported region (for example, East US 2)
- Auth via either:
  - API key in `AZURE_OPENAI_API_KEY`, or
  - Microsoft Entra ID token in `AZURE_OPENAI_AUTH_TOKEN` (scope: https://cognitiveservices.azure.com/.default)

Install the only required package:

```bash
python -m pip install requests
```

Export your endpoint and key/token (macOS zsh):

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
# either
export AZURE_OPENAI_API_KEY="<key>"
# or
export AZURE_OPENAI_AUTH_TOKEN="$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)"
```

## Scripts included

- `video_rest_cli.py` — Text-to-video via REST (JSON body). Creates a job, polls until terminal state, then downloads the generated MP4 to `videos/`.
- `image_to_video_rest.py` — Image-seeded video generation via REST (multipart/form-data). Uploads an image as `files`, references it with `inpaint_items` in the `json` form part, polls, and downloads MP4 to `videos/`.

Both use API version `2025-04-01-preview` and expect either an `api-key` header or `Authorization: Bearer` header.

## Run: Text → Video (CLI)

```bash
python video_rest_cli.py \
  --prompt "Drone view of waves crashing against rugged cliffs at sunset" \
  --width 1280 --height 720 --n-seconds 7 \
  --endpoint "$AZURE_OPENAI_ENDPOINT" \
  --api-key "$AZURE_OPENAI_API_KEY"
```

Swap `--api-key` for `--bearer-token "$AZURE_OPENAI_AUTH_TOKEN"` if you prefer Entra ID. Output is saved under `videos/` with a timestamped filename.

## Run: Image → Video (CLI, multipart)

```bash
python image_to_video_rest.py \
  --image ./images/car.png \
  --prompt "A cinematic shot of a sports car driving through neon-lit streets at night" \
  --width 1280 --height 720 --n-seconds 5 \
  --endpoint "$AZURE_OPENAI_ENDPOINT" \
  --api-key "$AZURE_OPENAI_API_KEY"
```

Optional crop and frame index (0 is typical):

```bash
python image_to_video_rest.py \
  --image ./images/face.jpg \
  --prompt "Ultra close-up portrait moving subtly" \
  --width 720 --height 1280 --n-seconds 5 \
  --frame-index 0 \
  --crop '{"top_fraction":0.1,"left_fraction":0.1,"right_fraction":0.9,"bottom_fraction":0.9}' \
  --endpoint "$AZURE_OPENAI_ENDPOINT" \
  --api-key "$AZURE_OPENAI_API_KEY"
```

## cURL examples

Set variables first:

```bash
ENDPOINT="https://<your-resource>.openai.azure.com"
API_KEY="<your-api-key>"
API_VERSION="2025-04-01-preview"
```

Create a text→video job:

```bash
curl -sS -X POST "$ENDPOINT/openai/v1/video/generations/jobs?api-version=$API_VERSION" \
  -H "Content-Type: application/json" \
  -H "api-key: $API_KEY" \
  -d '{
    "prompt": "A small dog playing in a creek in the forest, during a summer day",
    "width": 480,
    "height": 480,
    "n_seconds": 5,
    "model": "sora"
  }'
```

Poll job status:

```bash
JOB_ID="task_..."
curl -sS "$ENDPOINT/openai/v1/video/generations/jobs/$JOB_ID?api-version=$API_VERSION" \
  -H "api-key: $API_KEY"
```

Download the video when `status` is `succeeded`:

```bash
GENERATION_ID="gen_..."
curl -sS "$ENDPOINT/openai/v1/video/generations/$GENERATION_ID/content/video?api-version=$API_VERSION" \
  -H "api-key: $API_KEY" \
  -o output.mp4
```

Create an image→video job (multipart) with `inpaint_items`:

```bash
curl -sS -X POST "$ENDPOINT/openai/v1/video/generations/jobs?api-version=$API_VERSION" \
  -H "api-key: $API_KEY" \
  -F "json={\"prompt\":\"Cinematic portrait with subtle motion\",\"width\":720,\"height\":1280,\"n_seconds\":5,\"model\":\"sora\",\"inpaint_items\":[{\"type\":\"image\",\"file_name\":\"face.jpg\",\"frame_index\":0}]}";type=application/json \
  -F "files=@./images/face.jpg;type=image/jpeg"
```

Then poll and download as shown above.

## Endpoints and API version

- Create job: `{endpoint}/openai/v1/video/generations/jobs?api-version=2025-04-01-preview`
- Poll status: `{endpoint}/openai/v1/video/generations/jobs/{job_id}?api-version=2025-04-01-preview`
- Download video: `{endpoint}/openai/v1/video/generations/{generation_id}/content/video?api-version=2025-04-01-preview`

Authentication headers:
- API key: `api-key: <key>`
- Entra ID (recommended): `Authorization: Bearer <token>` (scope: https://cognitiveservices.azure.com/.default)

For the multipart schema, `inpaint_items` should reference the uploaded file by `file_name` and specify `frame_index`. Optional `crop_bounds` uses fractional bounds (0.0–1.0) for `top_fraction`, `left_fraction`, `right_fraction`, `bottom_fraction`.

## Notes and limits (preview)

- Duration: 1–20 seconds
- Resolutions: 480×480, 854×480, 720×720, 1280×720, 1080×1080, 1920×1080 (portrait/landscape variants supported)
- Higher resolutions reduce allowed variants; concurrency is limited
- Outputs are retained for a limited time (~24h). Save promptly
- Ensure your resource region supports Sora; use API version `2025-04-01-preview`

## Troubleshooting

- ImportError: `requests` → install with:
  ```bash
  python -m pip install requests
  ```
- 401/403 → verify endpoint URL, auth header (either `api-key` or `Authorization`), and that your `sora` deployment exists.
- 400 → check `width`/`height` and `n_seconds` are allowed, and that JSON/multipart fields match the API.

## Appendix

- Quality gates (local):
  - Lint/type: PASS (no unresolved imports in the two new scripts)
  - Build: N/A (scripts)
  - Tests: N/A
  - Smoke: Scripts mirror the notebooks’ working pattern (create → poll → download)

- Requirements coverage:
  - Image→video via REST documented: DONE
  - Runnable tooling for REST usage: DONE (`video_rest_cli.py`, `image_to_video_rest.py`)
  - Install steps and cURL examples: DONE
  - Endpoints/auth/version aligned to official docs: DONE

- Next steps (optional):
  - Add a `--variants` flag to request multiple variants when allowed and auto-download each
  - Add an `--aad` flag to fetch a bearer token via `az` automatically
  - Centralize output dir via `--output-dir` (default already `videos/`)
