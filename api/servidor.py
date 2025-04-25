# servidor.py
import os
import json
import uuid
from flask import Flask, request, jsonify
from datetime import datetime
import subprocess

app = Flask(__name__)

# Diretórios base
CONVERSAS_DIR = "conversas_salvas"
MODELOS_DIR = "modelos_disponiveis"
PERSONALIDADES_DIR = "personalidades"

# Config inicial
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

# Estado atual da sessão
sessao = {
    "id": str(uuid.uuid4()),
    "modelo": "llama3",
    "personalidade": "default",
    "historico": []
}

# Utilitários
os.makedirs(CONVERSAS_DIR, exist_ok=True)
os.makedirs(PERSONALIDADES_DIR, exist_ok=True)
os.makedirs(MODELOS_DIR, exist_ok=True)


def carregar_modelos():
    resultado = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    linhas = resultado.stdout.strip().split("\n")[1:]
    modelos = [linha.split()[0] for linha in linhas if linha.strip()]
    return modelos


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

    mensagens = [
        {"role": "system", "content": personalidade.get("system", "")}
    ] + sessao["historico"] + [{"role": "user", "content": pergunta}]

    payload = {
        "model": sessao["modelo"],
        "messages": mensagens,
        "stream": False
    }

    try:
        resposta = requests.post(OLLAMA_ENDPOINT, json=payload)
        output = resposta.json()
        content = output.get("message", {}).get("content", "")
    except Exception as e:
        content = f"Erro ao processar resposta: {str(e)}"

    sessao["historico"].append({"role": "user", "content": pergunta})
    sessao["historico"].append({"role": "assistant", "content": content})

    return jsonify({"resposta": content})


@app.route("/mudar_modelo", methods=["POST"])
def mudar_modelo():
    modelo = request.json.get("modelo")
    if modelo in carregar_modelos():
        sessao["modelo"] = modelo
        return jsonify({"status": "ok", "modelo": modelo})
    return jsonify({"status": "erro", "mensagem": "Modelo não encontrado."})


@app.route("/mudar_personalidade", methods=["POST"])
def mudar_personalidade():
    nome = request.json.get("personalidade")
    caminho = os.path.join(PERSONALIDADES_DIR, f"{nome}.json")
    if os.path.exists(caminho):
        sessao["personalidade"] = nome
        return jsonify({"status": "ok", "personalidade": nome})
    return jsonify({"status": "erro", "mensagem": "Personalidade não encontrada."})


@app.route("/listar_modelos")
def listar_modelos():
    return jsonify({"modelos": carregar_modelos()})


@app.route("/listar_personalidades")
def listar_personalidades():
    arquivos = [f[:-5] for f in os.listdir(PERSONALIDADES_DIR) if f.endswith(".json")]
    return jsonify({"personalidades": arquivos})


@app.route("/salvar")
def salvar():
    salvar_conversa()
    return jsonify({"status": "salvo", "arquivo": f"{sessao['id']}.json"})


@app.route("/sair")
def sair():
    salvar_conversa()
    os._exit(0)


@app.route("/resumir")
def resumir():
    resumo = "\n".join([x["content"] for x in sessao["historico"] if x["role"] == "assistant"])
    return jsonify({"resumo": resumo[:1000]})


@app.route("/carregar", methods=["POST"])
def carregar():
    arquivo = request.json.get("arquivo")
    caminho = os.path.join(CONVERSAS_DIR, arquivo)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            global sessao
            sessao = json.load(f)
        return jsonify({"status": "ok", "sessao_id": sessao["id"]})
    return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado."})


