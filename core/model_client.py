from ..ui_manager import UIManager
from typing import Optional, Dict, Any
import requests
import json
import os
ui = UIManager()


def send_prompt_to_model(prompt: str, backend: str=None, model: str=None
    ) ->Optional[str]:
    """
    Send a prompt to the specified LLM backend and return the response.
    
    Args:
        prompt (str): The prompt to send to the model
        backend (str, optional): Backend to use ('ollama' or 'openrouter')
        model (str, optional): Specific model to use
        
    Returns:
        Optional[str]: Model response text or None if failed
    """
    if not backend:
        backend = os.getenv('DEFAULT_BACKEND', 'ollama')
    if not model:
        model = os.getenv('DEFAULT_MODEL', ' llama3')
    try:
        if backend == 'ollama':
            return _send_ollama_request(prompt, model)
        elif backend == 'openrouter':
            return _send_openrouter_request(prompt, model)
        else:
            ui.show_error(f'Unsupported backend: {backend}')
            return None
    except Exception as e:
        ui.show_error(f'Model request failed: {str(e)}')
        return None


def _send_ollama_request(prompt: str, model: str) ->Optional[str]:
    """Send request to Ollama backend."""
    url = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
    payload = {'model': model, 'prompt': prompt, 'stream': False}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get('response')


def _send_openrouter_request(prompt: str, model: str) ->Optional[str]:
    """Send request to OpenRouter backend."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        ui.show_error('OPENROUTER_API_KEY not found in environment variables')
        return None
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type':
        'application/json'}
    payload = {'model': model, 'messages': [{'role': 'user', 'content':
        prompt}]}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content']
