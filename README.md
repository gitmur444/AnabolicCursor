# AnabolicCursor - OpenAI API Proxy

A proxy server for Cursor IDE, compatible with OpenAI API. Intercepts and logs all requests between Cursor and OpenAI for analysis and debugging.

## Quick Start

### 1. Installation and Setup

```bash
cd AnabolicCursor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start proxy server
uvicorn app:app --host 0.0.0.0 --port 8787 --reload
```

### 2. Expose with Ngrok

Since Cursor blocks localhost URLs, you need to expose the proxy through ngrok:

```bash
# Install ngrok if not already installed
# Download from https://ngrok.com/download

# In a NEW terminal window, expose local server
ngrok http 8787
```

Copy the generated URL (e.g., `https://abc123.ngrok.io`)

**Note**: Keep both terminals running - one for the proxy server, one for ngrok.

### 3. Cursor Configuration

In Cursor IDE:
1. Open **Settings** → **Models** → **Advanced**
2. **Override OpenAI Base URL**: `https://your-ngrok-url.ngrok.io` (from step 2)
3. **Model**: select or enter a custom model (e.g., `my-agent`)

### 4. Configuration (Optional)

```bash
# Model aliases
export MODEL_ALIASES="my-agent=gpt-5,custom-gpt=gpt-4"

# API key (if not passed through Cursor)
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
- `incoming_request` - request from Cursor
- `forwarded_request` - request to OpenAI  
- `response` - response from OpenAI
- `retry_scheduled` - retry attempts on rate limits
- `error` - errors

## Features

- ✅ **Complete logging** of all requests/responses
- ✅ **Streaming support** (Server-Sent Events)
- ✅ **Automatic retries** on rate limits (429)
- ✅ **Tool calls analysis** from model
- ✅ **Security** - API key masking in logs
- ✅ **Model aliases** for convenience
- ✅ **JSON formatting** with indentation

## Requirements

- Python 3.10+
- Cursor IDE
- OpenAI API key

## Documentation

Detailed architecture and modules description: [STRUCTURE.md](STRUCTURE.md)