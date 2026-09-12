# F1 Prediction Platform AI Provider Integration

## Overview

This document describes the AI provider integration implemented in Phase 7. The system supports multiple AI providers with fallback strategies to ensure reliability.

## Supported Providers

### Hugging Face Inference API
- **Model ID**: `microsoft/phi-2` (configurable)
- **API Endpoint**: `https://api-inference.huggingface.co/models/{model_id}`
- **Authentication**: Bearer token
- **Use Case**: Local model inference, cost-effective predictions

### OpenAI API
- **Model**: `gpt-3.5-turbo-instruct` (configurable)
- **API Endpoint**: `https://api.openai.com/v1/completions`
- **Authentication**: Bearer token
- **Use Case**: Advanced reasoning, complex scenario analysis

## Configuration

Configuration options are available in `config/settings.py`:

- `AI_PROVIDER`: Primary AI provider ('huggingface' or 'openai')
- `HUGGINGFACE_API_KEY`: Hugging Face API key
- `OPENAI_API_KEY`: OpenAI API key
- `HUGGINGFACE_MODEL_ID`: Hugging Face model identifier
- `OPENAI_MODEL`: OpenAI model name
- `AI_MODEL_TEMPERATURE`: Temperature for model output randomness
- `AI_MODEL_MAX_TOKENS`: Maximum tokens in response
- `AI_MODEL_TOP_P`: Top-p sampling parameter

## Fallback Strategy

The system implements a robust fallback strategy:

1. **Primary Provider**: First attempt with configured primary provider
2. **Secondary Provider**: If primary fails, try the other provider
3. **Local Fallback**: If both external providers fail, use local Monte Carlo simulation

## Technical Implementation

### Core Components

- `ai/provider.py`: Main provider classes and manager
- `ai/config.py`: Provider-specific configuration management
- `engine/probability_model.py`: Integration point for AI predictions

### Error Handling

- Comprehensive error logging for all provider interactions
- Graceful degradation when providers are unavailable
- Detailed metrics on provider success/failure rates

## Technical Debt

- [ ] Implement rate limiting for AI API calls
- [ ] Add caching layer for AI provider responses
- [ ] Implement comprehensive AI provider health monitoring
- [ ] Add integration tests for AI provider fallback logic
- [ ] Document AI model training methodology and data sources