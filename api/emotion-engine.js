// Real Emotion Analysis Engine for JavaScript
// Converts the Python word database system to pure JavaScript

const fs = require('fs');
const path = require('path');

class EmotionEngine {
    constructor() {
        this.wordCache = new Map();
        this.deepseekApiKey = process.env.DEEPSEEK_API_KEY;
        this.loadWordDatabase();
    }
    
    loadWordDatabase() {
        console.log('📚 Loading word emotion database...');
        
        try {
            // Load all word JSON files
            const wordsDir = path.join(process.cwd(), 'words');
            const files = fs.readdirSync(wordsDir).filter(f => f.endsWith('.json'));
            
            let totalWords = 0;
            
            for (const file of files) {
                try {
                    const filePath = path.join(wordsDir, file);
                    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                    
                    if (data.words && Array.isArray(data.words)) {
                        for (const wordEntry of data.words) {
                            if (wordEntry.word && wordEntry.stats) {
                                this.wordCache.set(wordEntry.word.toLowerCase(), wordEntry.stats);
                                totalWords++;
                            }
                        }
                    }
                } catch (fileError) {
                    console.error(`Error loading ${file}:`, fileError.message);
                }
            }
            
            console.log(`✅ Loaded emotion data for ${totalWords} words`);
            
        } catch (error) {
            console.error('❌ Error loading word database:', error.message);
            // Continue with empty database - will use DeepSeek for all words
        }
    }
    
    async analyzeText(text) {
        console.log(`🔍 Analyzing text: "${text}"`);
        
        const words = text.toLowerCase().split(/\s+/);
        const cleanWords = words.map(word => word.replace(/[^a-zA-Z0-9]/g, ''));
        
        console.log(`📝 Processing ${cleanWords.length} words`);
        
        // Analyze each word
        const wordAnalyses = [];
        const unknownWords = [];
        
        for (let i = 0; i < cleanWords.length; i++) {
            const originalWord = words[i];
            const cleanWord = cleanWords[i];
            
            if (!cleanWord || cleanWord.length < 1) {
                continue;
            }
            
            // Check if we have this word in our database
            const emotionData = this.wordCache.get(cleanWord);
            
            if (emotionData) {
                // Use real emotion data from database
                const dominantEmotion = this.getDominantEmotion(emotionData.emotion_probs);
                
                wordAnalyses.push({
                    word: originalWord,
                    clean_word: cleanWord,
                    emotion: dominantEmotion.emotion,
                    confidence: dominantEmotion.confidence,
                    valence: emotionData.vad.valence,
                    arousal: emotionData.vad.arousal,
                    sentiment: emotionData.sentiment.polarity,
                    found: true,
                    source: 'database',
                    emotion_probs: emotionData.emotion_probs
                });
                
                console.log(`✅ "${cleanWord}" found in database: ${dominantEmotion.emotion} (${(dominantEmotion.confidence * 100).toFixed(1)}%)`);
                
            } else {
                // Word not in database - will need DeepSeek
                unknownWords.push({
                    word: originalWord,
                    clean_word: cleanWord,
                    index: i
                });
                
                // Add placeholder for now
                wordAnalyses.push({
                    word: originalWord,
                    clean_word: cleanWord,
                    emotion: 'neutral',
                    confidence: 0.125,
                    valence: 0.5,
                    arousal: 0.5,
                    sentiment: 'neutral',
                    found: false,
                    source: 'unknown'
                });
                
                console.log(`❓ "${cleanWord}" not in database - will use DeepSeek`);
            }
        }
        
        // Process unknown words with DeepSeek if we have an API key
        if (unknownWords.length > 0 && this.deepseekApiKey) {
            console.log(`🤖 Processing ${unknownWords.length} unknown words with DeepSeek...`);
            
            for (const unknownWord of unknownWords.slice(0, 5)) { // Limit to 5 to avoid timeout
                try {
                    const deepseekResult = await this.analyzeWordWithDeepSeek(unknownWord.clean_word);
                    if (deepseekResult) {
                        // Update the word analysis with real DeepSeek result
                        const wordIndex = wordAnalyses.findIndex(w => w.clean_word === unknownWord.clean_word);
                        if (wordIndex !== -1) {
                            const dominantEmotion = this.getDominantEmotion(deepseekResult.emotion_probs);
                            wordAnalyses[wordIndex] = {
                                ...wordAnalyses[wordIndex],
                                emotion: dominantEmotion.emotion,
                                confidence: dominantEmotion.confidence,
                                valence: deepseekResult.vad.valence,
                                arousal: deepseekResult.vad.arousal,
                                sentiment: deepseekResult.sentiment.polarity,
                                found: true,
                                source: 'deepseek',
                                emotion_probs: deepseekResult.emotion_probs
                            };
                            
                            console.log(`🤖 DeepSeek analyzed "${unknownWord.clean_word}": ${dominantEmotion.emotion} (${(dominantEmotion.confidence * 100).toFixed(1)}%)`);
                        }
                    }
                } catch (deepseekError) {
                    console.error(`❌ DeepSeek failed for "${unknownWord.clean_word}":`, deepseekError.message);
                }
            }
        }
        
        // Calculate overall emotion from word analyses (like original system)
        return this.calculateOverallEmotion(wordAnalyses, text);
    }
    
