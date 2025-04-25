import os
import ollama
import json

# 📊 Memória local do chat
hist_path = "memory/chat_memoria.json"
os.makedirs("memory", exist_ok=True)

if os.path.exists(hist_path):
    with open(hist_path, "r", encoding="utf-8") as f:
        mensagens = json.load(f)
else:
    mensagens = [
        {"role": "system", "content": "Você é um assistente inteligente, prestativo e com memória. Responda como se fosse um humano experiente, e lembre-se das conversas passadas."}
    ]

# ✏️ Função de conversa
def conversar(usuario):
    mensagens.append({"role": "user", "content": usuario})

    stream = ollama.chat(
        model="openhermes",
        messages=mensagens,
        stream=True,
        options={
            "temperature": 0.5,
            "top_p": 0.9,
            "repeat_penalty": 1.2,
            "num_predict": 200
        }
    )

    resposta = ""
    print("\n🤖 Chatbot:", end=" ", flush=True)
    for parte in stream:
        token = parte['message']['content']
        print(token, end="", flush=True)
        resposta += token

    mensagens.append({"role": "assistant", "content": resposta})

    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(mensagens, f, ensure_ascii=False, indent=2)

# 🚀 Execução principal
if __name__ == "__main__":
    print("\n🔧 ChatGPT Local - Digite sua pergunta. (digite 'sair' para encerrar)")
    while True:
        entrada = input("\n🧽 Você: ")
        if entrada.strip().lower() in ["sair", "exit", "quit"]:
            print("\n📄 Memória salva. Até mais!")
            break
        conversar(entrada)
