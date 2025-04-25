import os
import subprocess
import ollama
import json

# 🧠 Memória da conversa (carrega de arquivo se existir)
hist_path = "memory/conversa.json"
if os.path.exists(hist_path):
    with open(hist_path, "r", encoding="utf-8") as f:
        conversa = json.load(f)
else:
    conversa = [
        {
            "role": "system",
            "content": (
                "Você é um assistente com acesso ao terminal Linux. "
                "Pode executar comandos reais usando 'cmd: <comando>' "
                "ou criar arquivos usando 'file: <caminho>' seguido por 'conteúdo:'. "
                "Lembre-se do que foi feito anteriormente e responda de forma clara."
            )
        }
    ]

# 📂 Execução de comandos do terminal
def executar_comando_terminal(comando):
    try:
        resultado = subprocess.check_output(
            comando, shell=True, stderr=subprocess.STDOUT, text=True
        )
        return resultado
    except subprocess.CalledProcessError as e:
        return f"Erro ao executar: {e.output}"

# 📁 Criação de arquivos
def criar_arquivo(caminho, conteudo):
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return f"✅ Arquivo '{caminho}' criado com sucesso."
    except Exception as e:
        return f"❌ Erro ao criar arquivo: {str(e)}"

# 🔄 Loop principal
while True:
    user_input = input("\n🧽 Você: ")

    if user_input.strip().lower() in ["exit", "sair"]:
        break
    if user_input.strip().lower() == "clear":
        conversa = conversa[:1]  # Mantém apenas o system prompt
        print("\n🔍 Memória apagada. Começando do zero.")
        continue

    conversa.append({"role": "user", "content": user_input})

    # ⏳ Streaming da resposta
    print("\n🤖 Mistral: ", end="", flush=True)
    stream = ollama.chat(model='mistral:7b-instruct-q4_K_M', messages=conversa, stream=True)

    texto = ""
    for parte in stream:
        token = parte['message']['content']
        print(token, end="", flush=True)
        texto += token

    print()  # Nova linha
    conversa.append({"role": "assistant", "content": texto})

    # 📅 Criação de arquivo
    if texto.startswith("file:"):
        try:
            linhas = texto.splitlines()
            caminho = linhas[0].replace("file:", "").strip()
            idx_conteudo = next(i for i, l in enumerate(linhas) if l.startswith("conteúdo:"))
            conteudo = "\n".join(linhas[idx_conteudo + 1:])
            resultado = criar_arquivo(caminho, conteudo)
        except Exception as e:
            resultado = f"❌ Erro ao interpretar criação de arquivo: {str(e)}"

        print(f"\n📁 Resultado da criação:
{resultado}")
        conversa.append({"role": "user", "content": f"Resultado da criação:
{resultado}"})

    # 💻 Execução de comando
    elif texto.startswith("cmd:"):
        comando = texto.replace("cmd:", "").strip()
        resultado = executar_comando_terminal(comando)
        print(f"\n📊 Resultado do comando:
{resultado}")
        conversa.append({"role": "user", "content": f"Resultado do comando '{comando}':
{resultado}"})

    # 🔢 Salva memória em disco
    os.makedirs("memory", exist_ok=True)
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(conversa, f, ensure_ascii=False, indent=2)
