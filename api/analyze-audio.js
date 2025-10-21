// Vercel Serverless Function for Audio Analysis
// Provides helpful message about serverless limitations

const formidable = require('formidable');
const fs = require('fs');

// Disable body parser to handle multipart/form-data
exports.config = {
  api: {
    bodyParser: false,
  },
};

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed. Use POST to analyze audio.'
    });
  }
  
  let tempFilePath = null;
  
  try {
    // Parse the multipart form data
    const form = formidable({
      maxFileSize: 50 * 1024 * 1024, // 50MB max file size
      keepExtensions: true,
      uploadDir: '/tmp',
    });
    
    const [fields, files] = await new Promise((resolve, reject) => {
      form.parse(req, (err, fields, files) => {
        if (err) reject(err);
        else resolve([fields, files]);
      });
    });
    
    // Check if audio file was provided
    const audioFile = files.audio?.[0] || files.audio;
    if (!audioFile) {
      return res.status(400).json({
        success: false,
        error: 'No audio file provided. Please include an audio file in the "audio" field.'
      });
    }
    
    // Get retry mode if specified
    const retryMode = fields.retry_mode?.[0] || fields.retry_mode || 'normal';
    
    // Validate file size
    if (audioFile.size < 50) {
      return res.status(400).json({
        success: false,
        error: 'Audio file too small or corrupted. Please provide a valid audio file.'
      });
    }
    
    if (audioFile.size > 50 * 1024 * 1024) {
      return res.status(400).json({
        success: false,
        error: 'Audio file too large. Maximum size is 50MB.'
      });
    }
    
    tempFilePath = audioFile.filepath;
    
    // Log file received
    console.log(`🎯 Audio upload received: ${audioFile.originalFilename || 'unknown'}`);
    console.log(`📊 File size: ${audioFile.size} bytes`);
    console.log(`🔄 Retry mode: ${retryMode}`);
    
    // Clean up temp file
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
      tempFilePath = null;
    }
    
    // Return helpful message for serverless environment
    return res.status(200).json({
      success: false,
      error: 'Audio analysis is not available in the serverless environment due to dependency limitations.',
      message: 'Audio file received successfully, but processing requires heavy dependencies not available in serverless functions.',
      suggestion: {
        text: 'Please use the text analysis endpoint instead for emotion analysis.',
        endpoint: '/api/analyze-text',
        method: 'POST',
        example: {
          url: 'https://vdp-peach.vercel.app/api/analyze-text',
          body: { text: 'I am feeling excited about this project!' },
          curl: 'curl -X POST https://vdp-peach.vercel.app/api/analyze-text -H "Content-Type: application/json" -d \'{"text": "I am happy"}\''
        }
      },
      file_received: {
        size: audioFile.size,
        name: audioFile.originalFilename,
        type: audioFile.mimetype,
        processing_time: 0.1
      }
    });
    
  } catch (error) {
    console.error('❌ Audio analysis error:', error);
    
    // Clean up temp file on error
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      try {
        fs.unlinkSync(tempFilePath);
      } catch (cleanupError) {
        console.error('Failed to clean up temp file:', cleanupError);
      }
    }
    
    return res.status(500).json({
      success: false,
      error: 'Internal server error during audio analysis',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
};