import requests
import json

SERVIDOR_URL = "http://localhost:5000"
modo_admin = False

def print_menu():
    print("""Comandos:
    /mudar_modelo
    /mudar_personalidade
    /listar_modelos
    /listar_personas
    /salvar
    /resumir
    /carregar
    /sair
    !admin → Ativar modo avançado
    !estado → Mostrar sessão
    """)

def enviar(msg):
    global modo_admin
    if msg.strip() == "!admin":
        modo_admin = not modo_admin
        print("🔒 Modo Admin:", "ATIVADO" if modo_admin else "DESATIVADO")
        return
    if modo_admin and msg.startswith("!estado"):
        r = requests.get(f"{SERVIDOR_URL}/admin/estado")
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
        return

    resposta = requests.post(f"{SERVIDOR_URL}/conversar", json={"mensagem": msg})
    if resposta.status_code == 200:
        print("[IA]:", resposta.json().get("resposta", "(sem resposta)"))
    else:
        print("[ERRO]:", resposta.text)

def main():
    print_menu()
    while True:
        try:
            entrada = input("Você: ").strip()
            if entrada == "":
                continue
            if entrada.startswith("/"):
                comando = entrada[1:]
                if comando == "mudar_modelo":
                    novo = input("Modelo: ")
                    r = requests.post(f"{SERVIDOR_URL}/mudar_modelo", json={"modelo": novo})
                    print(r.json())
                elif comando == "mudar_personalidade":
                    novo = input("Personalidade: ")
                    r = requests.post(f"{SERVIDOR_URL}/mudar_personalidade", json={"personalidade": novo})
                    print(r.json())
                elif comando == "listar_modelos":
                    print(requests.get(f"{SERVIDOR_URL}/listar_modelos").json())
                elif comando == "listar_personas":
                    print(requests.get(f"{SERVIDOR_URL}/listar_personalidades").json())
                elif comando == "salvar":
                    print(requests.get(f"{SERVIDOR_URL}/salvar").json())
                elif comando == "resumir":
                    print(requests.get(f"{SERVIDOR_URL}/resumir").json())
                elif comando == "sair":
                    print("Encerrando sessão...")
                    requests.get(f"{SERVIDOR_URL}/sair")
                    break
            else:
                enviar(entrada)
        except KeyboardInterrupt:
            print("\\nFinalizando.")
            break
        except Exception as e:
            print("[ERRO Client]:", str(e))

if __name__ == '__main__':
    main()
