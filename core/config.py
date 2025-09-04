import os
from typing import Dict

from utils.logging_utils import log_event


class ProxyConfig:
    """Configuration class for Cursor Proxy application."""
    
    def __init__(self):
        # Base URLs and keys
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Models
        self.default_model = os.getenv("DEFAULT_MODEL", "gpt-5")
        self.max_log_text = int(os.getenv("MAX_LOG_TEXT", "2000000"))
        
        # Parse model aliases
        model_aliases_env = os.getenv("MODEL_ALIASES", "my-agent=gpt-5")
        self.model_aliases: Dict[str, str] = {}
        for pair in model_aliases_env.split(","):
            if "=" in pair:
                a, b = pair.split("=", 1)
                self.model_aliases[a.strip()] = b.strip()
        
        # Log startup configuration
        log_event("startup", {
            "MODEL_ALIASES": self.model_aliases, 
            "DEFAULT_MODEL": self.default_model
        })


# Global config instance
config = ProxyConfig()