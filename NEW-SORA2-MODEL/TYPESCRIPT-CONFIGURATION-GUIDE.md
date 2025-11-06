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
npm install openai dotenv
# or
yarn add openai dotenv
# or
pnpm add openai dotenv
```

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
import { pollVideoStatus, downloadVideo } from './text-to-video';

interface ImageToVideoOptions {
  imagePath: string;
  prompt: string;
  size?: '720x1280' | '1280x720' | '1024x1792' | '1792x1024';
  seconds?: '4' | '8' | '12';
  outputFilename?: string;
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
  } = options;

  console.log('🎨 Starting image-to-video generation...');
  console.log(`   Image: ${imagePath}`);
  console.log(`   Prompt: ${prompt}`);

  try {
    // Read image file
    const imageBuffer = await fs.readFile(imagePath);
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

export { generateImageToVideo };
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
        console.error('   - Image dimensions must match video size');
        console.error('   - Invalid model deployment name');
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
    "dotenv": "^16.0.0"
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
