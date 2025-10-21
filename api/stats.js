// Vercel Serverless Function for System Statistics
// Returns information about the emotion analysis system

import { spawn } from 'child_process';
import path from 'path';

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

export default async function handler(req, res) {
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
    console.log('📊 Retrieving system statistics...');
    
    const startTime = Date.now();
    const stats = await getSystemStats();
    const queryTime = (Date.now() - startTime) / 1000;
    
    console.log(`✅ Statistics retrieved in ${queryTime.toFixed(2)}s`);
    console.log(`📚 Word database size: ${stats.word_database_size || 0} words`);
    
    return res.status(200).json({
      success: true,
      stats: {
        ...stats,
        api_info: {
          query_time: queryTime,
          timestamp: new Date().toISOString(),
          version: '2.0.0'
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