    getDominantEmotion(emotionProbs) {
        let maxEmotion = 'neutral';
        let maxConfidence = 0;
        
        for (const [emotion, probability] of Object.entries(emotionProbs)) {
            if (probability > maxConfidence) {
                maxConfidence = probability;
                maxEmotion = emotion;
            }
        }
        
        return { emotion: maxEmotion, confidence: maxConfidence };
    }
    
    async analyzeWordWithDeepSeek(word) {
        if (!this.deepseekApiKey) {
            return null;
        }
        
        const prompt = `Analyze the word "${word}" for its emotional connotations and psychological impact.

GOAL: Create ACCURATE and DISTINCTIVE emotion predictions that clearly differentiate between emotions.

Think deeply about:
1. What emotions does this word typically evoke in people?
2. Is it positive, negative, or neutral in feeling (valence)?
3. How energetic or calm does it make people feel (arousal)?
4. Does it convey power/control or submission (dominance)?
5. What is the overall sentiment and strength?

EMOTION ASSIGNMENT RULES:
- BE DECISIVE: If a word has emotional content, make it CLEAR in the probabilities
- NEUTRAL words (pronouns, articles, prepositions): Use equal probabilities (0.125 each)
- EMOTIONAL words: Give the primary emotion 0.4-0.7, secondary 0.1-0.3, others 0.01-0.05
- STRONG emotional words: Primary emotion should be 0.6+
- MODERATE emotional words: Primary emotion should be 0.4-0.6
- WEAK emotional words: Primary emotion should be 0.25-0.4

Based on your analysis, provide the emotion data in this exact JSON format:

{
  "emotion_probs": {
    "joy": 0.125,
    "trust": 0.125,
    "anticipation": 0.125,
    "surprise": 0.125,
    "anger": 0.125,
    "fear": 0.125,
    "sadness": 0.125,
    "disgust": 0.125
  },
  "vad": {
    "valence": 0.5,
    "arousal": 0.5,
    "dominance": 0.5
  },
  "sentiment": {
    "polarity": "neutral",
    "strength": 0.5
  }
}

Rules:
- emotion_probs must sum to 1.0
- vad values: 0.0 to 1.0 (valence: negative to positive, arousal: calm to energetic, dominance: submissive to dominant)
- Return ONLY the JSON, no explanation`;

        try {
            const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.deepseekApiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'deepseek-chat',
                    messages: [{ role: 'user', content: prompt }],
                    temperature: 0.1,
                    max_tokens: 800
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                let content = result.choices[0].message.content.trim();
                
                // Clean response
                if (content.startsWith('```json')) {
                    content = content.replace('```json', '').replace('```', '').trim();
                } else if (content.startsWith('```')) {
                    const lines = content.split('\n');
                    for (const line of lines) {
                        if (line.trim().startsWith('{"emotion_probs"')) {
                            content = line.trim();
                            break;
                        }
                    }
                }
                
                const wordData = JSON.parse(content);
                console.log(`🤖 DeepSeek processed "${word}":`, wordData);
                return wordData;
                
            } else {
                console.error(`❌ DeepSeek API error: ${response.status}`);
                return null;
            }
            
        } catch (error) {
            console.error(`❌ DeepSeek processing error for "${word}":`, error.message);
            return null;
        }
    }
    
    calculateOverallEmotion(wordAnalyses, text) {
        console.log('🧮 Calculating overall emotion from word analyses...');
        
        // Filter to only confident words (like original system)
        const CONFIDENCE_THRESHOLD = 0.25;
        const confidentWords = wordAnalyses.filter(w => w.found && w.confidence > CONFIDENCE_THRESHOLD);
        
        console.log(`📊 Using ${confidentWords.length} confident words out of ${wordAnalyses.length} total`);
        
        if (confidentWords.length === 0) {
            // No confident words - return neutral (like original)
            return this.getNeutralResult(wordAnalyses, text);
        }
        
        // Weighted emotion calculation (like original system)
        const emotionWeights = {
            joy: 0, trust: 0, anticipation: 0, surprise: 0,
            anger: 0, fear: 0, sadness: 0, disgust: 0
        };
        
        for (const wordData of confidentWords) {
            const emotionProbs = wordData.emotion_probs || this.getDefaultEmotionProbs(wordData.emotion);
            
            // Apply amplification for strong emotions (like original)
            let amplification = 1.0;
            if (wordData.confidence > 0.5) {
                amplification = 3.0; // Very strong emotional word
            } else if (wordData.confidence > 0.3) {
                amplification = 2.5; // Strong emotional word
            } else {
                amplification = 2.0; // Moderate emotional word
            }
            
            // Add weighted scores
            for (const emotion of Object.keys(emotionWeights)) {
                const baseScore = emotionProbs[emotion] || 0.125;
                const weightedScore = emotion === wordData.emotion ? 
                    baseScore * amplification : baseScore;
                emotionWeights[emotion] += weightedScore;
            }
        }
        
        // Normalize the weighted scores
        const totalWeight = Object.values(emotionWeights).reduce((a, b) => a + b, 0);
        const emotions = {};
        
        if (totalWeight > 0) {
            for (const emotion of Object.keys(emotionWeights)) {
                emotions[emotion] = emotionWeights[emotion] / totalWeight;
            }
        } else {
            // Fallback to neutral
            for (const emotion of Object.keys(emotionWeights)) {
                emotions[emotion] = 0.125;
            }
        }
        
        // Apply context adjustments (like original system)
        const adjustedEmotions = this.applyContextAdjustments(emotions, confidentWords, text);
        
        // Get dominant emotion
        const dominantEmotion = Object.keys(adjustedEmotions).reduce((a, b) => 
            adjustedEmotions[a] > adjustedEmotions[b] ? a : b
        );
        
        // Calculate aggregate VAD
        const vad = this.calculateAggregateVAD(confidentWords);
        
        // Calculate sentiment
        const sentiment = this.calculateSentiment(confidentWords);
        
        console.log(`🎯 Final emotion: ${dominantEmotion} (${(adjustedEmotions[dominantEmotion] * 100).toFixed(1)}%)`);
        console.log(`📊 All emotions:`, Object.fromEntries(
            Object.entries(adjustedEmotions).sort((a, b) => b[1] - a[1])
        ));
        
        return {
            overall_emotion: dominantEmotion,
            confidence: adjustedEmotions[dominantEmotion],
            emotions: adjustedEmotions,
            word_analysis: wordAnalyses,
            word_count: wordAnalyses.length,
            analyzed_words: confidentWords.length,
            coverage: confidentWords.length / wordAnalyses.length,
            vad: vad,
            sentiment: sentiment,
            processing_method: 'javascript_with_real_database'
        };
    }
    
    getDefaultEmotionProbs(emotion) {
        const defaultProbs = {
            joy: 0.125, trust: 0.125, anticipation: 0.125, surprise: 0.125,
            anger: 0.125, fear: 0.125, sadness: 0.125, disgust: 0.125
        };
        
        if (emotion && emotion !== 'neutral') {
            defaultProbs[emotion] = 0.8;
            const remaining = 0.2 / 7;
            for (const emo of Object.keys(defaultProbs)) {
                if (emo !== emotion) {
                    defaultProbs[emo] = remaining;
                }
            }
        }
        
        return defaultProbs;
    }
    
    applyContextAdjustments(emotions, confidentWords, text) {
        // Apply context patterns (like original system)
        const textLower = text.toLowerCase();
        const adjustedEmotions = { ...emotions };
        
        // Context patterns that boost specific emotions
        const contextPatterns = {
            anger: [['hate', 'angry', 'mad', 'furious'], ['damn', 'shit', 'stupid']],
            joy: [['love', 'happy', 'excited', 'amazing'], ['yes', 'awesome', 'fantastic']],
            sadness: [['sad', 'cry', 'tears', 'depressed'], ['sorry', 'disappointed']],
            fear: [['scared', 'afraid', 'worried', 'anxious'], ['danger', 'threat']],
            surprise: [['wow', 'omg', 'incredible', 'shocking'], ['sudden', 'unexpected']],
            disgust: [['gross', 'disgusting', 'nasty', 'awful'], ['sick', 'yuck']],
            trust: [['trust', 'reliable', 'honest', 'faithful'], ['sure', 'certain']],
            anticipation: [['excited', 'can\'t wait', 'looking forward'], ['hope', 'expect']]
        };
        
        // Apply pattern-based boosts
        for (const [emotion, patternGroups] of Object.entries(contextPatterns)) {
            let boostFactor = 0.0;
            
            for (const patterns of patternGroups) {
                const matches = patterns.filter(pattern => textLower.includes(pattern)).length;
                if (matches > 0) {
                    boostFactor += matches * 0.15;
                }
            }
            
            if (boostFactor > 0) {
                adjustedEmotions[emotion] = Math.min(adjustedEmotions[emotion] + boostFactor, 0.8);
                console.log(`🔥 Context boost for ${emotion}: +${boostFactor.toFixed(2)}`);
            }
        }
        
        // Normalize after adjustments
        const total = Object.values(adjustedEmotions).reduce((a, b) => a + b, 0);
        if (total > 0) {
            for (const emotion of Object.keys(adjustedEmotions)) {
                adjustedEmotions[emotion] = adjustedEmotions[emotion] / total;
            }
        }
        
        return adjustedEmotions;
    }
    
    calculateAggregateVAD(confidentWords) {
        if (confidentWords.length === 0) {
            return { valence: 0.5, arousal: 0.5, dominance: 0.5 };
        }
        
        const vad = { valence: 0, arousal: 0, dominance: 0 };
        
        for (const word of confidentWords) {
            vad.valence += word.valence || 0.5;
            vad.arousal += word.arousal || 0.5;
            vad.dominance += (word.dominance || 0.5);
        }
        
        return {
            valence: vad.valence / confidentWords.length,
            arousal: vad.arousal / confidentWords.length,
            dominance: vad.dominance / confidentWords.length
        };
    }
    
    calculateSentiment(confidentWords) {
        if (confidentWords.length === 0) {
            return { polarity: 'neutral', strength: 0.5 };
        }
        
        let positiveCount = 0;
        let negativeCount = 0;
        let strengthSum = 0;
        
        for (const word of confidentWords) {
            if (word.sentiment === 'positive') positiveCount++;
            else if (word.sentiment === 'negative') negativeCount++;
            
            strengthSum += word.confidence || 0.5;
        }
        
        let polarity = 'neutral';
        if (positiveCount > negativeCount) polarity = 'positive';
        else if (negativeCount > positiveCount) polarity = 'negative';
        
        return {
            polarity: polarity,
            strength: strengthSum / confidentWords.length
        };
    }
    
    getNeutralResult(wordAnalyses, text) {
        return {
            overall_emotion: 'neutral',
            confidence: 0.125,
            emotions: {
                joy: 0.125, trust: 0.125, anticipation: 0.125, surprise: 0.125,
                anger: 0.125, fear: 0.125, sadness: 0.125, disgust: 0.125
            },
            word_analysis: wordAnalyses,
            word_count: wordAnalyses.length,
            analyzed_words: 0,
            coverage: 0.0,
            vad: { valence: 0.5, arousal: 0.5, dominance: 0.5 },
            sentiment: { polarity: 'neutral', strength: 0.5 },
            processing_method: 'neutral_fallback'
        };
    }
    
    getDatabaseStats() {
        return {
            total_words: this.wordCache.size,
            deepseek_available: !!this.deepseekApiKey
        };
    }
}

// Global instance
const emotionEngine = new EmotionEngine();

module.exports = { emotionEngine };
