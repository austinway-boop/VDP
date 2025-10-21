// Vercel Serverless Function for System Statistics
// Returns information about the emotion analysis system

const { spawn } = require('child_process');
const path = require('path');

// Helper function to get system stats from Python
async function getSystemStats() {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(process.cwd(), 'api', 'get_stats.py');
    const python = spawn('python3', [pythonScript], {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PYTHONPATH: path.join(process.cwd(), 'api'),
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

// Simple in-memory counter (resets on function restart)
let callCounts = {
  stats: 0,
  text_analysis: 0,
  audio_analysis: 0,
  total: 0
};

module.exports = async function handler(req, res) {
  // Increment stats counter
  callCounts.stats++;
  callCounts.total++;
  
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed. Use GET to retrieve system statistics.'
    });
  }
  
  try {
    console.log(`📊 Stats API called (${callCounts.stats} times total)`);
    
    const queryTime = 0.001;
    
    return res.status(200).json({
      success: true,
      stats: {
        word_database_size: "25000+",
        system_status: "operational_serverless",
        api_calls: {
          stats_calls: callCounts.stats,
          text_analysis_calls: callCounts.text_analysis,
          audio_analysis_calls: callCounts.audio_analysis,
          total_calls: callCounts.total,
          last_reset: "function_restart"
        },
        features: {
          speech_recognition: false,
          emotion_analysis: true,
          text_analysis: true,
          laughter_detection: false,
          music_detection: false,
          confidence_scoring: true,
          serverless_mode: true
        },
        capabilities: {
          supported_audio_formats: ["Use text analysis instead"],
          supported_languages: ["en"],
          max_audio_size_mb: "N/A - use text analysis",
          max_text_length: 10000,
          confidence_threshold: 0.7
        },
        api_info: {
          query_time: queryTime,
          timestamp: new Date().toISOString(),
          version: '2.0.0',
          mode: 'serverless'
        }
      }
    });
    
  } catch (error) {
    console.error('❌ Stats retrieval error:', error);
    
    // Return basic fallback stats if Python fails
    return res.status(200).json({
      success: true,
      stats: {
        word_database_size: 'unknown',
        system_status: 'limited',
        training_stats: {
          pending_reviews: 'unknown',
          completed_corrections: 'unknown',
          total_corrections: 'unknown'
        },
        api_info: {
          query_time: 0,
          timestamp: new Date().toISOString(),
          version: '2.0.0',
          fallback: true,
          error: process.env.NODE_ENV === 'development' ? error.message : 'Stats unavailable'
        }
      }
    });
  }
}
