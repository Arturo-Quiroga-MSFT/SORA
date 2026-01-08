# Azure OpenAI SORA 2 - TypeScript/Node.js Configuration Guide

## Overview

This guide provides TypeScript/Node.js specific configuration and implementation details for Azure OpenAI's SORA 2 model. The endpoint format is critical for successful API calls.

## Correct Endpoint Format

The SORA 2 API requires the **v1 endpoint format**:

```
https://{your-resource-name}.openai.azure.com/openai/v1/
```

### Complete Example:

```typescript
const endpoint = "https://your-resource-name.openai.azure.com/openai/v1/";
```

⚠️ **Important**: The trailing slash `/` at the end is required!

---

## Installation

### Install Required Packages

```bash
npm install openai dotenv sharp
# or
yarn add openai dotenv sharp
# or
pnpm add openai dotenv sharp
```

**Note**: `sharp` is required for image processing and dimension validation

### TypeScript Type Definitions

```bash
npm install --save-dev @types/node
# or
yarn add -D @types/node
```

---

## Environment Configuration

### 1. Create `.env` File

Create a `.env` file in your project root:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=sora-2
```

### 2. Create `.env.example` (for version control)

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=sora-2
```

### 3. Update `.gitignore`

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Dependencies
node_modules/

# Build outputs
dist/
build/
```

---

## Basic Configuration

### TypeScript Configuration

```typescript
// config.ts
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

interface AzureOpenAIConfig {
  endpoint: string;
  apiKey: string;
  deploymentName: string;
}

export const config: AzureOpenAIConfig = {
  endpoint: process.env.AZURE_OPENAI_ENDPOINT || '',
  apiKey: process.env.AZURE_OPENAI_API_KEY || '',
  deploymentName: process.env.AZURE_OPENAI_DEPLOYMENT_NAME || 'sora-2',
};

// Validation
export function validateConfig(): void {
  if (!config.endpoint) {
    throw new Error('AZURE_OPENAI_ENDPOINT is not set in environment variables');
  }

  if (!config.endpoint.endsWith('/openai/v1/')) {
    throw new Error(
      `AZURE_OPENAI_ENDPOINT must end with '/openai/v1/'. Current value: ${config.endpoint}`
    );
  }

  if (!config.apiKey) {
    throw new Error('AZURE_OPENAI_API_KEY is not set in environment variables');
  }

  console.log('✅ Configuration validated successfully');
  console.log(`   Endpoint: ${config.endpoint}`);
  console.log(`   Deployment: ${config.deploymentName}`);
}
```

---

## OpenAI Client Setup

### Initialize the Client

```typescript
// client.ts
import OpenAI from 'openai';
import { config, validateConfig } from './config';

// Validate configuration on startup
validateConfig();

// Initialize OpenAI client for Azure
export const client = new OpenAI({
  apiKey: config.apiKey,
  baseURL: config.endpoint,
  defaultHeaders: {
    'api-key': config.apiKey,
  },
  defaultQuery: undefined,
});

console.log('✅ OpenAI client initialized');
```

---

## SORA 2 Video Generation Examples

### 1. Text-to-Video Generation

```typescript
// text-to-video.ts
import { client } from './client';
import { config } from './config';
import fs from 'fs/promises';
import path from 'path';

interface VideoGenerationOptions {
  prompt: string;
  size?: '720x1280' | '1280x720' | '1024x1792' | '1792x1024';
  seconds?: '4' | '8' | '12';
  outputFilename?: string;
}

