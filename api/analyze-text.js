// Vercel Serverless Function for Text Emotion Analysis
// Analyzes emotions directly from text input using DeepSeek API

// Simple emotion analysis using basic sentiment keywords
function analyzeTextBasic(text) {
  const words = text.toLowerCase().split(/\s+/);
  
  // Basic emotion keyword mapping
  const emotionKeywords = {
    joy: ['happy', 'excited', 'thrilled', 'delighted', 'joyful', 'cheerful', 'elated', 'glad', 'pleased', 'amazing', 'wonderful', 'fantastic', 'great', 'awesome', 'love', 'adore'],
    sadness: ['sad', 'depressed', 'miserable', 'unhappy', 'crying', 'tears', 'awful', 'terrible', 'horrible', 'devastating', 'heartbroken', 'disappointed'],
    anger: ['angry', 'furious', 'mad', 'rage', 'hate', 'disgusted', 'annoyed', 'irritated', 'frustrated', 'pissed', 'outraged'],
    fear: ['scared', 'afraid', 'terrified', 'worried', 'anxious', 'nervous', 'panic', 'frightened', 'alarmed'],
    surprise: ['surprised', 'shocked', 'amazed', 'astonished', 'wow', 'incredible', 'unbelievable', 'unexpected'],
    disgust: ['disgusting', 'gross', 'nasty', 'revolting', 'sick', 'yuck', 'awful', 'repulsive'],
    trust: ['trust', 'confident', 'reliable', 'faithful', 'loyal', 'honest', 'dependable', 'sure'],
    anticipation: ['excited', 'eager', 'hopeful', 'expecting', 'looking forward', 'anticipating', 'ready']
  };
  
  // Count emotion words
  const emotionScores = {
    joy: 0, sadness: 0, anger: 0, fear: 0, 
    surprise: 0, disgust: 0, trust: 0, anticipation: 0
  };
  
  let totalEmotionWords = 0;
  
  words.forEach(word => {
    Object.keys(emotionKeywords).forEach(emotion => {
      if (emotionKeywords[emotion].includes(word)) {
        emotionScores[emotion]++;
        totalEmotionWords++;
      }
    });
  });
  
  // Calculate probabilities
  let emotions = {};
  if (totalEmotionWords > 0) {
    Object.keys(emotionScores).forEach(emotion => {
      emotions[emotion] = emotionScores[emotion] / totalEmotionWords;
    });
    
    // Normalize to sum to 1
    const total = Object.values(emotions).reduce((a, b) => a + b, 0);
    if (total > 0) {
      Object.keys(emotions).forEach(emotion => {
        emotions[emotion] = emotions[emotion] / total;
      });
    }
  } else {
    // No emotion words found, return neutral
    Object.keys(emotionScores).forEach(emotion => {
      emotions[emotion] = 0.125; // Equal probability
    });
  }
  
  // Find dominant emotion
  const dominantEmotion = Object.keys(emotions).reduce((a, b) => 
    emotions[a] > emotions[b] ? a : b
  );
  
  // Create word analysis
  const wordAnalysis = words.map(word => {
    let wordEmotion = 'neutral';
    let wordConfidence = 0.125;
    
    Object.keys(emotionKeywords).forEach(emotion => {
      if (emotionKeywords[emotion].includes(word)) {
        wordEmotion = emotion;
        wordConfidence = 0.8;
      }
    });
    
    return {
      word: word,
      clean_word: word,
      emotion: wordEmotion,
      confidence: wordConfidence,
      valence: wordEmotion === 'joy' ? 0.8 : wordEmotion === 'sadness' ? 0.2 : 0.5,
      arousal: ['anger', 'fear', 'surprise'].includes(wordEmotion) ? 0.8 : 0.5,
      sentiment: ['joy', 'trust', 'anticipation'].includes(wordEmotion) ? 'positive' : 
                ['sadness', 'anger', 'fear', 'disgust'].includes(wordEmotion) ? 'negative' : 'neutral',
      found: wordEmotion !== 'neutral'
    };
  });
  
  return {
    overall_emotion: dominantEmotion,
    confidence: Math.max(...Object.values(emotions)),
    emotions: emotions,
    word_analysis: wordAnalysis,
    word_count: words.length,
    analyzed_words: wordAnalysis.filter(w => w.found).length,
    coverage: wordAnalysis.filter(w => w.found).length / words.length,
    vad: {
      valence: dominantEmotion === 'joy' ? 0.8 : dominantEmotion === 'sadness' ? 0.2 : 0.5,
      arousal: ['anger', 'fear', 'surprise'].includes(dominantEmotion) ? 0.8 : 0.5,
      dominance: ['anger', 'trust'].includes(dominantEmotion) ? 0.8 : 0.5
    },
    sentiment: {
      polarity: ['joy', 'trust', 'anticipation'].includes(dominantEmotion) ? 'positive' : 
               ['sadness', 'anger', 'fear', 'disgust'].includes(dominantEmotion) ? 'negative' : 'neutral',
      strength: Math.max(...Object.values(emotions))
    }
  };
}

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
    
    // Run the basic emotion analysis
    const startTime = Date.now();
    const emotionAnalysis = analyzeTextBasic(trimmedText);
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
