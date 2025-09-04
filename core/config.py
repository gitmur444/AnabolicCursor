import os
from typing import Dict

from utils.logging_utils import log_event


class ProxyConfig:
    """Configuration class for Cursor Proxy application."""
    
    def __init__(self):
        # Base URLs and keys
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Models - fixed to gpt-5 only
        self.default_model = "gpt-5"
        self.max_log_text = int(os.getenv("MAX_LOG_TEXT", "2000000"))
        
        # Log startup configuration
        log_event("startup", {
            "DEFAULT_MODEL": self.default_model
        })


# Global config instance
config = ProxyConfig()