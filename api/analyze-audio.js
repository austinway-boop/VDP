// Simple in-memory counter (resets on function restart)
let audioCalls = 0;

module.exports = (req, res) => {
  // Increment audio counter
  audioCalls++;
  
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
      error: 'Method not allowed. Use POST to analyze audio.'
    });
  }
  
  try {
    console.log(`🎯 Audio endpoint called (${audioCalls} times total)`);
    console.log('📊 Content-Type:', req.headers['content-type']);
    console.log('📊 Method:', req.method);
    
    // Return helpful message for serverless environment
    return res.status(200).json({
      success: false,
      error: 'Audio analysis is not available in the serverless environment.',
      message: 'Audio processing requires heavy dependencies that are not available in Vercel serverless functions.',
      suggestion: {
        text: 'Please use the text analysis endpoint instead for emotion analysis.',
        endpoint: '/api/analyze-text',
        method: 'POST',
        example: {
          url: 'https://vdp-peach.vercel.app/api/analyze-text',
          body: { text: 'Type what you said here for emotion analysis!' },
          curl: 'curl -X POST https://vdp-peach.vercel.app/api/analyze-text -H "Content-Type: application/json" -d \'{"text": "I am excited!"}\''
        }
      },
      debug_info: {
        endpoint_reached: true,
        method: req.method,
        content_type: req.headers['content-type'],
        timestamp: new Date().toISOString()
      },
      api_calls: {
        audio_calls: audioCalls,
        this_session: audioCalls
      }
    });
    
  } catch (error) {
    console.error('❌ Audio endpoint error:', error);
    
    return res.status(200).json({
      success: false,
      error: 'Audio endpoint error',
      message: 'An error occurred, but audio analysis is not supported anyway.',
      suggestion: {
        text: 'Please use the text analysis endpoint instead.',
        endpoint: '/api/analyze-text'
      },
      debug_info: {
        error_message: error.message,
        error_stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
      }
    });
  }
};