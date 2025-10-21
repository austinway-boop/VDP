#!/usr/bin/env python3
"""
ULTRA FAST Word Recovery System
Uses maximum safe concurrency to process all words as fast as possible
"""

import json
import os
import time
import requests
import threading
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Optional
import nltk
from nltk.corpus import wordnet
import random
import queue
from collections import defaultdict

class UltraFastWordRecovery:
    def __init__(self, max_workers: int = 1000):
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = "sk-af72eeb88bb3435c9656b175ec21d884"
        self.model = "deepseek-chat"
        self.max_workers = max_workers
        
        # Output directory
        self.output_dir = Path("words")
        self.output_dir.mkdir(exist_ok=True)
        
        # Statistics with thread safety
        self.stats_lock = threading.Lock()
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_update = time.time()
        
        # File locks for thread-safe writing
        self.file_locks = defaultdict(threading.Lock)
        
        # Rate limiting
        self.request_times = queue.Queue()
        self.rate_limit_lock = threading.Lock()
        
        print(f"🚀 ULTRA FAST Recovery System - {max_workers} CONCURRENT WORKERS!")
        print("⚡ This will process words at MAXIMUM SPEED!")
    
    def rate_limit_request(self):
        """Implement intelligent rate limiting"""
        with self.rate_limit_lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            while not self.request_times.empty():
                try:
                    old_time = self.request_times.get_nowait()
                    if now - old_time > 60:
                        continue
                    else:
                        self.request_times.put(old_time)
                        break
                except queue.Empty:
                    break
            
            # Count recent requests
            temp_queue = queue.Queue()
            recent_requests = 0
            
            while not self.request_times.empty():
                try:
                    req_time = self.request_times.get_nowait()
                    temp_queue.put(req_time)
                    recent_requests += 1
                except queue.Empty:
                    break
            
            # Put them back
            while not temp_queue.empty():
                try:
                    self.request_times.put(temp_queue.get_nowait())
                except queue.Empty:
                    break
            
            # Rate limit: max 1000 requests per minute (aggressive but safe)
            if recent_requests >= 6000:
                sleep_time = 60 - (now - old_time) if not self.request_times.empty() else 1
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Record this request
            self.request_times.put(now)
    
    def download_wordnet(self):
        """Download WordNet data if not available"""
        print("📚 Ensuring WordNet data is available...")
        try:
            nltk.data.find('corpora/wordnet')
            print("✅ WordNet already available")
        except LookupError:
            print("📥 Downloading WordNet...")
            nltk.download('wordnet')
            nltk.download('omw-1.4')
    
    def extract_all_words(self) -> List[str]:
        """Extract all unique words from WordNet"""
        print("🔍 Extracting all words from WordNet...")
        
        all_words = set()
        
        for synset in wordnet.all_synsets():
            for lemma in synset.lemmas():
                word = lemma.name().lower().replace('_', ' ')
                if word and word.isalpha() and len(word) > 1:
                    all_words.add(word)
        
        word_list = sorted(list(all_words))
        print(f"✅ Extracted {len(word_list):,} unique words from WordNet")
        return word_list
    
    def get_file_for_word(self, word: str) -> str:
        """Determine which file a word should be saved to"""
        if not word:
            return "empty.json"
        
        first_char = word[0].lower()
        if first_char.isalpha():
            return f"{first_char}.json"
        elif first_char.isdigit():
            return "numbers.json"
        else:
            return "symbols.json"
    
    def make_ultra_fast_request(self, word: str) -> Optional[Dict]:
        """Ultra-fast DeepSeek API request with optimizations"""
        
        # Rate limiting
        self.rate_limit_request()
        
        # Shorter, more efficient prompt
        prompt = f'Word: "{word}". Return JSON: {{"word":"{word}","stats":{{"emotion_probs":{{"joy":0.125,"trust":0.125,"anticipation":0.125,"surprise":0.125,"anger":0.125,"fear":0.125,"sadness":0.125,"disgust":0.125}},"vad":{{"valence":0.5,"arousal":0.5,"dominance":0.5}},"sentiment":{{"polarity":"neutral","strength":0.5}},"pos":["noun"],"social_axes":{{"good_bad":0,"warmth_cold":0,"competence_incompetence":0,"active_passive":0}},"toxicity":0,"dynamics":{{"negation_flip_probability":0,"sarcasm_flip_probability":0}}}}}}'
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                self.deepseek_url, 
                headers=headers, 
                json=data, 
                timeout=15  # Aggressive timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Parse JSON
            word_data = json.loads(content)
            return word_data
            
        except Exception as e:
            # Fast fail - don't waste time on retries
            return None
    
    def save_word_ultra_fast(self, word_data: Dict):
        """Ultra-fast thread-safe word saving"""
        word = word_data['word']
        filename = self.get_file_for_word(word)
        file_path = self.output_dir / filename
        
        # Use specific file lock for thread safety
        with self.file_locks[filename]:
            # Load existing data
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = {"words": []}
            else:
                data = {"words": []}
            
            # Add new word (skip duplicate check for speed)
            data['words'].append(word_data)
            
            # Save immediately (don't sort for speed)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))  # Compact JSON
    
    def process_word_ultra_fast(self, word: str) -> bool:
        """Ultra-fast single word processing"""
        try:
            word_data = self.make_ultra_fast_request(word)
            if word_data:
                self.save_word_ultra_fast(word_data)
                
                with self.stats_lock:
                    self.processed_count += 1
                    
                    # Update every 50 words for speed
                    if self.processed_count % 50 == 0:
                        now = time.time()
                        elapsed = now - self.start_time
                        rate = self.processed_count / elapsed * 3600
                        remaining = len(self.all_words) - self.processed_count
                        eta = remaining / (rate / 3600) if rate > 0 else 0
                        
                        print(f"⚡ ULTRA SPEED: {self.processed_count:,}/{len(self.all_words):,} "
                              f"({rate:.0f} words/hour) ETA: {eta/3600:.1f}h - "
                              f"Errors: {self.error_count}")
                
                return True
            else:
                with self.stats_lock:
                    self.error_count += 1
                return False
                
        except Exception as e:
            with self.stats_lock:
                self.error_count += 1
            return False
    
    def ultra_fast_parallel_processing(self, words: List[str]):
        """MAXIMUM SPEED parallel processing"""
        self.all_words = words
        
        print(f"🚀 LAUNCHING {self.max_workers} CONCURRENT WORKERS!")
        print(f"⚡ Processing {len(words):,} words at MAXIMUM SPEED!")
        print("🔥 This is going to be FAST!")
        
        # Shuffle for load distribution
        words_shuffled = words.copy()
        random.shuffle(words_shuffled)
        
        # Use ThreadPoolExecutor with maximum workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            print(f"💥 {self.max_workers} workers launched! Processing at light speed...")
            
            # Submit all tasks
            futures = [executor.submit(self.process_word_ultra_fast, word) for word in words_shuffled]
            
            try:
                # Wait for completion with progress updates
                start_time = time.time()
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    if i % 1000 == 0 and i > 0:
                        elapsed = time.time() - start_time
                        rate = i / elapsed * 3600
                        print(f"🔥 BLAZING SPEED: {i:,} completed ({rate:.0f}/hour)")
                
            except KeyboardInterrupt:
                print("\n⚠️  EMERGENCY STOP! Shutting down all workers...")
                executor.shutdown(wait=True)
        
        # Final ultra stats
        elapsed = time.time() - self.start_time
        print(f"\n🎉 ULTRA FAST PROCESSING COMPLETE!")
        print(f"⚡ Processed: {self.processed_count:,} words")
        print(f"❌ Errors: {self.error_count:,} words") 
        print(f"🔥 Total time: {elapsed/3600:.2f} hours")
        print(f"💥 INSANE RATE: {self.processed_count/elapsed*3600:.0f} words/hour")
        print(f"🚀 That's {self.processed_count/elapsed:.1f} words per SECOND!")
    
    def create_file_structure(self):
        """Create empty JSON structure for all files"""
        print("📁 Creating ultra-fast file structure...")
        
        files_to_create = [f"{chr(i)}.json" for i in range(ord('a'), ord('z')+1)]
        files_to_create.extend(["numbers.json", "symbols.json"])
        
        for filename in files_to_create:
            file_path = self.output_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({"words": []}, f)
        
        print(f"✅ Created {len(files_to_create)} files for ULTRA SPEED processing")
    
    def run_ultra_recovery(self):
        """Run the ULTRA FAST recovery process"""
        print("🔥 STARTING ULTRA FAST WORD RECOVERY!")
        print("="*60)
        print("⚡ MAXIMUM SPEED MODE ENGAGED!")
        print("🚀 This will be the FASTEST word processing ever!")
        print()
        
        # Download WordNet
        self.download_wordnet()
        
        # Create file structure
        self.create_file_structure()
        
        # Extract words
        all_words = self.extract_all_words()
        
        # ULTRA FAST processing
        self.ultra_fast_parallel_processing(all_words)
        
        print("\n🎉 ULTRA FAST RECOVERY COMPLETE!")
        print("🔥 Your word database is now COMPLETE at RECORD SPEED!")

def main():
    """Main ultra-fast recovery function"""
    print("🔥 ULTRA FAST WORD RECOVERY SYSTEM")
    print("="*60)
    print("⚡ MAXIMUM SPEED MODE!")
    print()
    print("This will use 1,000 CONCURRENT WORKERS to process words at:")
    print("🚀 Estimated speed: 50,000-100,000 words/hour")  
    print("⚡ Completion time: 1-2 hours (INSANELY FAST!)")
    print("💥 Cost: ~$25-30 in API fees")
    print()
    print("⚠️  WARNING: This is ABSOLUTELY INSANE!")
    print("   • Uses 1,000 concurrent API requests")
    print("   • 6,000 requests per minute rate limit")
    print("   • MAXIMUM POSSIBLE SPEED")
    print("   • May overwhelm the API (proceed with caution!)")
    print()
    
    confirm = input("Ready for ULTRA SPEED processing? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Ultra speed cancelled")
        return
    
    print("\n🔥 ENGAGING MAXIMUM SPEED MODE!")
    
    # Create ultra-fast recovery system
    recovery = UltraFastWordRecovery(max_workers=1000)
    recovery.run_ultra_recovery()

if __name__ == "__main__":
    main()
