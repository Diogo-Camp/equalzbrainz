import requests
import os

#os.getenv("OLLAMA_HOST")

#ip = os.getenv("OLLAMA_HOST")  # troca aqui pro IP real do seu servidor

ip = "http://192.168.0.36:5000/api/health"
try:
    r = requests.get(ip)
    print(r.status_code, r.text)
except Exception as e:
    print("Erro:", e)