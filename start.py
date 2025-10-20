#!/usr/bin/env python3
"""
Enhanced Speech Analysis System Launcher
Starts both the main interface and admin panel
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    print("🎤 Starting Enhanced Speech Analysis System...")
    print("=" * 50)
    
    # Check if we're in the right directory
    enhanced_dir = Path("enhanced_system")
    if not enhanced_dir.exists():
        print("❌ Error: enhanced_system directory not found")
        print("Please run this script from the CircuitAlg root directory")
        sys.exit(1)
    
    try:
        # Start the main speech server
        print("🚀 Starting main speech analysis server...")
        main_server = subprocess.Popen([
            sys.executable, "enhanced_speech_server.py"
        ], cwd=enhanced_dir)
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        # Start the admin panel
        print("🔧 Starting admin training panel...")
        admin_server = subprocess.Popen([
            sys.executable, "admin_panel.py"
        ], cwd=enhanced_dir)
        
        # Wait for both servers to start
        time.sleep(3)
        
        print("\n✅ System started successfully!")
        print("=" * 50)
        print("🌐 Main Interface: http://localhost:5003")
        print("⚙️  Admin Panel:   http://localhost:5002")
        print("=" * 50)
        print("Press Ctrl+C to stop both servers")
        
        # Open browser windows
        try:
            webbrowser.open("http://localhost:5003")
            time.sleep(1)
            webbrowser.open("http://localhost:5002")
        except:
            pass
        
        # Wait for user interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            main_server.terminate()
            admin_server.terminate()
            
            # Wait for graceful shutdown
            main_server.wait(timeout=5)
            admin_server.wait(timeout=5)
            
            print("✅ Servers stopped successfully")
            
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
