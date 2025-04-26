# servidor_ia.py (versão corrigida e ampliada)

import os
import json
import uuid
from flask import Flask, request, jsonify
import subprocess
import requests
import time
from utils.faiss_manager import FaissMemory

# Inicializações
app = Flask(__name__)

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONVERSAS_DIR = os.path.join(BASE_DIR, "..", "dados", "conversas_salvas")
PERSONALIDADES_DIR = os.path.join(BASE_DIR, "..", "dados", "personalidades")

# Endpoints
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

# Sessão atual
sessao = {
    "id": str(uuid.uuid4()),
    "modelo": None,
    "personalidade": None,
    "historico": []
}

# Configurações do servidor
sessao_config = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 50,
    "repeat_penalty": 1.1,
    "num_predict": 400,
    "max_historico": 10
}

# Instâncias de memória
memoria = FaissMemory()
modo_admin = False

# Garantir diretórios
os.makedirs(CONVERSAS_DIR, exist_ok=True)
os.makedirs(PERSONALIDADES_DIR, exist_ok=True)

# Funções auxiliares

def carregar_modelos():
    """Retorna uma lista de modelos locais disponíveis."""
    try:
        resultado = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        linhas = resultado.stdout.strip().split("\n")[1:]
        modelos = [linha.split()[0] for linha in linhas if linha.strip()]
        return modelos
    except Exception as e:
        print(f"[ERRO] Listar modelos: {e}")
        return []

def carregar_personalidade(nome):
    """Carrega uma personalidade do diretório. Se não existir, carrega padrão."""
    caminho = os.path.join(PERSONALIDADES_DIR, f"{nome}.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"system": "Você é um assistente útil."}

def salvar_conversa():
    """Salva o histórico atual em arquivo JSON."""
    caminho = os.path.join(CONVERSAS_DIR, f"{sessao['id']}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(sessao, f, indent=2, ensure_ascii=False)

# Rotas principais

@app.route("/conversar", methods=["POST"])
def conversar():
    """Recebe uma pergunta e retorna resposta gerada pela IA."""
    global modo_admin
    data = request.json
    pergunta = data.get("mensagem", "")

    similares = memoria.buscar_similar(pergunta, k=3)
    memoria_injetada = "\n".join([s.get("texto", "") for s in similares])

    personalidade = carregar_personalidade(sessao.get("personalidade", "default"))
    prompt = f"""{personalidade.get('system', 'Você é um assistente útil.')}
        Contexto relevante: {memoria_injetada},
        Usuário: {pergunta},
        Assistente:
    """
    payload = {
        "model": sessao["modelo"],
        "prompt": prompt,
        "stream": False,
        "temperature": sessao_config["temperature"],
        "top_p": sessao_config["top_p"],
        "top_k": sessao_config["top_k"],
        "repeat_penalty": sessao_config["repeat_penalty"],
        "num_predict": sessao_config["num_predict"]
    }

    inicio = time.time()
    try:
        resposta = requests.post(OLLAMA_ENDPOINT, json=payload)
        output = resposta.json()
        content = output.get("response") or output.get("message", {}).get("content", "[ERRO] Resposta inesperada.")
    except Exception as e:
        content = f"[ERRO] Falha no processamento: {str(e)}"

    fim = time.time()

    sessao["historico"].append({"role": "user", "content": pergunta})
    sessao["historico"].append({"role": "assistant", "content": content})

    if len(sessao["historico"]) > sessao_config["max_historico"] * 2:
        sessao["historico"] = sessao["historico"][-(sessao_config["max_historico"] * 2):]

    memoria.add_memory(f"Usuário: {pergunta} | IA: {content}")

    if modo_admin:
        print(f"[DEBUG] Tokens estimados: {len(prompt.split())}")
        print(f"[DEBUG] Tempo resposta: {fim - inicio:.2f}s")

    return jsonify({"resposta": content})

@app.route("/mudar_modelo", methods=["POST"])
def mudar_modelo():
    """Permite mudar para outro modelo já disponível localmente."""
    modelo = request.json.get("modelo")
    modelos = carregar_modelos()
    if modelo in modelos:
        sessao["modelo"] = modelo
        return jsonify({"status": "ok", "modelo": modelo})
    return jsonify({"status": "erro", "mensagem": "Modelo não encontrado localmente."})

@app.route("/mudar_personalidade", methods=["POST"])
def mudar_personalidade():
    """Muda para outra personalidade disponível."""
    nome = request.json.get("personalidade")
    if os.path.exists(os.path.join(PERSONALIDADES_DIR, f"{nome}.json")):
        sessao["personalidade"] = nome
        return jsonify({"status": "ok", "personalidade": nome})
    return jsonify({"status": "erro", "mensagem": "Personalidade não encontrada."})

@app.route("/listar_modelos")
def listar_modelos():
    """Lista os modelos locais disponíveis."""
    return jsonify({"modelos": carregar_modelos()})

@app.route("/listar_personalidades")
def listar_personalidades():
    """Lista personalidades disponíveis."""
    arquivos = [f[:-5] for f in os.listdir(PERSONALIDADES_DIR) if f.endswith(".json")]
    return jsonify({"personalidades": arquivos})

@app.route("/ajustar_parametro", methods=["POST"])
def ajustar_parametro():
    """Ajusta parâmetros como temperature, top_p, etc."""
    data = request.json
    param = data.get("param")
    valor = data.get("valor")
    if param in sessao_config:
        sessao_config[param] = valor
        return jsonify({"status": "ok", "param": param, "valor": valor})
    return jsonify({"status": "erro", "mensagem": "Parâmetro inválido."})

@app.route("/resetar_memoria", methods=["GET"])
def resetar_memoria():
    """Reseta o histórico da conversa atual."""
    sessao["historico"] = []
    memoria.reset()
    return jsonify({"status": "ok", "mensagem": "Histórico resetado."})

@app.route("/status", methods=["GET"])
def status():
    """Exibe o status atual da sessão."""
    return jsonify({
        "modelo": sessao.get("modelo"),
        "personalidade": sessao.get("personalidade"),
        "historico_mensagens": len(sessao.get("historico", [])),
        "parametros": sessao_config
    })

@app.route("/salvar")
def salvar():
    """Salva a sessão atual."""
    salvar_conversa()
    return jsonify({"status": "salvo", "arquivo": f"{sessao['id']}.json"})

@app.route("/resumir")
def resumir():
    """Gera um resumo da conversa atual."""
    resumo = "\n".join([x["content"] for x in sessao["historico"] if x["role"] == "assistant"])
    return jsonify({"resumo": resumo[:1000]})

@app.route("/sair")
def sair():
    """Salva e encerra a aplicação manualmente."""
    salvar_conversa()
    return jsonify({"mensagem": "Sessão salva. Use CTRL+C para sair."})