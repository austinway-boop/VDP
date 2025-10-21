// Vercel Serverless Function for Audio Analysis
// Converts audio to text and analyzes emotions

import formidable from 'formidable';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { promisify } from 'util';

// Disable body parser to handle multipart/form-data
export const config = {
  api: {
    bodyParser: false,
  },
};

// Helper function to run Python scripts
async function runPythonAnalysis(audioFilePath, retryMode = 'normal') {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(process.cwd(), 'python', 'audio_analyzer.py');
    const args = [pythonScript, audioFilePath];
    
    if (retryMode === 'aggressive') {
      args.push('--retry-mode', 'aggressive');
    }
    
    const python = spawn('python3', args, {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PYTHONPATH: path.join(process.cwd(), 'python'),
      }
    });
    
    let stdout = '';
    let stderr = '';
    
    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    python.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${e.message}`));
        }
      } else {
        reject(new Error(`Python script failed with code ${code}: ${stderr}`));
      }
    });
    
    python.on('error', (error) => {
      reject(new Error(`Failed to start Python process: ${error.message}`));
    });
  });
}

export default async function handler(req, res) {
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
    
    // Log analysis start
    console.log(`🎯 Starting audio analysis for file: ${audioFile.originalFilename || 'unknown'}`);
    console.log(`📊 File size: ${audioFile.size} bytes`);
    console.log(`🔄 Retry mode: ${retryMode}`);
    
    // Run the Python analysis
    const startTime = Date.now();
    const result = await runPythonAnalysis(tempFilePath, retryMode);
    const processingTime = (Date.now() - startTime) / 1000;
    
    console.log(`✅ Analysis completed in ${processingTime.toFixed(2)}s`);
    console.log(`📝 Transcription: "${result.transcription || 'No speech detected'}"`);
    console.log(`🎭 Primary emotion: ${result.emotion_analysis?.overall_emotion || 'unknown'}`);
    
    // Clean up temp file
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
      tempFilePath = null;
    }
    
    // Check if analysis succeeded
    if (!result.success || result.error || !result.transcription?.trim()) {
      return res.status(400).json({
        success: false,
        error: result.error || 'Speech recognition failed. Please try speaking louder or in a quieter environment.',
        details: {
          confidence: result.confidence || 0,
          processing_time: processingTime,
          file_info: {
            size: audioFile.size,
            name: audioFile.originalFilename
          }
        }
      });
    }
    
    // Return successful result
    return res.status(200).json({
      success: true,
      result: {
        ...result,
        api_processing_time: processingTime,
        file_info: {
          size: audioFile.size,
          name: audioFile.originalFilename,
          type: audioFile.mimetype
        }
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
}
