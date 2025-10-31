# SORA: Video Generation with Azure OpenAI SORA 2

## About

**Author**: Arturo Quiroga  
**Role**: Cloud Solution Architect - Data & AI at Microsoft  
**GitHub**: [@Arturo-Quiroga-MSFT](https://github.com/Arturo-Quiroga-MSFT)

This repository demonstrates video generation capabilities using Azure OpenAI's SORA 2 model, including text-to-video, image-to-video, and video-to-video transformations. The project features a comprehensive Jupyter notebook that showcases all three generation methods with AI-powered automation.

## Features

### SORA 2 Complete Demo Notebook (NEW-SORA2-MODEL/)

The **SORA-2-Complete-Demo.ipynb** notebook provides a complete, production-ready implementation of SORA 2 video generation:

#### 📹 **Text-to-Video Generation**
- Generate videos directly from natural language prompts
- Support for multiple resolutions (720×1280, 1280×720, 1024×1792, 1792×1024)
- Flexible durations (4, 8, or 12 seconds)
- Best practices for prompt engineering

#### 🎨 **Image-to-Video Generation**
- Animate static images with AI-powered descriptions
- **AI-Powered Mode**: Uses GPT-4o Vision to automatically analyze images and generate descriptive video prompts
- **Manual Mode**: Write your own custom prompts for precise control
- **Automatic Image Resizing**: Intelligently resizes images to match supported video dimensions
- Support for local files and URLs

#### 🎬 **Video-to-Video Transformation**
- Transform and stylize existing videos
- Remix previously generated videos with targeted adjustments
- Maintain motion and structure while applying new styles

#### 🛠️ **Advanced Features**
- Secure credential management with `.env` files
- Automatic dimension validation and image resizing
- Video polling and download automation
- Job management (list, retrieve, delete videos)
- Inline video playback in notebooks
- Comprehensive error handling

### Legacy Notebooks
- **Image to Video**: Generate high-quality videos from images using advanced AI models
- **Video to Video**: Transform existing videos with AI-powered enhancements or style transfers
- **Integration with GPT-4o**: Use GPT-4 Vision for automatic prompt engineering and creative control

## Quick Start

### Prerequisites

1. **Azure OpenAI Resource** with SORA 2 model deployed
2. **Python 3.8+** with Jupyter Notebook support
3. **Azure OpenAI API Key** and endpoint

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Arturo-Quiroga-MSFT/SORA.git
cd SORA
```

2. Install dependencies:
```bash
pip install -r NEW-SORA2-MODEL/requirements.txt
```

3. Create a `.env` file in the `NEW-SORA2-MODEL` directory:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=sora-2
```

4. Open and run the notebook:
```bash
cd NEW-SORA2-MODEL
jupyter notebook SORA-2-Complete-Demo.ipynb
```

## Repository Structure

```
SORA/
├── NEW-SORA2-MODEL/           # Latest SORA 2 implementation
│   ├── SORA-2-Complete-Demo.ipynb  # Main demo notebook
│   ├── .env                        # Configuration (create this)
│   ├── images/                     # Input images directory
│   └── videos/                     # Generated videos output
├── sora-1/                    # Legacy SORA 1 notebooks
└── README.md                  # This file
```

## Technical Specifications

- **Supported Resolutions**: 720×1280 (portrait), 1280×720 (landscape), 1024×1792, 1792×1024
- **Video Durations**: 4, 8, or 12 seconds
- **Concurrent Jobs**: Maximum 2 jobs at once
- **Video Availability**: 24 hours after creation
- **Audio Support**: SORA 2 includes audio generation in output videos

## Best Practices

1. **Prompting**: Be specific about shot type, subject, action, setting, lighting, and camera motion
2. **Resolution Matching**: Images and videos must match output dimensions (or use auto-resize)
3. **Polling**: Use 20-second intervals to avoid excessive API calls
4. **Content Safety**: SORA includes built-in content filtering and safety classifiers

## Documentation

- [Azure OpenAI SORA Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/video-generation)
- See notebook comments for detailed API usage and examples
