# client.py
import requests
import json
import readline  # histórico do terminal
import os

# Configuração do endpoint do servidor
SERVIDOR_URL = "http://192.168.0.36:5000"

# Estado local
sessao = {
    "modelo": None,
    "personalidade": None,
}

def print_menu():
    print("""
    === Comandos Disponíveis ===
    /mudar_modelo        → Escolher outro modelo Ollama
    /mudar_personalidade → Trocar personalidade da IA
    /listar_modelos      → Ver modelos disponíveis
    /listar_personas     → Ver personalidades salvas
    /salvar              → Salvar a conversa atual
    /resumir             → Ver um resumo da conversa
    /carregar            → Carregar uma sessão salva
    /sair                → Finalizar e salvar
    /ajuda               → Mostrar este menu
    ============================
    Digite sua mensagem normalmente para conversar com a IA.
    """)

def enviar_pergunta(msg):
    resposta = requests.post(f"{SERVIDOR_URL}/conversar", json={"mensagem": msg})
    print("[IA]:", resposta.json().get("resposta", "(Erro ao responder)"))

def mudar_modelo():
    modelos = requests.get(f"{SERVIDOR_URL}/listar_modelos").json()["modelos"]
    print("Modelos disponíveis:", modelos)
    modelo = input("Escolha o modelo: ")
    r = requests.post(f"{SERVIDOR_URL}/mudar_modelo", json={"modelo": modelo})
    print(r.json())

def mudar_personalidade():
    personalidades = requests.get(f"{SERVIDOR_URL}/listar_personalidades").json()["personalidades"]
    print("Personalidades disponíveis:", personalidades)
    p = input("Escolha a personalidade: ")
    r = requests.post(f"{SERVIDOR_URL}/mudar_personalidade", json={"personalidade": p})
    print(r.json())

def salvar():
    r = requests.get(f"{SERVIDOR_URL}/salvar")
    print("Conversa salva como:", r.json().get("arquivo"))

def resumir():
    r = requests.get(f"{SERVIDOR_URL}/resumir")
    print("Resumo da conversa:\n", r.json().get("resumo"))

def carregar():
    arquivo = input("Nome do arquivo JSON: ")
    r = requests.post(f"{SERVIDOR_URL}/carregar", json={"arquivo": arquivo})
    print(r.json())

def sair():
    requests.get(f"{SERVIDOR_URL}/sair")

def main():
    print("Conectado ao servidor de IA ✨")
    print_menu()
    while True:
        try:
            entrada = input("Você: ").strip()
            if entrada == "":
                continue
            elif entrada.startswith("/mudar_modelo"):
                mudar_modelo()
            elif entrada.startswith("/mudar_personalidade"):
                mudar_personalidade()
            elif entrada.startswith("/listar_modelos"):
                print(requests.get(f"{SERVIDOR_URL}/listar_modelos").json())
            elif entrada.startswith("/listar_personas"):
                print(requests.get(f"{SERVIDOR_URL}/listar_personalidades").json())
            elif entrada.startswith("/salvar"):
                salvar()
            elif entrada.startswith("/resumir"):
                resumir()
            elif entrada.startswith("/carregar"):
                carregar()
            elif entrada.startswith("/sair"):
                sair()
                break
            elif entrada.startswith("/ajuda"):
                print_menu()
            else:
                enviar_pergunta(entrada)
        except KeyboardInterrupt:
            print("\nEncerrando...")
            break
        except Exception as e:
            print("Erro:", str(e))

if __name__ == '__main__':
    main()