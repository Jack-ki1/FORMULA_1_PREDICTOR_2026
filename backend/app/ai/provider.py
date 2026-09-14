import logging
from typing import Dict, Any, Optional
import requests
from backend.app.config.settings import settings
from backend.app.ai.local.ollama_provider import OllamaClient
from backend.app.ai.agents.chief_strategist import ChiefStrategistAgent

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class HuggingFaceClient:
    """Client for Hugging Face Inference API."""
    
    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model_id = settings.HUGGINGFACE_MODEL_ID
        self.base_url = "https://api-inference.huggingface.co/models/"
        
        if not self.api_key:
            logger.warning("Hugging Face API key not configured")
    
    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using Hugging Face model."""
        if not self.api_key:
            raise AIProviderError("Hugging Face API key not configured")
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(
                f"{self.base_url}{self.model_id}",
                headers=headers,
                json={"inputs": inputs},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Hugging Face API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise AIProviderError(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error with Hugging Face API: {e}")
            raise AIProviderError(f"Network error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error with Hugging Face API: {e}")
            raise AIProviderError(f"Unexpected error: {str(e)}") from e


class OpenAIClient:
    """Client for OpenAI API."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = "https://api.openai.com/v1/completions"
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
    
    def predict(self, prompt: str) -> Dict[str, Any]:
        """Make prediction using OpenAI model."""
        if not self.api_key:
            raise AIProviderError("OpenAI API key not configured")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"OpenAI API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise AIProviderError(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error with OpenAI API: {e}")
            raise AIProviderError(f"Network error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error with OpenAI API: {e}")
            raise AIProviderError(f"Unexpected error: {str(e)}") from e


class AIProviderFactory:
    """Factory for creating AI provider instances."""
    
    @staticmethod
    def get_provider():
        """Get appropriate AI provider based on configuration."""
        provider_name = settings.AI_PROVIDER.lower()
        
        if provider_name == 'huggingface':
            return HuggingFaceClient()
        elif provider_name == 'openai':
            return OpenAIClient()
        elif provider_name == 'ollama':
            return OllamaClient()
        else:
            logger.warning(f"Unknown AI provider: {provider_name}. Using fallback.")
            return None


class AIProviderManager:
    """Manager for handling AI provider fallback strategies."""
    
    def __init__(self):
        self.primary_provider = AIProviderFactory.get_provider()
        
    def predict(self, **kwargs) -> Dict[str, Any]:
        """Make prediction with fallback strategy."""
        providers_tried = []
        
        # Try primary provider
        if self.primary_provider:
            try:
                return self.primary_provider.predict(**kwargs)
            except AIProviderError as e:
                providers_tried.append(type(self.primary_provider).__name__)
                logger.warning(f"Primary AI provider failed: {e}")
        
        # Try fallback providers
        fallback_providers = self._get_fallback_providers()
        for provider in fallback_providers:
            try:
                providers_tried.append(type(provider).__name__)
                return provider.predict(**kwargs)
            except AIProviderError as e:
                logger.warning(f"Fallback AI provider {type(provider).__name__} failed: {e}")

        # All providers failed - return error
        error_msg = f"All AI providers failed: {', '.join(providers_tried)}"
        logger.error(error_msg)
        raise AIProviderError(error_msg)

    def _get_fallback_providers(self):
        """Get fallback providers in order of preference."""
        fallbacks = []
        
        # Add Hugging Face if not primary
        if settings.HUGGINGFACE_API_KEY and \
           (not self.primary_provider or not isinstance(self.primary_provider, HuggingFaceClient)):
            fallbacks.append(HuggingFaceClient())
        
        # Add OpenAI if not primary
        if settings.OPENAI_API_KEY and \
           (not self.primary_provider or not isinstance(self.primary_provider, OpenAIClient)):
            fallbacks.append(OpenAIClient())
        
        # Add Ollama if not primary
        if settings.OLLAMA_BASE_URL and \
           (not self.primary_provider or not isinstance(self.primary_provider, OllamaClient)):
            fallbacks.append(OllamaClient())
        
        return fallbacks
    
    def call_multi_agent(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call the Multi-Agent Pit Wall system to analyze a 'What-If' scenario.
        
        Args:
            query: Natural language scenario (e.g., "What happens if a Safety Car deploys on Lap 24?")
            context: Additional context like race_id, session_type, current_grid, etc.
        
        Returns:
            Dictionary with analysis results and broadcast-style narrative.
        """
        if context is None:
            context = {}
        
        try:
            # Initialize Chief Strategist Agent
            strategist = ChiefStrategistAgent()
            
            # Analyze the scenario
            result = strategist.analyze_scenario(query, context)
            
            return {
                "success": True,
                "result": result,
                "provider": "multi-agent",
                "timestamp": context.get("timestamp", "")
            }
            
        except Exception as e:
            logger.error(f"Multi-Agent Pit Wall analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "multi-agent"
            }