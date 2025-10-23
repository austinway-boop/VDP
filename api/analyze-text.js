// Vercel Serverless Function for Text Emotion Analysis
// Uses REAL emotion analysis with word database + DeepSeek API

const { emotionEngine } = require('./emotion-engine');
const { authenticate } = require('./auth-middleware');

// Simple in-memory counter (resets on function restart)
let textAnalysisCalls = 0;

// REAL emotion analysis using the actual word database + DeepSeek
async function analyzeTextReal(text) {
  console.log(`🔍 Using REAL emotion analysis engine...`);
  return await emotionEngine.analyzeText(text);
}

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed. Use POST to analyze text.'
    });
  }
  
  // Authenticate the request
  const authResult = await new Promise((resolve) => {
    authenticate(req, res, (err) => {
      resolve(err || null);
    });
  });
  
  if (authResult) {
    return; // Authentication failed, response already sent
  }
  
  try {
    // Increment counter
    textAnalysisCalls++;
    console.log(`🔍 Text analysis called (${textAnalysisCalls} times total)`);
    
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
    
    // Run the REAL emotion analysis
    const startTime = Date.now();
    const emotionAnalysis = await analyzeTextReal(trimmedText);
    const processingTime = (Date.now() - startTime) / 1000;
    
    console.log(`✅ Text analysis completed in ${processingTime.toFixed(2)}s`);
    console.log(`🎭 Primary emotion: ${emotionAnalysis.overall_emotion}`);
    console.log(`📊 Coverage: ${emotionAnalysis.analyzed_words}/${emotionAnalysis.word_count} words`);
    
    // Return successful result
    return res.status(200).json({
      success: true,
      result: {
        transcription: trimmedText,
        confidence: 1.0, // Perfect confidence for direct text input
        emotion_analysis: emotionAnalysis,
        processing_time: processingTime,
        api_processing_time: processingTime,
        needs_review: false,
        success: true,
        error: null,
        input_stats: {
          character_count: trimmedText.length,
          word_count: trimmedText.split(/\s+/).length,
          sentence_count: trimmedText.split(/[.!?]+/).filter(s => s.trim().length > 0).length
        },
        api_calls: {
          text_analysis_calls: textAnalysisCalls,
          this_session: textAnalysisCalls
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
