import requests
import json
import time
import os
from typing import Dict, Optional

class ChatbotClient:
    def __init__(self, base_url: str = "http://192.168.0.36:5000"):
        self.base_url = base_url
        self.current_conversation = None
        self.configs = {
            'temperature': 0.7,
            'max_tokens': 256,
            'context_window': 4096
        }
    
    def start_new_chat(self, system_prompt: str = None):
        """Inicia uma nova conversa"""
        response = requests.post(
            f"{self.base_url}/api/start",
            json={
                'title': input("Título da conversa: "),
                'system_prompt': system_prompt
            }
        )
        self.current_conversation = response.json()['conversation_id']
        print(f"\nNova conversa iniciada (ID: {self.current_conversation})")
    
    def send_message(self, message: str):
        """Envia mensagem e mostra resposta em streaming"""
        start_time = time.time()
        
        # Configura a requisição com streaming
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                'message': message,
                'configs': self.configs,
                'stream': True  # Habilita streaming
            },
            stream=True
        )
        
        # Processa a resposta em streaming
        print("\nAssistente: ", end='', flush=True)
        full_response = ""
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data:'):
                    chunk = json.loads(decoded_line[5:])
                    if 'response' in chunk:
                        print(chunk['response'], end='', flush=True)
                        full_response += chunk['response']
        
        # Calcula estatísticas
        response_time = time.time() - start_time
        tokens = len(full_response.split())  # Aproximação
        
        print(f"\n\n[Stats: {response_time:.2f}s | ~{tokens} tokens]")
        return full_response
    
    def adjust_settings(self):
        """Menu para ajustar configurações"""
        print("\nConfigurações Atuais:")
        for k, v in self.configs.items():
            print(f"{k}: {v}")
        
        print("\nOpções:")
        print("1. Ajustar temperatura (0.1-1.0)")
        print("2. Ajustar máximo de tokens (50-2048)")
        print("3. Voltar")
        
        choice = input("Escolha: ")
        
        if choice == "1":
            new_temp = float(input("Nova temperatura (0.1-1.0): "))
            self.configs['temperature'] = max(0.1, min(1.0, new_temp))
        elif choice == "2":
            new_tokens = int(input("Novo máximo de tokens (50-2048): "))
            self.configs['max_tokens'] = max(50, min(2048, new_tokens))
    
    def interactive_loop(self):
        """Loop interativo principal"""
        print("Bem-vindo ao Chatbot CLI")
        self.start_new_chat()
        
        while True:
            try:
                print("\nOpções:")
                print("1. Enviar mensagem")
                print("2. Ajustar configurações")
                print("3. Nova conversa")
                print("4. Sair")
                
                choice = input("Escolha: ")
                
                if choice == "1":
                    message = input("\nVocê: ")
                    if message.lower() == '/quit':
                        break
                    self.send_message(message)
                elif choice == "2":
                    self.adjust_settings()
                elif choice == "3":
                    self.start_new_chat()
                elif choice == "4":
                    break
                else:
                    print("Opção inválida")
            
            except KeyboardInterrupt:
                print("\nSaindo...")
                break
            except Exception as e:
                print(f"Erro: {e}")

if __name__ == "__main__":
    # Verifica se a API está rodando
    try:
        client = ChatbotClient()
        print("Conectando à API...")
        
        # Testa a conexão
        requests.get(f"{client.base_url}/api/health", timeout=2)
        
        # Inicia o loop interativo
        client.interactive_loop()
    
    except requests.ConnectionError:
        print("Erro: API não encontrada. Certifique-se que o servidor Flask está rodando.")
    except Exception as e:
        print(f"Erro inesperado: {e}")