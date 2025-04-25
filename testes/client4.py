import requests
import json
import time

class ChatbotClient:
    def __init__(self, base_url="http://192.168.0.36:5000"):
        self.base_url = base_url
        self.conversation_id = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method, endpoint, **kwargs):
        try:
            response = getattr(self.session, method)(
                f"{self.base_url}{endpoint}", 
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\n⚠️ Erro na requisição: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Resposta do servidor: {e.response.text[:500]}")
            return None

    def start_conversation(self, title="Nova Conversa"):
        result = self._make_request(
            'post', 
            '/api/start',
            json={'title': title}
        )
        if result:
            self.conversation_id = result.get('conversation_id')
            print(f"Conversa iniciada: {self.conversation_id}")
        return result

    def send_message(self, message):
        if not self.conversation_id:
            self.start_conversation()
        
        result = self._make_request(
            'post',
            '/api/chat',
            json={
                'conversation_id': self.conversation_id,
                'message': message
            }
        )
        
        if result:
            print(f"\nAssistente: {result.get('response')}")
            print(f"Modelo: {result.get('metadata', {}).get('model')}")
            print(f"Tokens: {result.get('metadata', {}).get('eval_count')}")
        else:
            print("Não foi possível obter resposta")
        
        return result

def main():
    client = ChatbotClient()
    
    # Teste de conexão
    health = client._make_request('get', '/api/health')
    if health:
        print(f"Conectado ao servidor: {health}")
    else:
        print("Não foi possível conectar ao servidor")
        return
    
    client.start_conversation()
    
    while True:
        try:
            message = input("\nVocê: ")
            if message.lower() in ['sair', 'exit', 'quit']:
                break
            client.send_message(message)
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break

if __name__ == "__main__":
    main()