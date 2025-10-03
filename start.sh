#!/bin/bash

# AnabolicCursor Simple Startup Script
set -e

echo "🚀 Starting AnabolicCursor Proxy..."

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Kill existing processes quietly
pkill -f "uvicorn.*core.app" 2>/dev/null || true
pkill -f "ngrok.*http.*8787" 2>/dev/null || true
sleep 1

echo "📡 Starting ngrok tunnel..."

# Start ngrok in background
ngrok http 8787 > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to be ready
sleep 4

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('')
")

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to start ngrok tunnel"
    kill $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo "📡 Ngrok tunnel ready"
echo "🖥️  Starting proxy server..."

# Install python-dotenv if missing
source venv/bin/activate
pip install -q python-dotenv 2>/dev/null || true

# Start proxy server (let logs go to the file, suppress only uvicorn startup noise)
uvicorn core.app:app --host 0.0.0.0 --port 8787 --reload --log-level warning &
PROXY_PID=$!

# Wait for proxy to be ready
sleep 3
if ! curl -s http://localhost:8787/ > /dev/null 2>&1; then
    echo "❌ Failed to start proxy server"
    kill $PROXY_PID $NGROK_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Ready! Cursor Settings URL: $NGROK_URL/v1"
echo "⏹️  Stop: Ctrl+C"
echo

# Save PIDs for cleanup
echo $PROXY_PID > .proxy_pid
echo $NGROK_PID > .ngrok_pid

# Cleanup function
cleanup() {
    echo "🛑 Stopping..."
    kill $PROXY_PID $NGROK_PID 2>/dev/null || true
    rm -f .proxy_pid .ngrok_pid
    exit 0
}

# Handle Ctrl+C
trap cleanup SIGINT

# Keep process running
sleep 86400