async function generateTextToVideo(
  options: VideoGenerationOptions
): Promise<string> {
  const {
    prompt,
    size = '1280x720',
    seconds = '8',
    outputFilename = 'output.mp4',
  } = options;

  console.log('🎬 Starting video generation...');
  console.log(`   Prompt: ${prompt}`);
  console.log(`   Size: ${size}`);
  console.log(`   Duration: ${seconds}s`);

  try {
    // Create video generation job
    const video = await client.videos.create({
      model: config.deploymentName,
      prompt: prompt,
      size: size,
      seconds: seconds, // Must be string: "4", "8", or "12"
    });

    console.log(`✅ Video job created: ${video.id}`);
    console.log(`   Status: ${video.status}`);

    // Poll for completion
    let completedVideo = await pollVideoStatus(video.id);

    if (completedVideo.status === 'completed') {
      // Download video
      const videoPath = await downloadVideo(completedVideo.id, outputFilename);
      console.log(`✅ Video saved to: ${videoPath}`);
      return videoPath;
    } else {
      throw new Error(`Video generation failed with status: ${completedVideo.status}`);
    }
  } catch (error) {
    console.error('❌ Error generating video:', error);
    throw error;
  }
}

async function pollVideoStatus(
  videoId: string,
  maxAttempts: number = 30,
  pollInterval: number = 20000
): Promise<any> {
  console.log('⏳ Polling video status...');

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const video = await client.videos.retrieve(videoId);

    console.log(`   [Attempt ${attempt + 1}] Status: ${video.status} | Progress: ${video.progress}%`);

    if (video.status === 'completed' || video.status === 'failed' || video.status === 'cancelled') {
      return video;
    }

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }

  throw new Error('Video generation timed out');
}

async function downloadVideo(videoId: string, filename: string): Promise<string> {
  console.log('📥 Downloading video...');

  const content = await client.videos.downloadContent(videoId, { variant: 'video' });
  
  // Ensure output directory exists
  const outputDir = path.join(process.cwd(), 'videos');
  await fs.mkdir(outputDir, { recursive: true });
  
  const outputPath = path.join(outputDir, filename);
  
  // Write video content to file
  await fs.writeFile(outputPath, Buffer.from(await content.arrayBuffer()));
  
  const stats = await fs.stat(outputPath);
  console.log(`   File size: ${(stats.size / (1024 * 1024)).toFixed(2)} MB`);
  
  return outputPath;
}

// Example usage
async function main() {
  try {
    const videoPath = await generateTextToVideo({
      prompt: 'A cool cat wearing sunglasses riding a motorcycle through a neon-lit city street at night',
      size: '1280x720',
      seconds: '8',
      outputFilename: 'cat_motorcycle.mp4',
    });

    console.log('🎉 Video generation complete!');
  } catch (error) {
    console.error('Failed to generate video:', error);
    process.exit(1);
  }
}

// Run if this is the main module
if (require.main === module) {
  main();
}

export { generateTextToVideo, pollVideoStatus, downloadVideo };
```

### 2. Image-to-Video Generation

```typescript
// image-to-video.ts
import { client } from './client';
import { config } from './config';
import fs from 'fs/promises';
import path from 'path';
import sharp from 'sharp';
import { pollVideoStatus, downloadVideo } from './text-to-video';

interface ImageToVideoOptions {
  imagePath: string;
  prompt: string;
  size?: '720x1280' | '1280x720' | '1024x1792' | '1792x1024';
  seconds?: '4' | '8' | '12';
  outputFilename?: string;
  autoResize?: boolean; // Automatically resize image to match video dimensions
}

/**
 * Get image dimensions using sharp
 */
async function getImageDimensions(imagePath: string): Promise<{ width: number; height: number }> {
  const metadata = await sharp(imagePath).metadata();
  return {
    width: metadata.width || 0,
    height: metadata.height || 0,
  };
}

/**
 * Validate if image dimensions match the requested video size
 * 
 * CRITICAL: SORA 2 requires exact dimension matching!
 * Error: "400 Inpaint image must match the requested width and height"
 * means your image dimensions don't match the size parameter
 */
function validateImageDimensions(
  imageWidth: number,
  imageHeight: number,
  videoSize: string
): boolean {
  const [width, height] = videoSize.split('x').map(Number);
  return imageWidth === width && imageHeight === height;
}

/**
 * Resize image to match SORA 2 video dimensions
 * Uses smart cropping to maintain aspect ratio
 */
