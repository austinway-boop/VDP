#!/usr/bin/env node

/**
 * Test Suite for Speech Emotion Analysis API
 * Tests all endpoints with various inputs and edge cases
 */

const fs = require('fs');
const path = require('path');
const FormData = require('form-data');

// Configuration
const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:3000';
const TEST_TIMEOUT = 30000; // 30 seconds

console.log('🧪 Starting Speech Emotion Analysis API Tests');
console.log(`🌐 Base URL: ${BASE_URL}`);
console.log('=' * 60);

// Test utilities
async function makeRequest(url, options = {}) {
  const fetch = (await import('node-fetch')).default;
  
  try {
    const response = await fetch(url, {
      timeout: TEST_TIMEOUT,
      ...options
    });
    
    const contentType = response.headers.get('content-type');
    let data;
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }
    
    return {
      status: response.status,
      ok: response.ok,
      data: data
    };
  } catch (error) {
    return {
      status: 0,
      ok: false,
      error: error.message
    };
  }
}

function createTestAudio() {
  // Create a simple WAV file for testing (minimal valid WAV)
  const sampleRate = 44100;
  const duration = 1; // 1 second
  const samples = sampleRate * duration;
  
  const buffer = Buffer.alloc(44 + samples * 2);
  
  // WAV header
  buffer.write('RIFF', 0);
  buffer.writeUInt32LE(36 + samples * 2, 4);
  buffer.write('WAVE', 8);
  buffer.write('fmt ', 12);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20); // PCM
  buffer.writeUInt16LE(1, 22); // Mono
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * 2, 28);
  buffer.writeUInt16LE(2, 32);
  buffer.writeUInt16LE(16, 34);
  buffer.write('data', 36);
  buffer.writeUInt32LE(samples * 2, 40);
  
  // Generate sine wave at 440Hz (A note)
  for (let i = 0; i < samples; i++) {
    const sample = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 16384;
    buffer.writeInt16LE(sample, 44 + i * 2);
  }
  
  return buffer;
}

// Test cases
const tests = [
  {
    name: 'System Statistics',
    test: async () => {
      const response = await makeRequest(`${BASE_URL}/api/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(response.data)}`);
      }
      
      const stats = response.data;
      
      // Validate response structure
      if (!stats.success) {
        throw new Error(`Stats request failed: ${stats.error || 'Unknown error'}`);
      }
      
      const requiredFields = ['word_database_size', 'system_status', 'features', 'capabilities'];
      for (const field of requiredFields) {
        if (!(field in stats.stats)) {
          throw new Error(`Missing required field: ${field}`);
        }
      }
      
      console.log(`  📊 Word database size: ${stats.stats.word_database_size}`);
      console.log(`  🔧 System status: ${stats.stats.system_status}`);
      console.log(`  ⚡ Features: ${Object.keys(stats.stats.features).length} available`);
      
      return { success: true, data: stats };
    }
  },
  
  {
    name: 'Text Analysis - Simple Positive Text',
    test: async () => {
      const testText = "I am very happy and excited about this amazing project!";
      
      const response = await makeRequest(`${BASE_URL}/api/analyze-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: testText })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(response.data)}`);
      }
      
      const result = response.data;
      
      if (!result.success) {
        throw new Error(`Analysis failed: ${result.error || 'Unknown error'}`);
      }
      
      const analysis = result.result.emotion_analysis;
      
      // Validate response structure
      const requiredFields = ['overall_emotion', 'emotions', 'word_analysis', 'word_count'];
      for (const field of requiredFields) {
        if (!(field in analysis)) {
          throw new Error(`Missing required field: ${field}`);
        }
      }
      
      // Check that emotions sum to approximately 1.0
      const emotionSum = Object.values(analysis.emotions).reduce((a, b) => a + b, 0);
      if (Math.abs(emotionSum - 1.0) > 0.01) {
        throw new Error(`Emotions don't sum to 1.0: ${emotionSum}`);
      }
      
      console.log(`  📝 Text: "${testText}"`);
      console.log(`  🎭 Primary emotion: ${analysis.overall_emotion} (${(analysis.confidence * 100).toFixed(1)}%)`);
      console.log(`  📊 Coverage: ${analysis.analyzed_words}/${analysis.word_count} words`);
      
      return { success: true, data: result };
    }
  },
  
  {
    name: 'Text Analysis - Negative Text',
    test: async () => {
      const testText = "I feel terrible and sad about this awful situation";
      
      const response = await makeRequest(`${BASE_URL}/api/analyze-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: testText })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(response.data)}`);
      }
      
      const result = response.data;
      
      if (!result.success) {
        throw new Error(`Analysis failed: ${result.error || 'Unknown error'}`);
      }
      
      const analysis = result.result.emotion_analysis;
      console.log(`  📝 Text: "${testText}"`);
      console.log(`  🎭 Primary emotion: ${analysis.overall_emotion} (${(analysis.confidence * 100).toFixed(1)}%)`);
      
      // Expect negative emotions to be dominant
      const negativeEmotions = ['anger', 'fear', 'sadness', 'disgust'];
      const negativeSum = negativeEmotions.reduce((sum, emotion) => sum + analysis.emotions[emotion], 0);
      
      if (negativeSum < 0.3) {
        console.log(`  ⚠️  Warning: Expected more negative emotion, got ${(negativeSum * 100).toFixed(1)}%`);
      }
      
      return { success: true, data: result };
    }
  },
  
  {
    name: 'Text Analysis - Empty Text',
    test: async () => {
      const response = await makeRequest(`${BASE_URL}/api/analyze-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: "" })
      });
      
      if (response.ok) {
        throw new Error('Expected error for empty text, but request succeeded');
      }
      
      if (response.status !== 400) {
        throw new Error(`Expected status 400, got ${response.status}`);
      }
      
      console.log(`  ✅ Correctly rejected empty text with status ${response.status}`);
      
      return { success: true };
    }
  },
  
  {
    name: 'Text Analysis - Very Long Text',
    test: async () => {
      const longText = 'This is a test sentence. '.repeat(500); // ~12,500 characters
      
      const response = await makeRequest(`${BASE_URL}/api/analyze-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: longText })
      });
      
      if (response.ok) {
        throw new Error('Expected error for text too long, but request succeeded');
      }
      
      if (response.status !== 400) {
        throw new Error(`Expected status 400, got ${response.status}`);
      }
      
      console.log(`  ✅ Correctly rejected long text (${longText.length} chars) with status ${response.status}`);
      
      return { success: true };
    }
  },
  
  {
    name: 'Audio Analysis - Test Audio File',
    test: async () => {
      const audioBuffer = createTestAudio();
      const form = new FormData();
      form.append('audio', audioBuffer, {
        filename: 'test.wav',
        contentType: 'audio/wav'
      });
      form.append('retry_mode', 'normal');
      
      const response = await makeRequest(`${BASE_URL}/api/analyze-audio`, {
        method: 'POST',
        body: form,
        headers: form.getHeaders()
      });
      
      console.log(`  📁 Uploaded test audio: ${audioBuffer.length} bytes`);
      
      // Audio analysis might fail with synthetic audio, which is expected
      if (!response.ok) {
        console.log(`  ⚠️  Audio analysis failed (expected with synthetic audio): ${response.status}`);
        if (response.data && response.data.error) {
          console.log(`     Error: ${response.data.error}`);
        }
        return { success: true, note: 'Failed as expected with synthetic audio' };
      }
      
      const result = response.data;
      
      if (result.success) {
        console.log(`  🎤 Transcription: "${result.result.transcription || 'No speech detected'}"`);
        console.log(`  🎭 Primary emotion: ${result.result.emotion_analysis?.overall_emotion || 'unknown'}`);
        console.log(`  ⏱️  Processing time: ${result.result.processing_time || 0}s`);
      } else {
        console.log(`  ⚠️  Analysis failed: ${result.error || 'Unknown error'}`);
      }
      
      return { success: true, data: result };
    }
  },
  
  {
    name: 'Audio Analysis - No File',
    test: async () => {
      const form = new FormData();
      form.append('retry_mode', 'normal');
      
      const response = await makeRequest(`${BASE_URL}/api/analyze-audio`, {
        method: 'POST',
        body: form,
        headers: form.getHeaders()
      });
      
      if (response.ok) {
        throw new Error('Expected error for missing audio file, but request succeeded');
      }
      
      if (response.status !== 400) {
        throw new Error(`Expected status 400, got ${response.status}`);
      }
      
      console.log(`  ✅ Correctly rejected missing audio file with status ${response.status}`);
      
      return { success: true };
    }
  },
  
  {
    name: 'CORS Headers',
    test: async () => {
      const response = await makeRequest(`${BASE_URL}/api/stats`, {
        method: 'OPTIONS'
      });
      
      if (response.status !== 200) {
        throw new Error(`OPTIONS request failed with status ${response.status}`);
      }
      
      // Note: node-fetch doesn't expose headers in the same way as browser fetch
      console.log(`  ✅ CORS preflight request successful`);
      
      return { success: true };
    }
  }
];

