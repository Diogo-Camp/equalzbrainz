from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from ollama_wrapper import OllamaWrapper
import hashlib
import time
import sqlite3
from typing import Optional, List, Dict

app = Flask(__name__)
CORS(app)

# Configuração de logs
logging.basicConfig(level=logging.DEBUG)
app.logger = logging.getLogger(__name__)

# Configurações
DB_PATH = "../../../Documents/falta_pasta/falta_pasta/porjeto/chatbot.db"
ollama = OllamaWrapper()

# Banco de dados
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp REAL
            )
        """)
        conn.commit()
        conn.close()
        app.logger.info("Banco de dados inicializado")
    except Exception as e:
        app.logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise

init_db()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "ollama": "running",
        "database": "ok"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        app.logger.debug(f"Dados recebidos: {data}")
        
        if not data or 'message' not in data:
            return jsonify({"error": "Formato inválido, envie {'message': 'texto'}"}), 400

        # Gerenciamento de conversa
        conversation_id = data.get('conversation_id') or hashlib.sha256(str(time.time()).encode()).hexdigest()
        
        # Salva mensagem do usuário
        save_message(conversation_id, 'user', data['message'])
        
        # Obtém histórico
        history = get_conversation_history(conversation_id)
        messages = prepare_messages(history, data['message'])
        
        # Gera resposta
        response = ollama.generate_response(messages)
        
        # Salva resposta do assistente
        save_message(conversation_id, 'assistant', response)
        
        return jsonify({
            "response": response,
            "conversation_id": conversation_id
        })

    except Exception as e:
        app.logger.error(f"Erro no endpoint /api/chat: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "details": "Consulte os logs do servidor para mais informações"
        }), 500

def save_message(conversation_id: str, role: str, content: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
            (
                hashlib.sha256(f"{conversation_id}{content}{time.time()}".encode()).hexdigest(),
                conversation_id,
                role,
                content,
                time.time()
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        app.logger.error(f"Erro ao salvar mensagem: {str(e)}")
        raise

def get_conversation_history(conversation_id: str, limit: int = 5) -> List[tuple]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?",
            (conversation_id, limit)
        )
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        app.logger.error(f"Erro ao obter histórico: {str(e)}")
        return []

def prepare_messages(history: List[tuple], new_message: str) -> List[Dict]:
    """Prepara o contexto para o Ollama"""
    messages = []
    
    # Adiciona histórico (ordem reversa)
    for msg in reversed(history):
        messages.append({
            "role": msg[2],  # role
            "content": msg[3]  # content
        })
    
    # Adiciona nova mensagem
    messages.append({"role": "user", "content": new_message})
    
    return messages

if __name__ == "__main__":
    try:
        app.logger.info("Iniciando servidor...")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        app.logger.critical(f"Falha ao iniciar servidor: {str(e)}")
        raise
