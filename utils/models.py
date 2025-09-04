from typing import Optional, Dict, Any

from core.config import config


def resolve_model(model: Optional[str]) -> str:
    """Resolve model name using aliases or return default."""
    if not model:
        return config.default_model
    return config.model_aliases.get(model.strip(), model.strip())


def sanitize_payload(body: Dict[str, Any]) -> Dict[str, Any]:
    """Remove unsupported parameters for certain models."""
    model = body.get("model", "")
    if model.startswith("gpt-5"):
        # Убираем неподдерживаемые параметры
        for field in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]:
            body.pop(field, None)
        
        # Заменяем max_tokens на max_completion_tokens для gpt-5
        if "max_tokens" in body:
            body["max_completion_tokens"] = body.pop("max_tokens")
    
    return body
