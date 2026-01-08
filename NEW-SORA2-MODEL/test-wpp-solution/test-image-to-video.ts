import OpenAI from 'openai';
import * as dotenv from 'dotenv';
import sharp from 'sharp';
import * as fs from 'fs';
import * as path from 'path';

// Load environment variables
dotenv.config();

// Configuration
const endpoint = process.env.AZURE_OPENAI_ENDPOINT;
const apiKey = process.env.AZURE_OPENAI_API_KEY;
const deploymentName = process.env.AZURE_OPENAI_DEPLOYMENT_NAME;

if (!endpoint || !apiKey || !deploymentName) {
  throw new Error('Missing required environment variables');
}

// Initialize Azure OpenAI client
const client = new OpenAI({
  apiKey,
  baseURL: endpoint,
  defaultQuery: { 'api-version': '2024-12-01-preview' },
  defaultHeaders: { 'api-key': apiKey },
});

// Helper function to get image dimensions
async function getImageDimensions(imagePath: string): Promise<{ width: number; height: number }> {
  const metadata = await sharp(imagePath).metadata();
  if (!metadata.width || !metadata.height) {
    throw new Error('Could not determine image dimensions');
  }
  return { width: metadata.width, height: metadata.height };
}

// Helper function to resize image for video generation
async function resizeImageForVideo(
  imagePath: string,
  targetWidth: number,
  targetHeight: number,
  outputPath?: string
): Promise<string> {
  const output = outputPath || imagePath.replace(/(\.[^.]+)$/, `_${targetWidth}x${targetHeight}$1`);

  await sharp(imagePath)
    .resize(targetWidth, targetHeight, {
      fit: 'cover',
      position: 'center',
      kernel: sharp.kernel.lanczos3,
    })
    .toFile(output);

  console.log(`✅ Resized image saved to: ${output}`);
  return output;
}

// Main function to generate image-to-video
async function generateImageToVideo(
  imagePath: string,
  prompt: string,
  videoSize: '720x1280' | '1280x720' | '1024x1792' | '1792x1024' = '1280x720',
  duration: '4' | '8' | '12' = '8',
  autoResize: boolean = true
): Promise<string> {
  console.log('\n🎬 Starting Image-to-Video Generation');
  console.log(`Image: ${imagePath}`);
  console.log(`Prompt: ${prompt}`);
  console.log(`Video Size: ${videoSize}`);
  console.log(`Duration: ${duration}s`);
  console.log(`Auto-Resize: ${autoResize}`);

  // Parse target dimensions
  const [targetWidth, targetHeight] = videoSize.split('x').map(Number);

  // Get current image dimensions
  const { width, height } = await getImageDimensions(imagePath);
  console.log(`\n📐 Current image dimensions: ${width}x${height}`);
  console.log(`📐 Target video dimensions: ${targetWidth}x${targetHeight}`);

  let finalImagePath = imagePath;

  // Check if resize is needed
  if (width !== targetWidth || height !== targetHeight) {
    if (autoResize) {
      console.log('\n⚠️  Dimensions don\'t match - Auto-resizing enabled');
      finalImagePath = await resizeImageForVideo(imagePath, targetWidth, targetHeight);
    } else {
      throw new Error(
        `Image dimensions (${width}x${height}) don't match target video size (${targetWidth}x${targetHeight}). ` +
        `Set autoResize=true to automatically resize the image.`
      );
    }
  } else {
    console.log('\n✅ Image dimensions match target video size perfectly!');
  }

  // Read image as base64
  const imageBuffer = fs.readFileSync(finalImagePath);
  const base64Image = imageBuffer.toString('base64');
  const imageUrl = `data:image/png;base64,${base64Image}`;

  console.log('\n🚀 Submitting video generation job...');

  // Create video generation job
  const response = await client.videos.generate({
    model: deploymentName,
    prompt,
    input_image: imageUrl,
    size: videoSize,
    seconds: duration,
  });

  const jobId = response.id;
  console.log(`✅ Job created with ID: ${jobId}`);

  // Poll for completion
  console.log('\n⏳ Polling for job completion...');
  let video = await client.videos.retrieve(jobId);

  while (video.status === 'pending' || video.status === 'running') {
    console.log(`   Status: ${video.status}...`);
    await new Promise((resolve) => setTimeout(resolve, 5000));
    video = await client.videos.retrieve(jobId);
  }

  if (video.status === 'failed') {
    throw new Error(`Video generation failed: ${JSON.stringify(video, null, 2)}`);
  }

  console.log(`\n✅ Video generation completed!`);

  // Download video
  if (video.output?.data && video.output.data.length > 0) {
    const videoUrl = video.output.data[0].url;
    if (!videoUrl) {
      throw new Error('No video URL in response');
    }

    // Download the video
    console.log('\n⬇️  Downloading video...');
    const videoResponse = await fetch(videoUrl);
    const videoBuffer = Buffer.from(await videoResponse.arrayBuffer());

    // Save to videos directory
    const videosDir = path.join(process.cwd(), '../videos');
    if (!fs.existsSync(videosDir)) {
      fs.mkdirSync(videosDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const videoPath = path.join(videosDir, `image-to-video-${timestamp}.mp4`);
    fs.writeFileSync(videoPath, videoBuffer);

    console.log(`✅ Video saved to: ${videoPath}`);
    return videoPath;
  }

  throw new Error('No video data in response');
}

// Test the solution
async function main() {
  try {
    console.log('🧪 Testing WPP Image-to-Video Solution');
    console.log('=====================================\n');

    // Test with an image from the sora-2/images directory
    const testImagePath = '../../sora-2/images/car.jpg';
    
    console.log('Test Case 1: Auto-resize enabled (default behavior)');
    console.log('---------------------------------------------------');
    
    const videoPath = await generateImageToVideo(
      testImagePath,
      'A sleek car driving through a vibrant city at sunset, with dynamic camera movements',
      '1280x720',
      '8',
      true // Auto-resize enabled
    );

    console.log('\n🎉 SUCCESS! Video generated successfully.');
    console.log(`📹 Video location: ${videoPath}`);
    
    console.log('\n✅ Test completed successfully!');
    console.log('\nThis demonstrates the WPP solution working correctly:');
    console.log('1. ✅ Image dimensions are automatically validated');
    console.log('2. ✅ Image is resized if needed (with smart cropping)');
    console.log('3. ✅ Video generation succeeds without dimension errors');
    console.log('4. ✅ No more "Inpaint image must match" errors!');

  } catch (error) {
    console.error('\n❌ Test failed:', error);
    throw error;
  }
}

// Run the test
main();