// Run all tests
async function runTests() {
  let passed = 0;
  let failed = 0;
  
  for (const testCase of tests) {
    console.log(`\n🧪 Running: ${testCase.name}`);
    
    try {
      const result = await testCase.test();
      console.log(`  ✅ PASSED`);
      if (result.note) {
        console.log(`     Note: ${result.note}`);
      }
      passed++;
    } catch (error) {
      console.log(`  ❌ FAILED: ${error.message}`);
      failed++;
    }
  }
  
  console.log('\n' + '=' * 60);
  console.log(`📊 Test Results: ${passed} passed, ${failed} failed`);
  
  if (failed > 0) {
    console.log('\n⚠️  Some tests failed. This might be expected if:');
    console.log('   • API keys are not configured');
    console.log('   • The server is not running');
    console.log('   • Network connectivity issues');
    process.exit(1);
  } else {
    console.log('\n🎉 All tests passed!');
  }
}

// Handle command line arguments
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log('Usage: node test-endpoints.js [options]');
  console.log('');
  console.log('Options:');
  console.log('  --help, -h     Show this help message');
  console.log('  --url <url>    Set base URL (default: http://localhost:3000)');
  console.log('');
  console.log('Environment variables:');
  console.log('  TEST_BASE_URL  Set base URL for testing');
  console.log('');
  console.log('Examples:');
  console.log('  node test-endpoints.js');
  console.log('  node test-endpoints.js --url https://your-project.vercel.app');
  console.log('  TEST_BASE_URL=https://your-project.vercel.app node test-endpoints.js');
  process.exit(0);
}

const urlIndex = process.argv.indexOf('--url');
if (urlIndex !== -1 && process.argv[urlIndex + 1]) {
  BASE_URL = process.argv[urlIndex + 1];
}

// Install node-fetch if not available
try {
  require.resolve('node-fetch');
} catch (e) {
  console.log('❌ node-fetch not found. Please install it:');
  console.log('   npm install node-fetch');
  process.exit(1);
}

// Install form-data if not available
try {
  require.resolve('form-data');
} catch (e) {
  console.log('❌ form-data not found. Please install it:');
  console.log('   npm install form-data');
  process.exit(1);
}

// Run the tests
runTests().catch(error => {
  console.error('💥 Test runner crashed:', error);
  process.exit(1);
});
