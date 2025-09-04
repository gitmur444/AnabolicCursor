# AnabolicCursor Project Structure

## Project Architecture

```
AnabolicCursor/
├── app.py                     # 🚀 Entry point for uvicorn
├── core/                      # 📁 Core application components
│   ├── __init__.py
│   ├── app.py                 # FastAPI application factory
│   ├── config.py              # Application configuration
│   └── routes.py              # API route definitions
├── handlers/                  # 📁 Request handlers
│   ├── __init__.py
│   └── proxy_client.py        # Main proxy logic (streaming & JSON)
├── utils/                     # 📁 Utility modules
│   ├── __init__.py
│   ├── auth.py               # Authentication utilities
│   ├── http_utils.py         # HTTP helpers and error handling
│   ├── logging_utils.py      # Structured logging utilities
│   ├── models.py             # Model resolution and payload sanitization
│   └── retry_utils.py        # Retry logic for rate limits
├── parsers/                   # 📁 Data parsing modules
│   ├── __init__.py
│   ├── response_logger.py    # Response logging utilities
│   └── response_parser.py    # OpenAI response parsing
├── logs/                      # 📁 Application logs
│   └── proxy.log             # Main log file (JSON formatted)
├── loki/                      # 📁 Loki configuration (BETA)
├── promtail/                  # 📁 Promtail configuration (BETA)
├── venv/                      # 📁 Python virtual environment
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker services (Loki, Grafana, Promtail)
└── README.md                  # Project documentation
```

## Module Responsibilities

### 🚀 Entry Point
- **`app.py`**: Application entry point that imports the FastAPI app from `core.app`

### 📁 Core (`core/`)
- **`app.py`**: FastAPI application factory with CORS middleware setup
- **`config.py`**: Environment-based configuration management
- **`routes.py`**: API endpoint definitions (`/v1/chat/completions`, `/v1/responses`)

### 📁 Handlers (`handlers/`)
- **`proxy_client.py`**: Core proxy functionality
  - `proxy_json()` - Non-streaming requests
  - `proxy_stream()` - Streaming requests (SSE)

### 📁 Utils (`utils/`)
- **`auth.py`**: Authentication handling (Bearer tokens, API keys)
- **`http_utils.py`**: HTTP utilities and error handling
- **`logging_utils.py`**: Structured JSON logging with pretty printing
- **`models.py`**: Payload sanitization for gpt-5
- **`retry_utils.py`**: Retry mechanisms with exponential backoff

### 📁 Parsers (`parsers/`)
- **`response_parser.py`**: OpenAI response parsing (tool calls, choices, text)
- **`response_logger.py`**: Response logging utilities

## Data Flow

```
Client (Cursor) → routes.py → auth.py → models.py → proxy_client.py → OpenAI API
                                                         ↓
                                   response_parser.py → response_logger.py → logs/proxy.log
```

## Configuration

Environment variables:

```bash
# OpenAI API
OPENAI_BASE_URL=https://api.openai.com
OPENAI_API_KEY=your_api_key

# Models - fixed to gpt-5
DEFAULT_MODEL=gpt-5

# Logging
MAX_LOG_TEXT=2000000

# Retry Logic
RETRY_MAX=3
RETRY_BASE_SECONDS=1.5
RETRY_MAX_SECONDS=20
```