#!/usr/bin/env python3
"""
Simple HTTP server to serve the audio recorder web page on localhost.
Run this script and open http://localhost:8000 in your browser.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import socket
from pathlib import Path

# Configuration
DEFAULT_PORT = 8000
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve index.html as the default page"""
    
    def end_headers(self):
        # Add CORS headers for better browser compatibility
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def find_available_port(start_port=DEFAULT_PORT):
    """Find an available port starting from the given port number"""
    port = start_port
    while port < start_port + 100:  # Try up to 100 ports
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, port))
                return port
        except OSError:
            port += 1
    raise RuntimeError(f"Could not find an available port starting from {start_port}")

def main():
    # Change to the script's directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if index.html exists
    if not Path('index.html').exists():
        print("❌ Error: index.html not found in the current directory!")
        print(f"   Current directory: {script_dir}")
        print("   Please make sure index.html is in the same directory as this script.")
        sys.exit(1)
    
    # Find an available port
    try:
        PORT = find_available_port()
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Create and configure the server
    with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
        server_url = f"http://{HOST}:{PORT}"
        
        print("🚀 Audio Recorder Server Starting...")
        print(f"📁 Serving files from: {script_dir}")
        print(f"🌐 Server running at: {server_url}")
        if PORT != DEFAULT_PORT:
            print(f"ℹ️  Note: Using port {PORT} (port {DEFAULT_PORT} was already in use)")
        print("📱 Features available:")
        print("   • Record 10-second audio clips")
        print("   • Upload audio files")
        print("   • View waveform visualization")
        print("   • See audio duration")
        print("\n🎯 Instructions:")
        print("   1. Click the link above or copy it to your browser")
        print("   2. Allow microphone access when prompted (for recording)")
        print("   3. Use 'Record 10s' to record audio or 'Upload File' to load audio")
        print("   4. Press Ctrl+C to stop the server")
        print("\n" + "="*60)
        
        try:
            # Try to open the browser automatically
            print(f"🔗 Opening browser automatically...")
            webbrowser.open(server_url)
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"   Please manually open: {server_url}")
        
        try:
            print(f"\n✅ Server is ready! Visit: {server_url}")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped by user (Ctrl+C)")
            print("👋 Thanks for using the Audio Recorder!")

if __name__ == "__main__":
    main()
