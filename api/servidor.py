# servidor.py
import os
import json
import uuid
from flask import Flask, request, jsonify
import subprocess
import requests

app = Flask(__name__)

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSAS_DIR = os.path.join(BASE_DIR, "..", "dados", "conversas_salvas")
PERSONALIDADES_DIR = os.path.join(BASE_DIR, "..", "dados", "personalidades")

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

sessao = {
    "id": str(uuid.uuid4()),
    "modelo": "llama3",
    "personalidade": "default",
    "historico": []
}

os.makedirs(CONVERSAS_DIR, exist_ok=True)
os.makedirs(PERSONALIDADES_DIR, exist_ok=True)


def carregar_modelos():
    try:
        resultado = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        linhas = resultado.stdout.strip().split("\n")[1:]
        modelos = [linha.split()[0] for linha in linhas if linha.strip()]
        return modelos
    except Exception as e:
        print(f"[ERRO] Listar modelos: {e}")
        return []


def carregar_personalidade(nome):
    caminho = os.path.join(PERSONALIDADES_DIR, f"{nome}.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"system": "Você é um assistente útil."}


def salvar_conversa():
    caminho = os.path.join(CONVERSAS_DIR, f"{sessao['id']}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(sessao, f, indent=2, ensure_ascii=False)


@app.route("/conversar", methods=["POST"])
def conversar():
    data = request.json
    pergunta = data.get("mensagem", "")
    personalidade = carregar_personalidade(sessao["personalidade"])

    prompt = f"{personalidade.get('system', '')}\nUsuário: {pergunta}\nAssistente:"

    payload = {
        "model": sessao["modelo"],
        "prompt": prompt,
        "stream": False
    }

    try:
        resposta = requests.post(OLLAMA_ENDPOINT, json=payload)
        output = resposta.json()
        content = output.get("response", "[ERRO] Sem resposta.")
    except Exception as e:
        content = f"[ERRO] Ollama: {str(e)}"

    sessao["historico"].append({"role": "user", "content": pergunta})
    sessao["historico"].append({"role": "assistant", "content": content})

    return jsonify({"resposta": content})


@app.route("/mudar_modelo", methods=["POST"])
def mudar_modelo():
    modelo = request.json.get("modelo")
    modelos = carregar_modelos()

    if modelo not in modelos:
        print(f"[INFO] Baixando novo modelo: {modelo}")
        resultado = subprocess.run(["ollama", "pull", modelo], capture_output=True, text=True)
        if resultado.returncode != 0:
            return jsonify({"status": "erro", "mensagem": "Falha ao puxar modelo."})

    sessao["modelo"] = modelo
    return jsonify({"status": "ok", "modelo": modelo})


@app.route("/listar_modelos")
def listar_modelos():
    return jsonify({"modelos": carregar_modelos()})


@app.route("/mudar_personalidade", methods=["POST"])
def mudar_personalidade():
    nome = request.json.get("personalidade")
    if os.path.exists(os.path.join(PERSONALIDADES_DIR, f"{nome}.json")):
        sessao["personalidade"] = nome
        return jsonify({"status": "ok", "personalidade": nome})
    return jsonify({"status": "erro", "mensagem": "Personalidade não encontrada."})


@app.route("/listar_personalidades")
def listar_personalidades():
    arquivos = [f[:-5] for f in os.listdir(PERSONALIDADES_DIR) if f.endswith(".json")]
    return jsonify({"personalidades": arquivos})


@app.route("/salvar")
def salvar():
    salvar_conversa()
    return jsonify({"status": "salvo", "arquivo": f"{sessao['id']}.json"})


@app.route("/resumir")
def resumir():
    resumo = "\n".join([x["content"] for x in sessao["historico"] if x["role"] == "assistant"])
    return jsonify({"resumo": resumo[:1000]})


@app.route("/sair")
def sair():
    salvar_conversa()
    os._exit(0)


# 🛡️ Admin secreta
@app.route("/admin/estado")
def estado():
    return jsonify(sessao)
