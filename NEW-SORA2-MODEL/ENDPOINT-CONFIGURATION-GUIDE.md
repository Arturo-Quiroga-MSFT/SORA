# Azure OpenAI SORA 2 Endpoint Configuration Guide

## Overview

When working with Azure OpenAI's SORA 2 model, the endpoint URL format is **critical** for successful API calls. A common issue is the 404 "Not Found" error, which typically indicates an incorrect endpoint URL structure.

## Correct Endpoint Format

The SORA 2 API requires the **v1 endpoint format** with the following structure:

```
https://{your-resource-name}.openai.azure.com/openai/v1/
```

### Key Components:

1. **Protocol**: `https://`
2. **Resource Name**: Your Azure OpenAI resource name (e.g., `my-aoai-resource`)
3. **Base Domain**: `.openai.azure.com`
4. **API Path**: `/openai/v1/` (required for SORA 2)

### Complete Example:

```
https://aq-ai-foundry-sweden-central.openai.azure.com/openai/v1/
```

⚠️ **Important**: Note the trailing slash `/` at the end - this is required!

---

## Common Mistakes

### ❌ Incorrect Format (Missing `/openai/v1/`)

```
https://aq-ai-foundry-sweden-central.openai.azure.com/
```

**Result**: 404 Not Found error

### ❌ Incorrect Format (Missing trailing slash)

```
https://aq-ai-foundry-sweden-central.openai.azure.com/openai/v1
```

**Result**: May cause routing issues

### ✅ Correct Format

```
https://aq-ai-foundry-sweden-central.openai.azure.com/openai/v1/
```

---

## Configuration Steps

### 1. Locate Your Azure OpenAI Resource Name

In the Azure Portal:
1. Navigate to your Azure OpenAI resource
2. Note the resource name from the Overview page
3. The endpoint will be: `https://{resource-name}.openai.azure.com/openai/v1/`

### 2. Update Your `.env` File

Create or update your `.env` file with the correct endpoint:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=sora-2
```

### 3. Verify the Configuration

After updating, restart your application or reload environment variables:

**In Jupyter Notebook:**
- Restart the kernel: `Kernel` → `Restart`
- Re-run the configuration cell that loads the `.env` file

**In Python Script:**
- Restart the script
- Environment variables are loaded at script startup

---

## Troubleshooting

### Error: 404 Not Found

**Symptom**: 
```
openai.NotFoundError: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
```

**Solution**:
1. Verify your endpoint includes `/openai/v1/` at the end
2. Check for the trailing slash `/`
3. Ensure no extra spaces or characters in the `.env` file
4. Restart your kernel/application after making changes

### Error: 401 Unauthorized

**Symptom**:
```
openai.AuthenticationError: Error code: 401
```

**Solution**:
- Verify your API key is correct
- Check that the API key has not expired
- Ensure the key has permissions for the SORA deployment

### Error: 400 Bad Request

**Symptom**:
```
openai.BadRequestError: Error code: 400
```

**Common Causes**:
- Incorrect parameter values (e.g., `seconds` must be a string: "4", "8", or "12")
- Image dimensions don't match video size
- Invalid model deployment name

---

## Best Practices

### 1. Use Environment Variables

**✅ Recommended:**
```python
from dotenv import load_dotenv
load_dotenv('.env')

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
```

**❌ Not Recommended:**
```python
# Hardcoding credentials in code
AZURE_OPENAI_ENDPOINT = "https://my-resource.openai.azure.com/openai/v1/"
```

### 2. Validate Configuration on Startup

```python
# Validate required environment variables
if not AZURE_OPENAI_ENDPOINT:
    raise ValueError("AZURE_OPENAI_ENDPOINT not found in .env file")

if not AZURE_OPENAI_ENDPOINT.endswith("/openai/v1/"):
    raise ValueError(
        "AZURE_OPENAI_ENDPOINT must end with '/openai/v1/'. "
        f"Current value: {AZURE_OPENAI_ENDPOINT}"
    )

print(f"✅ Endpoint configured: {AZURE_OPENAI_ENDPOINT}")
```

### 3. Create an Example Configuration File

Provide a `.env.example` file in your repository:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=sora-2
```

---

## Regional Endpoints

Azure OpenAI is available in multiple regions. The endpoint format remains the same, but the resource name changes:

| Region | Example Endpoint |
|--------|-----------------|
| Sweden Central | `https://my-resource-sweden.openai.azure.com/openai/v1/` |
| East US | `https://my-resource-eastus.openai.azure.com/openai/v1/` |
| West Europe | `https://my-resource-westeurope.openai.azure.com/openai/v1/` |
| Australia East | `https://my-resource-australiaeast.openai.azure.com/openai/v1/` |

All require the `/openai/v1/` path for SORA 2 API access.

---

## Quick Checklist

Before running your SORA 2 code, verify:

- [ ] Endpoint URL ends with `/openai/v1/`
- [ ] Trailing slash `/` is present
- [ ] Resource name matches your Azure OpenAI resource
- [ ] API key is valid and has proper permissions
- [ ] Deployment name matches your SORA model deployment
- [ ] `.env` file is in the correct directory
- [ ] No extra spaces or quotes in environment variables
- [ ] Application/kernel restarted after configuration changes

---

## Testing Your Configuration

Use this simple test to verify your endpoint:

```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv('.env')

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# Test by listing models (or use videos.list())
try:
    # Attempt a simple API call
    videos = client.videos.list(limit=1)
    print("✅ Configuration successful!")
    print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
```

---

## Additional Resources

- [Azure OpenAI SORA Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/video-generation)
- [Azure OpenAI Authentication](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/authentication)
- [Environment Variables Best Practices](https://12factor.net/config)

---

## Support

If you continue to experience issues after following this guide:

1. Verify your Azure OpenAI resource is properly deployed
2. Check that SORA 2 model is deployed in your resource
3. Confirm your subscription has access to SORA capabilities
4. Review Azure OpenAI service health status
5. Contact Azure Support for deployment-specific issues

---

**Last Updated**: November 2025  
**Applies To**: Azure OpenAI SORA 2 Model
