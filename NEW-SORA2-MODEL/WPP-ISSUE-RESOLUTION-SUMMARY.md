# Response to Priya Devakumar - WPP SORA 2 Issue Update

**Date**: January 8, 2026  
**To**: Priya Devakumar (pdevakumar@microsoft.com)  
**From**: Arturo Quiroga (arturoqu@microsoft.com)  
**Subject**: RE: WPP SORA 2 Issue - Solution Provided

---

## Executive Summary

✅ **Issue Resolved**: The WPP customer's "400 Inpaint image must match the requested width and height" error has been addressed with a complete solution in the TypeScript Configuration Guide.

---

## Issue Timeline

### Issue #1: 404 Error (November 6, 2025)
- **Status**: ✅ Resolved
- **Problem**: Endpoint missing `/openai/v1/` path
- **Solution**: Updated endpoint format documentation
- **Customer Confirmation**: Marius confirmed resolution on November 7, 2025

### Issue #2: Image Dimension Error (November 10, 2025)
- **Status**: ✅ Solution Provided (January 8, 2026)
- **Problem**: "400 Inpaint image must match the requested width and height"
- **Root Cause**: SORA 2 requires pixel-perfect dimension matching
- **Solution**: Added automatic image resizing functionality to TypeScript guide

---

## Technical Solution Details

### Problem
WPP was getting dimension mismatch errors even when providing images that "looked" the right size. SORA 2 requires EXACT pixel-perfect matching (e.g., an image must be exactly 1280x720, not 1280x719).

### Solution Provided
Updated the TypeScript Configuration Guide with:

1. **Image Dimension Validation**
   - `getImageDimensions()` function using `sharp` library
   - Validates exact pixel dimensions before API call

2. **Automatic Image Resizing**
   - `resizeImageForVideo()` function with smart cropping
   - Maintains aspect ratio while achieving exact dimensions
   - Uses Lanczos3 resampling for high quality

3. **Updated `generateImageToVideo()` Function**
   - New `autoResize` parameter (default: `true`)
   - Automatically detects and fixes dimension mismatches
   - Prevents the 400 error before it happens

### Code Example for WPP
```typescript
import { generateImageToVideo } from './image-to-video';

await generateImageToVideo({
  imagePath: './their-image.jpg',
  prompt: 'Animation prompt',
  size: '1280x720',
  autoResize: true, // ✅ Automatically handles dimension mismatches
});
```

---

## Documentation Updates

**File**: `TYPESCRIPT-CONFIGURATION-GUIDE.md`  
**Location**: https://github.com/Arturo-Quiroga-MSFT/SORA/blob/main/NEW-SORA2-MODEL/TYPESCRIPT-CONFIGURATION-GUIDE.md

### Updates Include:

1. **Added `sharp` dependency**
   - Required for image processing
   - `npm install sharp`

2. **New Section**: "WPP Customer Issues - Solutions"
   - Documents both reported issues
   - Provides complete solutions with code examples
   - Includes verification scripts

3. **Enhanced Image-to-Video Section**
   - Complete rewrite with dimension handling
   - Automatic resize functionality
   - Multiple solution approaches

4. **Improved Error Handling**
   - Specific guidance for "Inpaint image must match" error
   - Troubleshooting steps
   - Validation scripts

---

## Customer Communication

### Recommended Response to WPP

```
Hi Marius,

Thank you for your patience. We've updated the TypeScript Configuration Guide 
with a complete solution for the image dimension error you reported.

Solution:
The updated guide now includes automatic image resizing to handle the 
"Inpaint image must match" error. This happens because SORA 2 requires 
pixel-perfect dimension matching.

What you need to do:
1. Install the sharp library: npm install sharp
2. Use the updated generateImageToVideo() function from the guide
3. Set autoResize: true (it's the default)

Updated Guide:
https://github.com/Arturo-Quiroga-MSFT/SORA/blob/main/NEW-SORA2-MODEL/TYPESCRIPT-CONFIGURATION-GUIDE.md

The section "WPP Customer Issues - Solutions" specifically addresses your 
reported issue with complete code examples.

Please let me know if you need any additional assistance.

Best regards,
Arturo Quiroga
```

---

## Testing Recommendations

For WPP to verify the solution:

1. **Install Dependencies**
   ```bash
   npm install sharp
   ```

2. **Test with Their Images**
   ```typescript
   // Verify dimensions first
   import { getImageDimensions } from './image-to-video';
   const dims = await getImageDimensions('./test-image.jpg');
   console.log(`Dimensions: ${dims.width}x${dims.height}`);
   ```

3. **Generate Video with Auto-Resize**
   ```typescript
   await generateImageToVideo({
     imagePath: './test-image.jpg',
     prompt: 'Test animation',
     size: '1280x720',
     autoResize: true,
   });
   ```

---

## Additional Notes

- The Python notebook already had this functionality (added November 2025)
- TypeScript guide now has feature parity with Python implementation
- Solution uses industry-standard `sharp` library (same as Python's PIL)
- All changes committed and pushed to the public GitHub repository

---

## Next Steps

1. **Customer Communication**: Notify WPP that solution is available
2. **Validation**: Confirm WPP tests and validates the solution
3. **Follow-up**: Check back in 1 week for customer feedback
4. **Close Issue**: Mark resolved once customer confirms success

---

## Repository Links

- **Main Repository**: https://github.com/Arturo-Quiroga-MSFT/SORA
- **TypeScript Guide**: https://github.com/Arturo-Quiroga-MSFT/SORA/blob/main/NEW-SORA2-MODEL/TYPESCRIPT-CONFIGURATION-GUIDE.md
- **Python Notebook** (Reference): https://github.com/Arturo-Quiroga-MSFT/SORA/blob/main/NEW-SORA2-MODEL/SORA-2-Complete-Demo.ipynb

---

**Status**: ✅ Solution Complete and Documented  
**Customer Action Required**: Test and validate the updated guide  
**Microsoft Action Required**: Communicate solution to WPP

---

For any questions or additional support needed, please contact:

**Arturo Quiroga**  
Azure AI Services Engineer  
Partner Solutions Architect (PSA)  
arturoqu@microsoft.com
