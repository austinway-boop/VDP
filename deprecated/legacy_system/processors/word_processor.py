#!/usr/bin/env python3
"""
Word Emotion Processor using DeepSeek API
Processes dictionary words through DeepSeek API for emotion analysis with parallel processing
"""

import json
import os
import time
import random
import requests
import threading
import concurrent.futures
from typing import Dict, List, Optional
from pathlib import Path

class WordEmotionProcessor:
    def __init__(self, words_file: str = "VoiceRelatedEmotionPrediction/WordEmotionPrediction/words.json", max_workers: int = 1000):
        self.words_file = words_file
        self.max_workers = max_workers
        # DeepSeek API configuration
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = "your-api-key-here"
        self.model = "deepseek-chat"  # DeepSeek V3.2 model
        
        # Create output directory
        self.output_dir = Path("words")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load words and processed words
        self.words = self.load_words()
        self.processed_words = self.load_processed_words()
        
        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 100
        
        # Processing stats - load from session file
        self.current_words = []
        self.session_processed = 0  # Will be loaded from session data
        
        # Performance tracking
        self.processing_times = []
        self.session_start_time = time.time()
        self.session_file = "current_session.json"
        self.session_data = self.load_session_data()
        self.current_words_file = "current_processing.json"
        
        # Computer performance monitoring
        self.start_system_monitoring()
        
    def load_words(self) -> List[str]:
        """Load words from JSON file"""
        try:
            with open(self.words_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('words', [])
        except Exception as e:
            print(f"Error loading words: {e}")
            return []
    
    def load_processed_words(self) -> set:
        """Load already processed words from existing files"""
        processed = set()
        for file_path in self.output_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data.get('words', []):
                        processed.add(entry.get('word', ''))
            except Exception as e:
                print(f"Error loading processed words from {file_path}: {e}")
        return processed
    
    def load_session_data(self) -> Dict:
        """Load current session data"""
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Restore session state
                self.session_processed = data.get('session_processed', 0)
                self.session_start_time = data.get('session_start_time', time.time())
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'session_processed': 0,
                'session_start_time': time.time(),
                'words_this_session': [],
                'avg_processing_time': 0,
                'total_session_time': 0
            }
    
    def save_session_data(self):
        """Save current session data"""
        try:
            self.session_data.update({
                'session_processed': self.session_processed,
                'session_start_time': self.session_start_time,
                'avg_processing_time': sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0,
                'total_session_time': time.time() - self.session_start_time,
                'last_updated': time.time()
            })
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            print(f"Error saving session data: {e}")
    
    def start_system_monitoring(self):
        """Start monitoring computer performance"""
        try:
            import psutil
            self.has_psutil = True
        except ImportError:
            self.has_psutil = False
            print("⚠️ Install psutil for system monitoring: pip install psutil")
    
    def get_system_performance(self) -> Dict:
        """Get current system performance metrics"""
        if not self.has_psutil:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'available_memory_gb': 0,
                'disk_usage_percent': 0
            }
        
        try:
            import psutil
            
            # Get system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'available_memory_gb': memory.available / (1024**3),
                'disk_usage_percent': disk.percent,
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            print(f"Error getting system performance: {e}")
            return {}
    
    def save_current_words(self):
        """Save currently processing words to shared file"""
        try:
            data = {
                'current_words': self.current_words,
                'timestamp': time.time()
            }
            with open(self.current_words_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving current words: {e}")
    
    def load_current_words(self):
        """Load currently processing words from shared file"""
        try:
            with open(self.current_words_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Only use if recent (within last 2 minutes)
                if time.time() - data.get('timestamp', 0) < 120:
                    return data.get('current_words', [])
                else:
                    return []
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_remaining_words(self) -> List[str]:
        """Get list of words that haven't been processed yet"""
        return [word for word in self.words if word not in self.processed_words]
    
    def get_file_for_word(self, word: str) -> str:
        """Determine which file a word should be saved to based on first character"""
        if not word:
            return "empty.json"
        
        first_char = word[0].lower()
        if first_char.isalpha():
            return f"{first_char}.json"
        elif first_char.isdigit():
            return "numbers.json"
        else:
            return "symbols.json"
    
    def make_ai_request(self, word: str) -> Optional[Dict]:
        """Make request to DeepSeek API for word emotion analysis"""
        
        prompt = f"""Analyze the word "{word}" for emotion. Return ONLY valid JSON in this exact format:

{{
  "word": "{word}",
  "stats": {{
    "pos": ["noun"],
    "vad": {{"valence": 0.50, "arousal": 0.50, "dominance": 0.50}},
    "emotion_probs": {{
      "joy": 0.125, "trust": 0.125, "anticipation": 0.125, "surprise": 0.125,
      "anger": 0.125, "fear": 0.125, "sadness": 0.125, "disgust": 0.125
    }},
    "sentiment": {{"polarity": "neutral", "strength": 0.50}},
    "social_axes": {{"good_bad": 0.00, "warmth_cold": 0.00, "competence_incompetence": 0.00, "active_passive": 0.00}},
    "toxicity": 0.00,
    "dynamics": {{"negation_flip_probability": 0.00, "sarcasm_flip_probability": 0.00}}
  }}
}}

Rules: emotion_probs must sum to 1.00, values 0-1 except social_axes (-1 to 1). Return ONLY the JSON, no explanation."""

        start_time = time.time()
        
        # Show detailed AI request info
        print(f"🚀 Sending to DeepSeek: {self.model}")
        print(f"📝 Prompt length: {len(prompt)} characters")
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 500,
                'stream': False
            }
            
            response = requests.post(self.deepseek_url, 
                                   json=payload,
                                   headers=headers,
                                   timeout=30)  # 30 second timeout
            
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            print(f"⏱️  AI Response time: {processing_time:.1f}s")
            
            # Keep only last 100 times for average calculation
            if len(self.processing_times) > 100:
                self.processing_times = self.processing_times[-100:]
            
            if response.status_code == 200:
                result_data = response.json()
                
                # DeepSeek API response format
                if 'choices' in result_data and len(result_data['choices']) > 0:
                    response_text = result_data['choices'][0]['message']['content'].strip()
                    
                    print(f"📤 DeepSeek Response length: {len(response_text)} characters")
                    
                    # Extract JSON from response
                    if '{' in response_text and '}' in response_text:
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        json_text = response_text[json_start:json_end]
                        
                        print(f"🔍 Extracting JSON from response...")
                        print(f"📋 JSON preview: {json_text[:100]}...")
                        
                        try:
                            result = json.loads(json_text)
                            result['word'] = word  # Ensure word matches
                            print(f"✅ JSON parsed successfully!")
                            return result
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON parsing failed: {e}")
                            print(f"🔍 Raw JSON: {json_text[:200]}...")
                            return None
                    else:
                        print(f"❌ No JSON found in DeepSeek response")
                        print(f"🔍 Response preview: {response_text[:200]}...")
                        return None
                else:
                    print(f"❌ Invalid DeepSeek response format")
                    return None
                        
            else:
                print(f"DeepSeek API request failed for word '{word}': {response.status_code}")
                if response.text:
                    print(f"Error details: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ CRITICAL ERROR processing word '{word}': {e}")
            print("🛑 NO FALLBACK - This word FAILED and will not be processed")
            return None
    
    def process_batch_words(self, count: int = 1000, max_concurrent: int = 100) -> int:
        """Process a specific number of words with EXTREME parallel processing"""
        remaining = self.get_remaining_words()
        if not remaining:
            print("🎉 No more words to process!")
            return 0
        
        words_to_process = min(count, len(remaining))
        words_batch = remaining[:words_to_process]
        
        # Dynamic concurrency based on batch size - ULTRA SPEED
        optimal_concurrent = min(self.max_workers, words_to_process, self.max_workers)  # Use max_workers setting
        
        print(f"🚀 Processing {words_to_process} words with ULTRA PARALLEL DeepSeek API requests...")
        print(f"⚡ Using {optimal_concurrent} concurrent threads for INSANE SPEED!")
        print(f"🔥 This could be up to {optimal_concurrent}x faster than single processing!")
        print(f"📊 Starting batch - {words_to_process} words remaining to process")
        
        processed = 0
        failed = 0
        start_time = time.time()
        
        # Thread-safe lock for file operations
        self.save_lock = threading.Lock()
        
        # Process words in parallel batches - ULTRA SPEED
        batch_size = optimal_concurrent  # Use maximum concurrency per batch
        
        for batch_start in range(0, words_to_process, batch_size):
            batch_end = min(batch_start + batch_size, words_to_process)
            current_batch = words_batch[batch_start:batch_end]
            
            batch_num = batch_start//batch_size + 1
            total_batches = (words_to_process + batch_size - 1) // batch_size
            words_left_in_1000 = words_to_process - batch_start
            print(f"🔄 Batch {batch_num}/{total_batches}: processing words {batch_start+1}-{batch_end}")
            print(f"📋 Remaining in this 1000: {words_left_in_1000} words")
            
            # Process this batch in parallel - EXTREME CONCURRENCY
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all words in this batch
                future_to_word = {
                    executor.submit(self.process_word_parallel, word): word 
                    for word in current_batch
                }
                
                # Collect results as they complete with progress tracking
                completed_in_batch = 0
                for future in concurrent.futures.as_completed(future_to_word):
                    word = future_to_word[future]
                    completed_in_batch += 1
                    try:
                        success = future.result()
                        if success:
                            processed += 1
                            print(f"✅ {word} completed ({completed_in_batch}/{len(current_batch)} in this batch)")
                        else:
                            failed += 1
                            print(f"❌ {word} failed ({completed_in_batch}/{len(current_batch)} in this batch)")
                    except Exception as e:
                        failed += 1
                        print(f"❌ {word} error: {e} ({completed_in_batch}/{len(current_batch)} in this batch)")
            
            # Progress update after each batch
            elapsed = time.time() - start_time
            rate = processed / (elapsed / 3600) if elapsed > 0 else 0
            remaining_count = len(self.get_remaining_words())
            
            batch_remaining = words_to_process - processed - failed
            print(f"📊 Batch Progress: {processed}/{words_to_process} processed | {failed} failed | {batch_remaining} remaining in batch")
            print(f"⚡ Current rate: {rate:.1f} words/hour")
            print(f"📈 Total remaining: {remaining_count} words")
            
            # Minimal delay between batches for maximum speed
            time.sleep(0.1)
        
        total_time = time.time() - start_time
        final_rate = processed / (total_time / 3600) if total_time > 0 else 0
        
        print(f"🎉 PARALLEL BATCH COMPLETED!")
        print(f"✅ Processed: {processed}/{words_to_process} words")
        print(f"❌ Failed: {failed} words")
        print(f"⏱️ Total time: {self.format_time(total_time)}")
        print(f"🚀 Final rate: {final_rate:.1f} words/hour")
        print(f"⚡ Speed improvement: ~{optimal_concurrent}x faster with ULTRA parallel processing!")
        
        return processed
    
    def process_word_parallel(self, word: str) -> bool:
        """Process a single word in parallel - thread-safe version with better error handling"""
        try:
            # Make AI request (this is the slow part we're parallelizing)
            result = self.make_ai_request(word)
            
            if result:
                # Thread-safe saving with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with self.save_lock:
                            self.save_word_result(result)
                            self.remove_word_from_source(word)
                            self.session_processed += 1
                            
                            # Update current words list safely
                            if word in self.current_words:
                                self.current_words.remove(word)
                            self.save_current_words()
                        
                        return True
                    except Exception as save_error:
                        if attempt < max_retries - 1:
                            time.sleep(0.1 * (attempt + 1))  # Progressive delay
                            continue
                        else:
                            print(f"❌ Failed to save '{word}' after {max_retries} attempts: {save_error}")
                            return False
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error processing '{word}' in parallel: {e}")
            return False
    
    def save_word_result(self, word_data: Dict):
        """Save word analysis result to appropriate file and remove from words.json"""
        word = word_data.get('word', '')
        filename = self.get_file_for_word(word)
        filepath = self.output_dir / filename
        
        # Load existing data or create new
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                "file_character": filename.replace('.json', ''),
                "word_count": 0,
                "words": []
            }
        
        # Add new word data
        data['words'].append(word_data)
        data['word_count'] = len(data['words'])
        data['words'].sort(key=lambda x: x.get('word', '').lower())
        
        # Save back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Remove word from words.json
        self.remove_word_from_source(word)
        print(f"Saved '{word}' to {filename}")
    
    def remove_word_from_source(self, processed_word: str):
        """Remove processed word from words.json"""
        try:
            with open(self.words_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if processed_word in data['words']:
                data['words'].remove(processed_word)
                data['total_words'] = len(data['words'])
                
                with open(self.words_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                if processed_word in self.words:
                    self.words.remove(processed_word)
                    
        except Exception as e:
            print(f"Error removing word '{processed_word}' from source: {e}")
    
    def process_single_word(self) -> bool:
        """Process a single word. Returns True if successful, False if failed"""
        remaining = self.get_remaining_words()
        
        if not remaining:
            print("🎉 No more words to process! All words completed!")
            return False
        
        word = remaining[0]
        self.current_words.append(word)
        self.save_current_words()  # Save for real-time display
        
        # Enhanced feedback - show detailed progress
        print(f"\n{'='*60}")
        print(f"🔄 PROCESSING: '{word}'")
        print(f"📊 Progress: {len(remaining)} remaining | {self.session_processed} processed this session")
        print(f"⏱️  Starting AI analysis...")
        
        start_time = time.time()
        result = self.make_ai_request(word)
        processing_time = time.time() - start_time
        
        if word in self.current_words:
            self.current_words.remove(word)
            self.save_current_words()  # Update shared file
        
        if result:
            # Success feedback
            print(f"✅ SUCCESS: Processed '{word}' in {processing_time:.1f}s")
            print(f"📁 Saved to: {self.get_file_for_word(word)}")
            
            # Show AI analysis preview
            if 'stats' in result:
                stats = result['stats']
                if 'sentiment' in stats:
                    sentiment = stats['sentiment']
                    print(f"🎯 Analysis: {sentiment.get('polarity', 'unknown')} sentiment")
                if 'vad' in stats:
                    vad = stats['vad']
                    print(f"📈 VAD: valence={vad.get('valence', 0):.2f}, arousal={vad.get('arousal', 0):.2f}")
            
            self.save_word_result(result)
            self.processed_words.add(word)
            self.session_processed += 1
            self.consecutive_errors = 0
            
            # Add word to session tracking
            if 'words_this_session' not in self.session_data:
                self.session_data['words_this_session'] = []
            self.session_data['words_this_session'].append({
                'word': word,
                'processing_time': processing_time,
                'timestamp': time.time()
            })
            
            # Save session data
            self.save_session_data()
            
            # Calculate and show speed stats
            if len(self.processing_times) > 1:
                avg_time = sum(self.processing_times[-10:]) / min(10, len(self.processing_times))
                words_per_hour = 3600 / avg_time if avg_time > 0 else 0
                remaining_hours = len(remaining) * avg_time / 3600
                print(f"⚡ Speed: {words_per_hour:.1f} words/hour | ETA: {self.format_time(remaining_hours * 3600)}")
            
            print(f"📊 Session: {self.session_processed} words processed")
            print(f"{'='*60}")
            return True
        else:
            # Failure feedback
            self.consecutive_errors += 1
            print(f"❌ FAILED: '{word}' after {processing_time:.1f}s")
            print(f"🔄 Consecutive errors: {self.consecutive_errors}")
            print(f"{'='*60}")
            return False
    
    def get_stats(self) -> Dict:
        """Get processing statistics with speed and completion estimates"""
        remaining = self.get_remaining_words()
        
        # Calculate processed words from original total minus current remaining
        try:
            with open(self.words_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                current_total = len(current_data.get('words', []))
        except:
            current_total = len(self.words)
        
        original_total = 147323
        processed_count = original_total - current_total
        
        # Calculate processing speed and estimates with real-time data
        if self.processing_times:
            # Use recent processing times for more accurate estimates
            recent_times = self.processing_times[-20:] if len(self.processing_times) >= 20 else self.processing_times
            avg_processing_time = sum(recent_times) / len(recent_times)
            
            # Calculate different time estimates
            recent_avg = sum(self.processing_times[-5:]) / min(5, len(self.processing_times)) if self.processing_times else avg_processing_time
            overall_avg = sum(self.processing_times) / len(self.processing_times)
        else:
            avg_processing_time = 45.0  # Realistic default based on testing
            recent_avg = avg_processing_time
            overall_avg = avg_processing_time
        
        # Real-time completion estimates
        remaining_time_seconds_recent = current_total * recent_avg  # Based on last 5 words
        remaining_time_seconds_overall = current_total * overall_avg  # Based on all processing
        
        # Calculate current session speed (words per hour) - REAL TIME
        session_duration = time.time() - self.session_start_time
        if session_duration > 0 and self.session_processed > 0:
            session_speed = (self.session_processed / (session_duration / 3600))
            # Calculate instantaneous speed from recent processing
            if len(self.processing_times) >= 3:
                instant_speed = 3600 / recent_avg  # Words per hour based on recent performance
            else:
                instant_speed = session_speed
        else:
            # No current session data, use historical averages for meaningful predictions
            session_speed = 0
            if recent_avg > 0:
                # Use recent average processing time to calculate potential speed
                instant_speed = 3600 / recent_avg  # Words per hour based on historical performance
            else:
                instant_speed = 0
        
        # Get system performance
        system_perf = self.get_system_performance()
        
        # Load current words from shared file for real-time display
        current_words_live = self.load_current_words()
        
        return {
            "total_words": original_total,
            "processed_words": processed_count,
            "remaining_words": current_total,
            "session_processed": self.session_processed,
            "consecutive_errors": self.consecutive_errors,
            "completion_percentage": (processed_count / original_total) * 100 if original_total > 0 else 0,
            "current_words": current_words_live,
            "performance": {
                "avg_processing_time": avg_processing_time,
                "recent_avg_time": recent_avg,
                "overall_avg_time": overall_avg,
                "estimated_completion_time": remaining_time_seconds_recent,  # Use recent performance
                "estimated_completion_time_overall": remaining_time_seconds_overall,  # Conservative estimate
                "session_speed_wph": session_speed,  # words per hour (session average)
                "instant_speed_wph": instant_speed,  # words per hour (recent performance)
                "total_processing_time": session_duration,
                "session_duration_hours": session_duration / 3600,
                "words_processed_this_session": self.session_processed,
                "processing_times_count": len(self.processing_times),
                "eta_formatted": self.format_time(remaining_time_seconds_recent),
                "eta_conservative": self.format_time(remaining_time_seconds_overall)
            },
            "system_performance": system_perf,
            "session_data": {
                "start_time": self.session_start_time,
                "duration": session_duration,
                "words_completed": self.session_processed,
                "current_session_speed": session_speed,
                "recent_words": [w.get('word', '') for w in self.session_data.get('words_this_session', [])[-5:]]
            }
        }
    
    def print_stats(self):
        """Print current processing statistics"""
        stats = self.get_stats()
        perf = stats['performance']
        
        print("\n" + "="*50)
        print("WORD EMOTION ANALYSIS STATS")
        print("="*50)
        print(f"Total Words: {stats['total_words']:,}")
        print(f"Processed: {stats['processed_words']:,}")
        print(f"Remaining: {stats['remaining_words']:,}")
        print(f"Session Processed: {stats['session_processed']:,}")
        print(f"Completion: {stats['completion_percentage']:.2f}%")
        print(f"Consecutive Errors: {stats['consecutive_errors']}")
        
        if stats['current_words']:
            print(f"Currently Processing: {', '.join(stats['current_words'])}")
        
        print(f"\n--- SPEED & ESTIMATES ---")
        print(f"Avg Time per Word: {perf['avg_processing_time']:.1f}s")
        print(f"Session Speed: {perf['session_speed_wph']:.1f} words/hour")
        print(f"Est. Completion Time: {self.format_time(perf['estimated_completion_time'])}")
        print("="*50)
    
    def format_time(self, seconds):
        """Format seconds into human readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days}d {hours}h"
    
    def process_all_with_regulation(self):
        """Process all remaining words with intelligent resource regulation"""
        remaining = self.get_remaining_words()
        total_to_process = len(remaining)
        processed_in_batch = 0
        batch_start_time = time.time()
        
        print(f"🛡️ Starting regulated processing of {total_to_process} words...")
        
        while remaining and self.consecutive_errors < self.max_consecutive_errors:
            # Check system resources every 10 words
            if processed_in_batch % 10 == 0:
                sys_perf = self.get_system_performance()
                sleep_time = self.calculate_adaptive_delay(sys_perf, processed_in_batch)
                
                if sleep_time > 0.5:
                    print(f"⚠️ High resource usage detected - throttling processing...")
                    print(f"   CPU: {sys_perf.get('cpu_percent', 0):.1f}%, Memory: {sys_perf.get('memory_percent', 0):.1f}%")
                    print(f"   Applying {sleep_time:.1f}s delay between words")
            
            # Process single word
            success = self.process_single_word()
            
            if success:
                processed_in_batch += 1
                
                # Show progress every 25 words
                if processed_in_batch % 25 == 0:
                    elapsed = time.time() - batch_start_time
                    rate = processed_in_batch / (elapsed / 3600) if elapsed > 0 else 0
                    remaining_count = len(self.get_remaining_words())
                    
                    print(f"📊 Batch Progress: {processed_in_batch}/{total_to_process} words")
                    print(f"⚡ Current rate: {rate:.1f} words/hour")
                    print(f"📈 Remaining: {remaining_count} words")
                    print(f"⏱️ Batch time: {self.format_time(elapsed)}")
            
            # Apply adaptive delay
            time.sleep(sleep_time if 'sleep_time' in locals() else 0.1)
            remaining = self.get_remaining_words()
            
            # Emergency brake for excessive errors
            if self.consecutive_errors >= 20:
                print(f"🛑 Emergency stop: Too many consecutive errors ({self.consecutive_errors})")
                break
        
        total_time = time.time() - batch_start_time
        print(f"✅ Batch completed: {processed_in_batch} words in {self.format_time(total_time)}")
        if processed_in_batch > 0:
            final_rate = processed_in_batch / (total_time / 3600) if total_time > 0 else 0
            print(f"📈 Final rate: {final_rate:.1f} words/hour")
    
    def calculate_adaptive_delay(self, sys_perf, words_processed):
        """Calculate adaptive delay based on system performance"""
        base_delay = 0.1  # Minimal delay for speed
        
        cpu = sys_perf.get('cpu_percent', 0)
        memory = sys_perf.get('memory_percent', 0)
        
        # Increase delay based on resource usage
        delay_multiplier = 1.0
        
        if cpu >= 90 or memory >= 95:
            delay_multiplier = 4.0  # Critical: 2s delay
            print(f"🚨 Critical resource usage - maximum throttling")
        elif cpu >= 75 or memory >= 80:
            delay_multiplier = 2.5  # High: 1.25s delay
        elif cpu >= 60 or memory >= 70:
            delay_multiplier = 1.5  # Medium: 0.75s delay
        
        # Factor in consecutive errors
        if self.consecutive_errors > 10:
            delay_multiplier *= 1.5
        elif self.consecutive_errors > 5:
            delay_multiplier *= 1.2
        
        # Reduce delay as we process more words successfully (learning effect)
        if words_processed > 100 and self.consecutive_errors < 3:
            delay_multiplier *= 0.8
        
        return base_delay * delay_multiplier

def main():
    """Main function for command line usage"""
    import sys
    
    processor = WordEmotionProcessor(max_workers=1000)
    
    print("🔥 ULTRA FAST MODE: 1000 CONCURRENT WORKERS ENABLED!")
    print("⚡ This will process words at MAXIMUM SPEED!")
    
    # Show system info at startup
    sys_perf = processor.get_system_performance()
    print(f"💻 System Status: CPU {sys_perf.get('cpu_percent', 0):.1f}%, Memory {sys_perf.get('memory_percent', 0):.1f}%")
    
    if len(sys.argv) < 2:
        print("Word Emotion Processor with DeepSeek API")
        print("Usage:")
        print("  python word_processor.py single    - Process one word")
        print("  python word_processor.py batch     - Process continuously")
        print("  python word_processor.py all       - Process all remaining")
        print("  python word_processor.py 1000      - Process 1000 words (100 concurrent)")
        print("  python word_processor.py extreme   - Process 1000 words (1000 concurrent!)")
        print("  python word_processor.py stats     - Show statistics")
        return
    
    command = sys.argv[1].lower()
    
    if command == "single":
        processor.process_single_word()
        processor.print_stats()
        
    elif command == "batch":
        try:
            print("Starting continuous processing...")
            while processor.get_remaining_words():
                if processor.consecutive_errors >= processor.max_consecutive_errors:
                    break
                processor.process_single_word()
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nProcessing stopped by user")
        
        processor.print_stats()
        
    elif command == "all":
        remaining = processor.get_remaining_words()
        if remaining:
            print(f"🔥 ULTRA FAST MODE: Processing {len(remaining)} remaining words with {processor.max_workers} concurrent workers!")
            processor.process_parallel_batch(len(remaining))
        
        processor.print_stats()
        
    elif command == "500":
        # Process 500 words with optimized concurrency
        try:
            print("🚀 Processing 500 words with optimized parallel processing...")
            processed = processor.process_batch_words(500, max_concurrent=50)
            print(f"✅ Successfully processed {processed} words!")
        except Exception as e:
            print(f"⚠️ Error processing 500 words: {e}")
        
        processor.print_stats()
        
    elif command == "1000":
        # Try extreme concurrency first, fall back if needed
        try:
            print("🚀 Attempting EXTREME parallel processing with 100 concurrent threads...")
            processed = processor.process_batch_words(1000, max_concurrent=100)
        except Exception as e:
            print(f"⚠️ Extreme concurrency failed: {e}")
            print("🔄 Falling back to safe 20 concurrent threads...")
            processed = processor.process_batch_words(1000, max_concurrent=20)
        
        print(f"🎉 Processed {processed} words in this batch")
        processor.print_stats()
        
    elif command == "extreme":
        # EXTREME MODE: Smart rate-limited processing - RUN UNTIL COMPLETION!
        print("🔥 EXTREME MODE: Smart rate-limited DeepSeek processing!")
        print("🚀 RUNNING UNTIL ALL WORDS ARE COMPLETED!")
        print("🧠 Will automatically adjust concurrency based on rate limits")
        
        total_processed = 0
        session_start = time.time()
        current_concurrency = 50   # Start with safe 50 concurrent threads
        rate_limit_hits = 0
        
        while True:
            remaining = processor.get_remaining_words()
            if not remaining:
                print("🎉 ALL WORDS COMPLETED!")
                break
                
            batch_size = min(1000, len(remaining))
            print(f"\n🔄 Processing next {batch_size} words with {current_concurrency} concurrent threads...")
            
            try:
                processed = processor.process_batch_words(batch_size, max_concurrent=current_concurrency)
                total_processed += processed
                
                # If we processed successfully, we can try increasing concurrency
                if processed > batch_size * 0.8:  # 80% success rate
                    if current_concurrency < 500:
                        current_concurrency = min(500, current_concurrency + 50)
                        print(f"✅ Good success rate - increasing concurrency to {current_concurrency}")
                    rate_limit_hits = 0
                else:
                    # If low success rate, probably hit rate limits
                    rate_limit_hits += 1
                    if rate_limit_hits >= 2:
                        current_concurrency = max(50, current_concurrency - 100)
                        print(f"⚠️ Rate limits detected - reducing concurrency to {current_concurrency}")
                        print("⏱️ Waiting 60 seconds for rate limit reset...")
                        time.sleep(60)
                        rate_limit_hits = 0
                
                elapsed = time.time() - session_start
                overall_rate = total_processed / (elapsed / 3600) if elapsed > 0 else 0
                
                print(f"\n📊 SESSION PROGRESS:")
                print(f"✅ Total processed this session: {total_processed}")
                print(f"⚡ Overall rate: {overall_rate:.1f} words/hour")
                print(f"⏱️ Session time: {processor.format_time(elapsed)}")
                print(f"📈 Remaining words: {len(remaining)}")
                print(f"🔧 Current concurrency: {current_concurrency}")
                
                # Adaptive break between batches
                sleep_time = 5 if rate_limit_hits > 0 else 2
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"❌ Batch failed: {e}")
                current_concurrency = max(50, current_concurrency // 2)
                print(f"🔄 Reducing concurrency to {current_concurrency} and waiting 30 seconds...")
                time.sleep(30)
        
        total_time = time.time() - session_start
        final_rate = total_processed / (total_time / 3600) if total_time > 0 else 0
        
        print(f"\n🎉 EXTREME MODE COMPLETION!")
        print(f"✅ Total words processed: {total_processed}")
        print(f"⏱️ Total session time: {processor.format_time(total_time)}")
        print(f"🚀 Final rate: {final_rate:.1f} words/hour")
        
        processor.print_stats()
        
    elif command == "stats":
        processor.print_stats()
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
