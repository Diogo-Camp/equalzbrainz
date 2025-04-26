# config.py
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

DEFAULT_SESSAO_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,
    "repeat_penalty": 1.1,
    "num_predict": 400,
    "max_historico": 10
}