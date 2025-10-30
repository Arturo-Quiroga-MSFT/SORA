# Sora via REST (preview) in `sora-2`

This folder contains minimal, runnable scripts to use Azure OpenAI Sora over REST for:
- Text to video: `video_rest_cli.py`
- Image to video (multipart seeding): `image_to_video_rest.py`

Both follow the async pattern: create job → poll status → download MP4.

## Prereqs
- Python 3.10+
- Azure OpenAI resource with a deployed `sora` model in a supported region (for example, East US 2)
- One of the following auth methods:
  - API key in `AZURE_OPENAI_API_KEY`
  - Microsoft Entra ID token in `AZURE_OPENAI_AUTH_TOKEN` (scope: https://cognitiveservices.azure.com/.default)

Install the only required package:

```bash
python -m pip install requests
```

Export your endpoint and key/token. On macOS/zsh:

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
# either
export AZURE_OPENAI_API_KEY="<key>"
# or
export AZURE_OPENAI_AUTH_TOKEN="$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)"
```

## Text → Video (CLI)

```bash
python video_rest_cli.py \
  --prompt "Drone view of waves crashing against rugged cliffs at sunset" \
  --width 1280 --height 720 --n-seconds 7 \
  --endpoint "$AZURE_OPENAI_ENDPOINT" \
  --api-key "$AZURE_OPENAI_API_KEY"
```

Output is saved under `videos/` with a timestamped filename.

## Image → Video (CLI, multipart)

```bash
python image_to_video_rest.py \
  --image ./images/car.png \
  --prompt "A cinematic shot of a sports car driving through neon-lit streets at night" \
  --width 1280 --height 720 --n-seconds 5 \
  --endpoint "$AZURE_OPENAI_ENDPOINT" \
  --api-key "$AZURE_OPENAI_API_KEY"
```

Optional: crop the seed area and/or use a different frame index (0 is typical):

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

Replace variables prior to running.

```bash
ENDPOINT="https://<your-resource>.openai.azure.com"
API_KEY="<your-api-key>"
API_VERSION="2025-04-01-preview"
```

- Create text→video job

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

The response contains `id` (job id).

- Poll job status

```bash
JOB_ID="task_..."
curl -sS "$ENDPOINT/openai/v1/video/generations/jobs/$JOB_ID?api-version=$API_VERSION" \
  -H "api-key: $API_KEY"
```

- Download generated video (once status == succeeded)

```bash
GENERATION_ID="gen_..."
curl -sS "$ENDPOINT/openai/v1/video/generations/$GENERATION_ID/content/video?api-version=$API_VERSION" \
  -H "api-key: $API_KEY" \
  -o output.mp4
```

- Create image→video job (multipart)

```bash
curl -sS -X POST "$ENDPOINT/openai/v1/video/generations/jobs?api-version=$API_VERSION" \
  -H "api-key: $API_KEY" \
  -F "json={\"prompt\":\"Cinematic portrait with subtle motion\",\"width\":720,\"height\":1280,\"n_seconds\":5,\"model\":\"sora\",\"inpaint_items\":[{\"type\":\"image\",\"file_name\":\"face.jpg\",\"frame_index\":0}]}";type=application/json \
  -F "files=@./images/face.jpg;type=image/jpeg"
```

Then poll and download as shown above.

## Notes and limits (preview)
- Durations 1–20s, supported resolutions: 480×480, 854×480, 720×720, 1280×720, 1080×1080, 1920×1080 (both portrait/landscape variants supported).
- Higher resolutions reduce allowed variants; concurrency is limited.
- Outputs are retained for a limited time (~24h). Save results promptly.
- Ensure your resource region supports Sora and use API version `2025-04-01-preview`.

## Troubleshooting
- ImportError: requests — install with `python -m pip install requests`.
- 401/403 — verify you used the correct endpoint, auth header (api-key or Authorization), and that the `sora` deployment exists.
- 400 — check width/height and n_seconds are in the allowed ranges, and JSON/multipart fields are correctly named.
