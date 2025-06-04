# Copyright (c) Microsoft Corporation.
# the code can be found at https://learn.microsoft.com/en-us/azure/ai-services/openai/video-generation-quickstart?tabs=windows%2Ckeyless

import requests
import base64 
import os
import time
from azure.identity import DefaultAzureCredential

# Set environment variables or edit the corresponding values here.
endpoint = os.environ['AZURE_OPENAI_ENDPOINT']

# Keyless authentication
credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default")

api_version = 'preview'
headers= { "Authorization": f"Bearer {token.token}", "Content-Type": "application/json" }


# 1. Create a video generation job
create_url = f"{endpoint}/openai/v1/video/generations/jobs?api-version={api_version}"
body = {
    "prompt": """
Create a video of cinematic quality of a horse galloping through a lush green meadow. The horse should be majestic, with a shiny coat and flowing mane.
The video should capture the grace and power of the horse as it runs freely, with the sun shining and a clear blue sky in the background.
The camera should follow the horse, showing its movements from different angles, including close-ups of its face and hooves.
The background should be vibrant and natural, with wildflowers and tall grass swaying in the breeze.
    """,
    "width": 480,
    "height": 480,
    "n_seconds": 8,
    "model": "sora"
}
response = requests.post(create_url, headers=headers, json=body)
response.raise_for_status()
print("Full response JSON:", response.json())
job_id = response.json()["id"]
print(f"Job created: {job_id}")

# 2. Poll for job status
status_url = f"{endpoint}/openai/v1/video/generations/jobs/{job_id}?api-version={api_version}"
status=None
while status not in ("succeeded", "failed", "cancelled"):
    time.sleep(5)  # Wait before polling again
    status_response = requests.get(status_url, headers=headers).json()
    status = status_response.get("status")
    print(f"Job status: {status}")

# 3. Retrieve generated video 
if status == "succeeded":
    generations = status_response.get("generations", [])
    if generations:
        print(f"✅ Video generation succeeded.")
        generation_id = generations[0].get("id")
        video_url = f"{endpoint}/openai/v1/video/generations/{generation_id}/content/video?api-version={api_version}"
        video_response = requests.get(video_url, headers=headers)
        if video_response.ok:
            output_filename = f"output.mp4"
            with open(output_filename, "wb") as file:
                file.write(video_response.content)
                print(f'Generated video saved as "{output_filename}"')
    else:
        raise Exception("No generations found in job result.")
else:
    raise Exception(f"Job didn't succeed. Status: {status}")