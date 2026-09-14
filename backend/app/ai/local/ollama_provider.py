import logging
from typing import Dict, Any, Optional
import requests
from openai import OpenAI
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama client using OpenAI-compatible API.
    
    Connects to http://localhost:11434/v1 for local offline LLM inference.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL or "http://localhost:11434/v1"
        self.api_key = settings.OLLAMA_API_KEY or "ollama"  # dummy key
        
        # Initialize OpenAI client with Ollama endpoint
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
    
    def predict(self, model: str, prompt: str, temperature: float = 0.7, 
                max_tokens: int = 1000) -> Optional[Dict[str, Any]]:
        """
        Call Ollama model with the given prompt.
        
        Args:
            model: Model name (e.g., 'llama3', 'qwen3:8b')
            prompt: Prompt text
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dictionary with 'text' and 'provider' keys, or None if failed
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a Formula 1 race strategist assistant. Be concise, factual, and use broadcast-style narration."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if response.choices and response.choices[0].message.content:
                return {
                    "text": response.choices[0].message.content.strip(),
                    "provider": "ollama",
                    "model": model
                }
            else:
                logger.warning("Ollama response has no content")
                return None
                
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return None
