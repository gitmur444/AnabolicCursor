# AnabolicCursor - OpenAI API Proxy

A proxy server for Cursor IDE, compatible with OpenAI API. Intercepts and logs all requests between Cursor and OpenAI for analysis and debugging.

## Quick Start

### 🚀 One-Command Setup (Recommended)

```bash
cd AnabolicCursor

# 1. Install dependencies (first time only)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Add your OpenAI API key to .env file
# .env file is already created with your key, or create it:
# echo "OPENAI_API_KEY=your_api_key_here" > .env

# 3. Start everything with one command
./start.sh
```

The script will automatically:
- Start ngrok tunnel
- Start proxy server  
- Display the ngrok URL for Cursor configuration
- Show live logs

### 📋 Cursor Configuration

When `start.sh` shows the ngrok URL, configure Cursor:

1. Open **Settings** → **Models** → **Advanced**
2. **Override OpenAI Base URL**: `https://your-ngrok-url.ngrok.io` (from start.sh output)
3. **Model**: use any model name (will be automatically routed to gpt-5)

### ⚙️ Manual Setup (Advanced)

<details>
<summary>Click to expand manual setup instructions</summary>

#### 1. Installation and Setup

```bash
cd AnabolicCursor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start proxy server
uvicorn core.app:app --host 0.0.0.0 --port 8787 --reload
```

#### 2. Expose with Ngrok

Since Cursor blocks localhost URLs, you need to expose the proxy through ngrok:

```bash
# Install ngrok if not already installed
# Download from https://ngrok.com/download

# In a NEW terminal window, expose local server
ngrok http 8787
```

Copy the generated URL (e.g., `https://abc123.ngrok.io`)

**Note**: Keep both terminals running - one for the proxy server, one for ngrok.

</details>

### 🔑 Configuration

#### Using .env file (Recommended)

Create or edit `.env` file in project root:

```bash
# OpenAI API Configuration  
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com

# Proxy Configuration
DEFAULT_MODEL=gpt-5
MAX_LOG_TEXT=2000000

# Retry Configuration
RETRY_MAX=3
RETRY_BASE_SECONDS=1.5
RETRY_MAX_SECONDS=20
```

#### Using Environment Variables (Alternative)

```bash
# API key (if not using .env file)
export OPENAI_API_KEY=sk-...
```

## Log Viewing

### Primary Method
All logs are saved to file:
```bash
tail -f logs/proxy.log | jq .
```

### Monitoring (BETA)
Additionally available Grafana + Loki stack:

```bash
# Start monitoring
docker-compose up -d

# Open Grafana
open http://localhost:3000
# Login: admin / admin
```

In Grafana add Loki data source: `http://loki:3100`

Example queries:
```
{job="proxy"} | json | event="incoming_request"
{job="proxy"} | json | event="response" 
{job="proxy"} | json | model="gpt-5"
```

## Log Structure

Each event is logged in JSON format:

```json
{
  "event": "incoming_request",
  "timestamp": 1756971574,
  "data": {
    "model": "gpt-5",
    "message_count": 3,
    "has_tool_results": false,
    "stream": true,
    "tools_available": true,
    "full_payload": { ... }
  }
}
```

### Events:
- `incoming_request` - request from Cursor (includes full payload)
- `response` - response from OpenAI
- `retry_scheduled` - retry attempts on rate limits
- `error` - errors

## Features

- ✅ **Complete logging** of all requests/responses
- ✅ **Streaming support** (Server-Sent Events)
- ✅ **Automatic retries** on rate limits (429)
- ✅ **Tool calls analysis** from model
- ✅ **Security** - API key masking in logs
- ✅ **Fixed gpt-5 routing** - all requests go to gpt-5
- ✅ **JSON formatting** with indentation

## Requirements

- Python 3.10+
- Cursor IDE
- OpenAI API key

## Documentation

Detailed architecture and modules description: [STRUCTURE.md](STRUCTURE.md)