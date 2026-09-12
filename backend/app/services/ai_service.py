import logging
logger = logging.getLogger(__name__)
class AIService:
    def chat(self, message: str, model: str, api_key: str, temperature: float) -> dict:
        if not message:
            raise ValueError("message is required")
        system_prompt = """You are an expert Formula 1 analyst and racing strategist. You have deep knowledge of:
- Current F1 regulations and technical rules
- Driver performance histories and driving styles
- Team strategies and car characteristics
- Circuit layouts and their specific challenges
- Weather impacts on racing
- Tyre strategies and degradation patterns
Provide detailed, accurate, and insightful responses about F1 racing. When discussing predictions or probabilities, always acknowledge uncertainty."""
        enhanced = f"{system_prompt}\n\nUser question: {message}"
        if api_key:
            from engine.ai_client import ai_client
            res = ai_client.call_ai(model=model, api_key=api_key, prompt=enhanced, temperature=temperature, max_tokens=1500)
            if res and 'text' in res:
                return {"response": res["text"], "provider": res.get("provider"), "model": model}
            fallback = "I'm having trouble connecting to the AI service right now. However, I can still help you with F1 predictions using the traditional ML models available in the dashboard."
            return {"response": fallback, "provider":"fallback","model": model}
        else:
            from ai.provider import AIProviderManager
            manager = AIProviderManager()
            result = manager.predict(prompt=enhanced)
            return {"response": result.get("text", str(result)), "provider":"fallback","model": model}
ai_service = AIService()
