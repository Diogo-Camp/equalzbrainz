import requests
import json

SERVIDOR_URL = "http://192.168.0.36:5000"
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


def ajustar_parametro(param, valor):
    """
    Função do CLIENTE.
    Envia para o servidor o novo valor de um parâmetro de geração (ex: temperature, top_p, etc).

    Recebe:
    - param: str (nome do parâmetro)
    - valor: float (novo valor para esse parâmetro)

    Retorna:
    - Nada (só printa a resposta do servidor)
    """
    try:
        r = requests.post(f"{SERVIDOR_URL}/ajustar_parametro", json={"param": param, "valor": valor})
        print(r.json())
    except Exception as e:
        print("[ERRO Ajuste]:", str(e))

def main():
    print_menu()
    #entrada = input("Você: ").strip()
    while True:
        try:
            entrada = input("Você: ").strip()
            if entrada.startswith("!param"):
                try:
                    _, param, valor = entrada.split()
                    ajustar_parametro(param, float(valor))
                except ValueError:
                    print("Formato incorreto! Use: !param parametro valor")
                continue

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
                    r = requests.get(f"{SERVIDOR_URL}/listar_modelos")
                    print(r.json())

                elif comando == "listar_personas":
                    r = requests.get(f"{SERVIDOR_URL}/listar_personalidades")
                    print(r.json())

                elif comando == "salvar":
                    r = requests.get(f"{SERVIDOR_URL}/salvar")
                    print(r.json())

                elif comando == "resumir":
                    r = requests.get(f"{SERVIDOR_URL}/resumir")
                    print(r.json())

                elif comando == "resetar_memoria":
                    r = requests.get(f"{SERVIDOR_URL}/resetar_memoria")
                    print(r.json())

                elif comando == "status":
                    r = requests.get(f"{SERVIDOR_URL}/status")
                    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

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
