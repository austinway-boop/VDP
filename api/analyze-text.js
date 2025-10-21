// Vercel Serverless Function for Text Emotion Analysis
// Analyzes emotions directly from text input

import { spawn } from 'child_process';
import path from 'path';

// Helper function to run Python text analysis
async function runTextAnalysis(text) {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(process.cwd(), 'api', 'text_analyzer.py');
    const python = spawn('python3', [pythonScript], {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PYTHONPATH: path.join(process.cwd(), 'api'),
      }
    });
    
    let stdout = '';
    let stderr = '';
    
    // Send text to Python script via stdin
    python.stdin.write(text);
    python.stdin.end();
    
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
      error: 'Method not allowed. Use POST to analyze text.'
    });
  }
  
  try {
    const { text } = req.body;
    
    // Validate input
    if (!text || typeof text !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid input. Please provide text in the "text" field.'
      });
    }
    
    const trimmedText = text.trim();
    if (!trimmedText) {
      return res.status(400).json({
        success: false,
        error: 'Empty text provided. Please provide some text to analyze.'
      });
    }
    
    if (trimmedText.length > 10000) {
      return res.status(400).json({
        success: false,
        error: 'Text too long. Maximum length is 10,000 characters.'
      });
    }
    
    // Log analysis start
    console.log(`🔍 Starting text analysis for: "${trimmedText.substring(0, 100)}${trimmedText.length > 100 ? '...' : ''}"`);
    console.log(`📊 Text length: ${trimmedText.length} characters`);
    console.log(`📝 Word count: ${trimmedText.split(/\s+/).length} words`);
    
    // Run the Python analysis
    const startTime = Date.now();
    const result = await runTextAnalysis(trimmedText);
    const processingTime = (Date.now() - startTime) / 1000;
    
    console.log(`✅ Text analysis completed in ${processingTime.toFixed(2)}s`);
    console.log(`🎭 Primary emotion: ${result.emotion_analysis?.overall_emotion || 'unknown'}`);
    console.log(`📊 Coverage: ${result.emotion_analysis?.analyzed_words || 0}/${result.emotion_analysis?.word_count || 0} words`);
    
    // Return successful result
    return res.status(200).json({
      success: true,
      result: {
        transcription: trimmedText,
        confidence: 1.0, // Perfect confidence for direct text input
        emotion_analysis: result.emotion_analysis,
        processing_time: result.processing_time || 0,
        api_processing_time: processingTime,
        needs_review: false,
        success: true,
        error: null,
        input_stats: {
          character_count: trimmedText.length,
          word_count: trimmedText.split(/\s+/).length,
          sentence_count: trimmedText.split(/[.!?]+/).filter(s => s.trim().length > 0).length
        }
      }
    });
    
  } catch (error) {
    console.error('❌ Text analysis error:', error);
    
    return res.status(500).json({
      success: false,
      error: 'Internal server error during text analysis',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
