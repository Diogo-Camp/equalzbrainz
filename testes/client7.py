import requests
import json

def send_message(message, conversation_id=None):
    url = "http://192.168.0.36:5000/api/chat"
    data = {"message": message}
    if conversation_id:
        data["conversation_id"] = conversation_id
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None

if __name__ == "__main__":
    while True:
        msg = input("Você: ")
        if msg.lower() in ['sair', 'exit']:
            break
        send_message(msg)