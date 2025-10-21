// Vercel Serverless Function for Audio Analysis
// Provides helpful message about serverless limitations

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
  
  try {
    console.log('🎯 Audio endpoint called');
    
    // Return helpful message for serverless environment
    return res.status(200).json({
      success: false,
      error: 'Audio analysis is not available in the serverless environment.',
      message: 'Audio processing requires heavy dependencies (Python, speech recognition libraries) that are not available in Vercel serverless functions.',
      suggestion: {
        text: 'Please use the text analysis endpoint instead for emotion analysis.',
        endpoint: '/api/analyze-text',
        method: 'POST',
        working_example: {
          url: 'https://vdp-peach.vercel.app/api/analyze-text',
          body: { text: 'I am feeling excited about this project!' },
          curl: 'curl -X POST https://vdp-peach.vercel.app/api/analyze-text -H "Content-Type: application/json" -d \'{"text": "I am happy!"}\''
        }
      },
      alternatives: [
        'Use the text analysis endpoint with manual transcription',
        'Deploy the full Python system on a traditional server',
        'Use a different audio processing service'
      ],
      status: 'audio_not_supported_in_serverless'
    });
    
  } catch (error) {
    console.error('❌ Audio endpoint error:', error);
    
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      message: 'An unexpected error occurred in the audio endpoint.',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
};