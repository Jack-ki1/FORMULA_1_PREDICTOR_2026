from typing import Dict, Any
from backend.app.config.settings import settings

# Default AI model configurations
AI_MODEL_CONFIGS = {
    'huggingface': {
        'model_id': 'microsoft/phi-2',
        'max_tokens': 100,
        'temperature': 0.7,
        'top_p': 0.9
    },
    'openai': {
        'model': 'gpt-3.5-turbo-instruct',
        'max_tokens': 100,
        'temperature': 0.7,
        'top_p': 0.9
    }
}


def get_ai_config(provider_name: str) -> Dict[str, Any]:
    """Get AI provider configuration."""
    provider_name = provider_name.lower()
    if provider_name in AI_MODEL_CONFIGS:
        return AI_MODEL_CONFIGS[provider_name].copy()
    
    # Return default config for unknown providers
    return AI_MODEL_CONFIGS['huggingface'].copy()


def get_huggingface_config() -> Dict[str, Any]:
    """Get Hugging Face specific configuration."""
    config = get_ai_config('huggingface')
    config['api_key'] = settings.HUGGINGFACE_API_KEY
    config['model_id'] = getattr(settings, 'HUGGINGFACE_MODEL_ID', 'microsoft/phi-2')
    return config


def get_openai_config() -> Dict[str, Any]:
    """Get OpenAI specific configuration."""
    config = get_ai_config('openai')
    config['api_key'] = settings.OPENAI_API_KEY
    config['model'] = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo-instruct')
    return config