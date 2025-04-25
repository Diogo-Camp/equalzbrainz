import requests
import json

def test_chat():
    url = "http://192.168.0.36:5000/api/chat"
    data = {
        "conversation_id": "teste123",
        "message": "Olá, como vai?"
    }
    
    try:
        response = requests.post(
            url,
            json=data,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        print("Resposta:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    test_chat()