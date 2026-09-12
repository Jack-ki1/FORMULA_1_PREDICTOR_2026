'''
AI/LLM Client for prediction enhancement.
Supports Gemini, OpenAI, Anthropic, Groq, Mistral, Cohere, and OpenAI-compatible endpoints.
'''
import logging
import requests
import json
from typing import Dict, List, Any, Optional
from ai.provider import AIProviderManager

logger = logging.getLogger(__name__)


class AIClient:
    """Client for AI/LLM providers to enhance predictions and chat."""
    
    def __init__(self):
        self.provider_manager = AIProviderManager()
    
    def _determine_provider(self, model: str) -> str:
        """Determine provider from model name."""
        m = model.lower()
        if m.startswith('gemini'):
            return 'gemini'
        elif m.startswith('gpt') or m.startswith('o1') or m.startswith('o3') or m.startswith('text-embedding') or m.startswith('chatgpt'):
            return 'openai'
        elif m.startswith('claude'):
            return 'anthropic'
        elif m.startswith('llama') or m.startswith('gemma'):
            return 'groq'
        elif m.startswith('mistral') or m.startswith('mixtral'):
            return 'mistral'
        elif m.startswith('command'):
            return 'cohere'
        elif m.startswith('deepseek'):
            return 'deepseek'
        elif m.startswith('qwen'):
            return 'qwen'
        else:
            return 'openai_compatible'
    
    def call_ai(
        self,
        model: str,
        api_key: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Optional[Dict[str, Any]]:
        """
        Call AI API with the given prompt.
        
        Args:
            model: Model identifier
            api_key: API key for the provider
            prompt: Prompt text
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
        
        Returns:
            AI response as dictionary, or None if failed
        """
        if not api_key or not api_key.strip():
            logger.warning("No API key provided for AI call")
            return None

        provider = self._determine_provider(model)
        
        try:
            if provider == 'gemini':
                # Gemini REST generateContent API - updated for latest models
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    'contents': [{'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'temperature': temperature,
                        'maxOutputTokens': max_tokens,
                    }
                }
                try:
                    resp = requests.post(url, headers=headers, json=payload, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get('candidates', [])
                        if candidates:
                            parts = candidates[0].get('content', {}).get('parts', [])
                            if parts:
                                return {'text': parts[0].get('text', ''), 'provider': 'gemini'}
                    else:
                        logger.warning(f"Gemini API error {resp.status_code}: {resp.text}")
                        # Try fallback to v1 API if v1beta fails
                        if 'v1beta' in url:
                            fallback_url = url.replace('v1beta', 'v1')
                            resp = requests.post(fallback_url, headers=headers, json=payload, timeout=30)
                            if resp.status_code == 200:
                                data = resp.json()
                                candidates = data.get('candidates', [])
                                if candidates:
                                    parts = candidates[0].get('content', {}).get('parts', [])
                                    if parts:
                                        return {'text': parts[0].get('text', ''), 'provider': 'gemini'}
                except Exception as gemini_err:
                    logger.warning(f"Gemini API request failed: {gemini_err}")

            elif provider == 'anthropic':
                # Anthropic Messages API
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': api_key.strip(),
                    'anthropic-version': '2023-06-01'
                }
                payload = {
                    'model': model,
                    'max_tokens': max_tokens,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': temperature,
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get('content', [])
                    if content:
                        return {'text': content[0].get('text', ''), 'provider': 'anthropic'}
                else:
                    logger.warning(f"Anthropic API error {resp.status_code}: {resp.text}")

            elif provider == 'groq':
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {api_key.strip()}"
                }
                payload = {
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': 'You are a concise Formula 1 analysis assistant.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get('choices', [])
                    if choices:
                        return {'text': choices[0].get('message', {}).get('content', ''), 'provider': 'groq'}
                else:
                    logger.warning(f"Groq API error {resp.status_code}: {resp.text}")

            elif provider == 'mistral':
                url = "https://api.mistral.ai/v1/chat/completions"
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {api_key.strip()}"
                }
                payload = {
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': 'You are a concise Formula 1 analysis assistant.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get('choices', [])
                    if choices:
                        return {'text': choices[0].get('message', {}).get('content', ''), 'provider': 'mistral'}
                else:
                    logger.warning(f"Mistral API error {resp.status_code}: {resp.text}")

            else:
                # Default OpenAI / OpenAI-compatible endpoint
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f"Bearer {api_key.strip()}"
                }
                payload = {
                    'model': model if model != 'custom' else 'gpt-4o',
                    'messages': [
                        {'role': 'system', 'content': 'You are a concise Formula 1 analysis assistant. State uncertainty and do not invent live telemetry.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get('choices', [])
                    if choices:
                        return {'text': choices[0].get('message', {}).get('content', ''), 'provider': 'openai'}
                else:
                    logger.warning(f"OpenAI API error {resp.status_code}: {resp.text}")

        except Exception as e:
            logger.warning(f"AI API request failed for {model}: {e}")

        return None
    
    def call_multi_agent(
        self,
        query: str,
        context: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Call the Multi-Agent Pit Wall system to analyze a 'What-If' scenario.
        
        Args:
            query: Natural language scenario (e.g., "What happens if a Safety Car deploys on Lap 24?")
            context: Additional context like race_id, session_type, current_grid, etc.
        
        Returns:
            Dictionary with analysis results and broadcast-style narrative.
        """
        try:
            result = self.provider_manager.call_multi_agent(query, context)
            
            if result.get("success"):
                return {
                    "result": result["result"],
                    "provider": result["provider"],
                    "timestamp": result.get("timestamp", "")
                }
            else:
                logger.error(f"Multi-Agent Pit Wall failed: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Multi-Agent Pit Wall call failed: {e}")
            return None
    
    def get_prediction_insights(
        self,
        model: str,
        api_key: str,
        race_context: Dict[str, Any],
        current_predictions: Dict[str, float],
        temperature: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """
        Get AI insights and adjustments for race predictions.
        """
        # Enhanced prompt with more context
        prompt = f"""You are an F1 racing expert with deep knowledge of driver performance, circuit characteristics, and race strategy. Analyze the following race prediction and provide insights.

Race: {race_context.get('race_name', 'Unknown')}
Circuit: {race_context.get('circuit', 'Unknown')}
Weather: {race_context.get('weather', 'Unknown')}
Session: {race_context.get('session_type', 'Unknown')}
Sub-Session: {race_context.get('sub_session', 'N/A')}

Current top 5 predictions (driver, probability):
{self._format_predictions(current_predictions)}

Provide your analysis in JSON format with this exact structure:
{{
    "insights": "brief analysis of the race considering circuit characteristics, weather impact, and driver form",
    "upset_picks": ["driver1", "driver2"],
    "risk_factors": ["factor1", "factor2"],
    "adjustments": {{
        "DRIVER_CODE": 0.05
    }}
}}

Important guidelines:
- Only include adjustments between -0.1 and 0.1 for drivers you think are significantly over or under-valued
- Consider the specific session type (practice, qualifying, race) when making adjustments
- Factor in weather conditions and their impact on driver performance
- Be conservative with adjustments - small tweaks are better than large changes
- If you're uncertain about a driver, don't include them in adjustments"""
        
        try:
            response = self.call_ai(model, api_key, prompt, temperature)
            
            if response and response.get('text'):
                try:
                    text = response['text']
                    start_idx = text.find('{')
                    end_idx = text.rfind('}') + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = text[start_idx:end_idx]
                        insights = json.loads(json_str)
                        
                        # Validate adjustments
                        if 'adjustments' in insights:
                            for driver, adj in insights['adjustments'].items():
                                # Clamp adjustments to valid range
                                insights['adjustments'][driver] = max(-0.1, min(0.1, float(adj)))
                        
                        logger.info(f"AI insights generated successfully using {response.get('provider', 'ai')}")
                        return {
                            'insights': insights,
                            'provider': response.get('provider', 'ai'),
                            'raw_text': text
                        }
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse AI response JSON: {e}")
                    # Try to extract partial JSON or provide fallback
                    return self._fallback_insights(current_predictions)
                except Exception as e:
                    logger.warning(f"Error processing AI response: {e}")
                    return self._fallback_insights(current_predictions)
        except Exception as e:
            logger.warning(f"AI API call failed: {e}")
            return None
        
        return None
    
    def _fallback_insights(self, current_predictions: Dict[str, float]) -> Dict[str, Any]:
        """Provide fallback insights when AI fails."""
        sorted_preds = sorted(current_predictions.items(), key=lambda x: x[1], reverse=True)
        top_driver = sorted_preds[0][0] if sorted_preds else "VER"
        
        return {
            'insights': {
                'insights': f"Based on current model predictions, {top_driver} appears to be the favorite. Weather and track conditions will play a significant role in the final result.",
                'upset_picks': [sorted_preds[1][0] if len(sorted_preds) > 1 else "HAM"],
                'risk_factors': ['Weather conditions', 'Safety car probability', 'Tyre degradation'],
                'adjustments': {}  # No adjustments when AI fails
            },
            'provider': 'fallback',
            'raw_text': 'Fallback analysis due to AI unavailability'
        }
    
    def _format_predictions(self, predictions: Dict[str, float]) -> str:
        """Format predictions for prompt."""
        sorted_preds = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for driver, prob in sorted_preds[:5]:
            lines.append(f"  {driver}: {prob:.1%}")
        return '\n'.join(lines)


# Global AI client instance
ai_client = AIClient()