async function resizeImageForVideo(
  inputPath: string,
  outputPath: string,
  targetSize: string
): Promise<string> {
  const [targetWidth, targetHeight] = targetSize.split('x').map(Number);
  
  console.log(`🔧 Resizing image to ${targetWidth}x${targetHeight}...`);
  
  const image = sharp(inputPath);
  const metadata = await image.metadata();
  
  const origWidth = metadata.width || 0;
  const origHeight = metadata.height || 0;
  const origAspect = origWidth / origHeight;
  const targetAspect = targetWidth / targetHeight;
  
  let resizedImage: sharp.Sharp;
  
  if (origAspect > targetAspect) {
    // Image is wider - crop width
    const newWidth = Math.round(origHeight * targetAspect);
    resizedImage = image.extract({
      left: Math.round((origWidth - newWidth) / 2),
      top: 0,
      width: newWidth,
      height: origHeight,
    });
  } else {
    // Image is taller - crop height
    const newHeight = Math.round(origWidth / targetAspect);
    resizedImage = image.extract({
      left: 0,
      top: Math.round((origHeight - newHeight) / 2),
      width: origWidth,
      height: newHeight,
    });
  }
  
  // Resize to exact target dimensions
  await resizedImage
    .resize(targetWidth, targetHeight, {
      kernel: sharp.kernel.lanczos3,
      fit: 'fill',
    })
    .toFile(outputPath);
  
  console.log(`✅ Image resized from ${origWidth}x${origHeight} to ${targetWidth}x${targetHeight}`);
  console.log(`   Saved to: ${outputPath}`);
  
  return outputPath;
}

async function generateImageToVideo(
  options: ImageToVideoOptions
): Promise<string> {
  const {
    imagePath,
    prompt,
    size = '1280x720',
    seconds = '8',
    outputFilename = 'output.mp4',
    autoResize = true, // Default to auto-resize for convenience
  } = options;

  console.log('🎨 Starting image-to-video generation...');
  console.log(`   Image: ${imagePath}`);
  console.log(`   Prompt: ${prompt}`);
  console.log(`   Target size: ${size}`);

  try {
    // Check if image exists
    await fs.access(imagePath);
    
    // Get image dimensions
    const { width, height } = await getImageDimensions(imagePath);
    console.log(`📐 Image dimensions: ${width}x${height}`);
    
    let finalImagePath = imagePath;
    
    // Validate dimensions
    if (!validateImageDimensions(width, height, size)) {
      console.log(`⚠️  Image dimensions (${width}x${height}) don't match video size (${size})`);
      
      if (autoResize) {
        // Automatically resize the image
        const parsedPath = path.parse(imagePath);
        const resizedPath = path.join(
          parsedPath.dir,
          `${parsedPath.name}_resized_${size}${parsedPath.ext}`
        );
        
        finalImagePath = await resizeImageForVideo(imagePath, resizedPath, size);
      } else {
        throw new Error(
          `Image dimensions (${width}x${height}) must match video size (${size}). ` +
          `Set autoResize=true to automatically resize, or manually resize your image.`
        );
      }
    } else {
      console.log(`✅ Image dimensions match video size`);
    }

    // Read the final image file
    const imageBuffer = await fs.readFile(finalImagePath);
    const imageBlob = new Blob([imageBuffer]);

    // Create video generation job with image reference
    const video = await client.videos.create({
      model: config.deploymentName,
      prompt: prompt,
      size: size,
      seconds: seconds,
      input_reference: imageBlob as any,
    });

    console.log(`✅ Video job created: ${video.id}`);

    // Poll for completion
    const completedVideo = await pollVideoStatus(video.id);

    if (completedVideo.status === 'completed') {
      // Download video
      const videoPath = await downloadVideo(completedVideo.id, outputFilename);
      console.log(`✅ Video saved to: ${videoPath}`);
      return videoPath;
    } else {
      throw new Error(`Video generation failed with status: ${completedVideo.status}`);
    }
  } catch (error) {
    console.error('❌ Error generating video from image:', error);
    throw error;
  }
}

