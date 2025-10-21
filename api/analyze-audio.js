module.exports = (req, res) => {
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
  
  // Return helpful message for serverless environment
  return res.status(200).json({
    success: false,
    error: 'Audio analysis is not available in the serverless environment.',
    message: 'Please use the text analysis endpoint instead.',
    suggestion: {
      endpoint: '/api/analyze-text',
      method: 'POST',
      example: 'curl -X POST https://vdp-peach.vercel.app/api/analyze-text -H "Content-Type: application/json" -d \'{"text": "I am happy"}\''
    }
  });
};