"""
Tests for AI Client model provider identification and formatting.
"""
from engine.ai_client import AIClient


def test_determine_provider():
    client = AIClient()
    assert client._determine_provider("gemini-2.5-pro") == "gemini"
    assert client._determine_provider("gemini-1.5-flash") == "gemini"
    assert client._determine_provider("gpt-4o") == "openai"
    assert client._determine_provider("claude-3.5-sonnet") == "anthropic"
    assert client._determine_provider("llama-3.3-70b") == "groq"
    assert client._determine_provider("mistral-large") == "mistral"


def test_format_predictions():
    client = AIClient()
    preds = {"VER": 0.45, "NOR": 0.25, "HAM": 0.15}
    formatted = client._format_predictions(preds)
    assert "VER: 45.0%" in formatted
    assert "NOR: 25.0%" in formatted