// Example usage
async function main() {
  try {
    const videoPath = await generateImageToVideo({
      imagePath: './images/sample.jpg',
      prompt: 'The scene comes to life with gentle camera motion and natural lighting',
      size: '1280x720',
      seconds: '8',
      outputFilename: 'image_to_video.mp4',
      autoResize: true, // Automatically resize if dimensions don't match
    });

    console.log('🎉 Image-to-video generation complete!');
  } catch (error) {
    console.error('Failed to generate video:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { generateImageToVideo, getImageDimensions, resizeImageForVideo };
```

#### Handling the "400 Inpaint image must match" Error

**Problem**: You get this error even when providing an image with the "same" size.

**Root Cause**: SORA 2 requires **EXACT** pixel-perfect dimension matching. Even 1 pixel difference causes this error.

**Solutions**:

1. **Automatic Resizing (Recommended)**:
```typescript
await generateImageToVideo({
  imagePath: './my-image.jpg',
  prompt: 'Your prompt here',
  size: '1280x720',
  autoResize: true, // Will automatically resize to match
});
```

2. **Manual Validation**:
```typescript
import { getImageDimensions } from './image-to-video';

const dims = await getImageDimensions('./my-image.jpg');
console.log(`Image is ${dims.width}x${dims.height}`);

// Choose matching video size
const videoSize = dims.width > dims.height ? '1280x720' : '720x1280';
```

3. **Pre-resize Images**:
```typescript
import { resizeImageForVideo } from './image-to-video';

// Resize image before generation
await resizeImageForVideo(
  './original.jpg',
  './resized.jpg',
  '1280x720'
);
```

### 3. Video Management Operations

```typescript
// video-management.ts
import { client } from './client';

// List all videos
async function listVideos(limit: number = 10): Promise<void> {
  console.log('📋 Listing videos...');

  try {
    const videos = await client.videos.list({ limit });

    console.log(`Found ${videos.data.length} videos:\n`);

    for (const video of videos.data) {
      const statusEmoji = video.status === 'completed' ? '✅' : 
                          video.status === 'failed' ? '❌' : '⏳';
      
      console.log(`${statusEmoji} ID: ${video.id}`);
      console.log(`   Status: ${video.status} | Progress: ${video.progress}%`);
      console.log(`   Size: ${video.size} | Duration: ${video.seconds}s`);
      console.log(`   Created: ${video.created_at}`);
      console.log('');
    }
  } catch (error) {
    console.error('❌ Error listing videos:', error);
    throw error;
  }
}

// Retrieve specific video
async function getVideo(videoId: string): Promise<any> {
  console.log(`🔍 Retrieving video: ${videoId}`);

  try {
    const video = await client.videos.retrieve(videoId);
    console.log(`✅ Video found:`);
    console.log(`   Status: ${video.status}`);
    console.log(`   Progress: ${video.progress}%`);
    return video;
  } catch (error) {
    console.error('❌ Error retrieving video:', error);
    throw error;
  }
}

// Delete video
async function deleteVideo(videoId: string): Promise<void> {
  console.log(`🗑️  Deleting video: ${videoId}`);

  try {
    await client.videos.delete(videoId);
    console.log('✅ Video deleted successfully');
  } catch (error) {
    console.error('❌ Error deleting video:', error);
    throw error;
  }
}

export { listVideos, getVideo, deleteVideo };
```

---

## Error Handling

### Common Errors and Solutions

```typescript
// error-handler.ts
import { OpenAI } from 'openai';

export function handleOpenAIError(error: unknown): never {
  if (error instanceof OpenAI.APIError) {
    switch (error.status) {
      case 404:
        console.error('❌ 404 Not Found Error');
        console.error('   Problem: Endpoint URL is incorrect');
        console.error('   Solution: Verify endpoint ends with /openai/v1/');
        console.error(`   Current endpoint: ${process.env.AZURE_OPENAI_ENDPOINT}`);
        break;

      case 401:
        console.error('❌ 401 Unauthorized Error');
        console.error('   Problem: API key is invalid or expired');
        console.error('   Solution: Check your AZURE_OPENAI_API_KEY');
        break;

      case 400:
        console.error('❌ 400 Bad Request Error');
        console.error('   Problem: Invalid request parameters');
        console.error('   Common causes:');
        console.error('   - seconds parameter must be string: "4", "8", or "12"');
        console.error('   - Image dimensions must EXACTLY match video size (pixel-perfect)');
        console.error('   - Error "Inpaint image must match" = dimension mismatch');
        console.error('   - Invalid model deployment name');
        console.error('   Solution: Use autoResize=true in image-to-video generation');
        break;

      case 429:
        console.error('❌ 429 Rate Limit Error');
        console.error('   Problem: Too many requests');
        console.error('   Solution: Implement retry with backoff');
        break;

      default:
        console.error(`❌ API Error (${error.status}): ${error.message}`);
    }
  } else if (error instanceof Error) {
    console.error(`❌ Error: ${error.message}`);
  } else {
    console.error('❌ Unknown error:', error);
  }

  throw error;
}

// Retry wrapper with exponential backoff
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (error instanceof OpenAI.APIError && error.status === 429) {
        const delay = initialDelay * Math.pow(2, attempt);
        console.log(`⏳ Rate limited. Retrying in ${delay}ms... (Attempt ${attempt + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }

  throw lastError;
}
```

---

## WPP Customer Issues - Solutions

### 🔧 Issue 1: "400 Inpaint image must match the requested width and height"

**Reported**: November 10, 2025  
**Status**: ✅ SOLVED - Solution added to guide

**Problem Description**:
WPP customer reported getting this error when trying image-to-video generation, even when providing images with matching dimensions.

**Root Cause**:
SORA 2 requires **EXACT pixel-perfect** dimension matching. An image that appears to be 1280x720 might actually be 1280x719 or 1281x720.

**Solution Implemented**:
The updated `generateImageToVideo()` function now includes:
- Automatic dimension validation with `getImageDimensions()`
- Smart image resizing with `resizeImageForVideo()` using `sharp` library
- `autoResize` parameter (default: `true`) to automatically handle mismatches

**Code Example for WPP**:
```typescript
// Install sharp for image processing
npm install sharp

// Use the updated function with auto-resize
import { generateImageToVideo } from './image-to-video';

await generateImageToVideo({
  imagePath: './your-image.jpg',
  prompt: 'Your animation prompt here',
  size: '1280x720',
  autoResize: true, // ✅ Automatically fixes dimension mismatches
});
```

**Verification**:
```typescript
// Verify your image dimensions
import { getImageDimensions } from './image-to-video';

const dims = await getImageDimensions('./your-image.jpg');
console.log(`Image dimensions: ${dims.width}x${dims.height}`);
// If not exactly 1280x720, autoResize will fix it
```

---

### 🔧 Issue 2: "404 Resource not found"

**Reported**: November 6, 2025  
**Status**: ✅ RESOLVED

**Problem**:
```typescript
endpoint: "https://wppai-d-01-swedencentral.openai.azure.com/"
// Error: 404 Resource not found
```

**Solution**:
```typescript
endpoint: "https://wppai-d-01-swedencentral.openai.azure.com/openai/v1/"
// Must include /openai/v1/ path
```

---

## Complete Example Application

### Main Application File

```typescript
// index.ts
import { validateConfig } from './config';
import { generateTextToVideo } from './text-to-video';
import { generateImageToVideo } from './image-to-video';
import { listVideos } from './video-management';
import { handleOpenAIError } from './error-handler';

async function main() {
  try {
    // Validate configuration
    validateConfig();

    console.log('\n🎬 Azure OpenAI SORA 2 - TypeScript Demo\n');
    console.log('=' .repeat(60));

    // Example 1: Text-to-Video
    console.log('\n📝 Example 1: Text-to-Video Generation\n');
    await generateTextToVideo({
      prompt: 'A serene mountain lake at sunrise with mist rising from the water',
      size: '1280x720',
      seconds: '8',
      outputFilename: 'mountain_lake.mp4',
    });

    // Example 2: Image-to-Video (if you have an image)
    // console.log('\n🎨 Example 2: Image-to-Video Generation\n');
    // await generateImageToVideo({
    //   imagePath: './images/sample.jpg',
    //   prompt: 'Camera slowly pans across the scene with natural lighting',
    //   size: '1280x720',
    //   seconds: '8',
    //   outputFilename: 'image_animation.mp4',
    // });

    // Example 3: List all videos
    console.log('\n📋 Example 3: List Recent Videos\n');
    await listVideos(5);

    console.log('=' .repeat(60));
    console.log('\n✅ All examples completed successfully!\n');

  } catch (error) {
    handleOpenAIError(error);
    process.exit(1);
  }
}

main();
```

---

## Package.json Scripts

### Add Useful Scripts

```json
{
  "name": "azure-openai-sora2-typescript",
  "version": "1.0.0",
  "description": "Azure OpenAI SORA 2 TypeScript Implementation",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts",
    "text-to-video": "ts-node src/text-to-video.ts",
    "image-to-video": "ts-node src/image-to-video.ts",
    "list-videos": "ts-node src/video-management.ts",
    "validate": "ts-node -e \"require('./src/config').validateConfig()\"",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "openai": "^4.0.0",
    "dotenv": "^16.0.0",
    "sharp": "^0.33.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "ts-node": "^10.0.0"
  }
}
```

---

## TypeScript Configuration

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## Project Structure

```
my-sora2-project/
├── src/
│   ├── index.ts                 # Main application
│   ├── config.ts                # Configuration and validation
│   ├── client.ts                # OpenAI client setup
│   ├── text-to-video.ts         # Text-to-video generation
│   ├── image-to-video.ts        # Image-to-video generation
│   ├── video-management.ts      # Video CRUD operations
│   └── error-handler.ts         # Error handling utilities
├── images/                      # Input images (optional)
├── videos/                      # Generated videos output
├── .env                         # Environment variables (not in git)
├── .env.example                 # Example environment file
├── .gitignore                   # Git ignore rules
├── package.json                 # NPM dependencies
├── tsconfig.json                # TypeScript configuration
└── README.md                    # Project documentation
```

---

## Testing Configuration

### Quick Test Script

```typescript
// test-config.ts
import { validateConfig, config } from './config';
import { client } from './client';

async function testConfiguration() {
  console.log('🧪 Testing Azure OpenAI SORA 2 Configuration\n');

  try {
    // Test 1: Validate config
    console.log('Test 1: Validating configuration...');
    validateConfig();
    console.log('✅ Configuration valid\n');

    // Test 2: Test API connection
    console.log('Test 2: Testing API connection...');
    const videos = await client.videos.list({ limit: 1 });
    console.log('✅ API connection successful\n');

    console.log('🎉 All tests passed!');
  } catch (error) {
    console.error('❌ Configuration test failed:', error);
    process.exit(1);
  }
}

testConfiguration();
```

Run with: `ts-node src/test-config.ts`

---

## Best Practices

### 1. Type Safety

```typescript
// Use type definitions for better IDE support
import type { Video } from 'openai/resources/videos';

interface VideoResult {
  id: string;
  status: string;
  path?: string;
}
```

### 2. Async/Await Error Handling

```typescript
async function safeVideoGeneration(prompt: string): Promise<VideoResult | null> {
  try {
    const path = await generateTextToVideo({ prompt });
    return { id: 'video-id', status: 'completed', path };
  } catch (error) {
    console.error('Video generation failed:', error);
    return null;
  }
}
```

### 3. Environment Variable Validation

```typescript
// Validate at startup
if (process.env.NODE_ENV === 'production') {
  validateConfig();
}
```

---

## Additional Resources

- [OpenAI Node.js SDK Documentation](https://github.com/openai/openai-node)
- [Azure OpenAI SORA Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/video-generation)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)

---

**Last Updated**: November 2025  
**Applies To**: Azure OpenAI SORA 2 with TypeScript/Node.js
