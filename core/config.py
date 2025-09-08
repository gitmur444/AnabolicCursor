import os
from typing import Dict

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # dotenv not installed, use only environment variables

from utils.logging_utils import log_event


class ProxyConfig:
    """Configuration class for Cursor Proxy application."""
    
    def __init__(self):
        # Base URLs and keys
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Models - fixed to gpt-5 only
        self.default_model = "gpt-5"
        
        # Validate and set max_log_text
        try:
            self.max_log_text = int(os.getenv("MAX_LOG_TEXT", "2000000"))
            if self.max_log_text <= 0:
                raise ValueError("MAX_LOG_TEXT must be positive")
        except ValueError as e:
            log_event("config_error", {"field": "MAX_LOG_TEXT", "error": str(e)})
            self.max_log_text = 2000000  # fallback
        
        # Validate base URL
        if not self.openai_base_url.startswith(("http://", "https://")):
            log_event("config_error", {"field": "OPENAI_BASE_URL", "error": "Invalid URL format"})
            self.openai_base_url = "https://api.openai.com"  # fallback
        
        # Warning if no API key is provided
        if not self.openai_api_key:
            log_event("config_warning", {"message": "No OPENAI_API_KEY provided - will require key in requests"})
        
        # Log startup configuration
        log_event("startup", {
            "DEFAULT_MODEL": self.default_model,
            "OPENAI_BASE_URL": self.openai_base_url,
            "HAS_API_KEY": bool(self.openai_api_key),
            "MAX_LOG_TEXT": self.max_log_text
        })


# Global config instance
config = ProxyConfig()