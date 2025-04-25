from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from ollama_wrapper import OllamaWrapper
import hashlib
import time
import sqlite3

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# Configurações
DB_PATH = "../../../Documents/falta_pasta/falta_pasta/porjeto/chatbot.db"
ollama = OllamaWrapper()

# Banco de dados simplificado
def init_db():
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

init_db()

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Dados inválidos"}), 400

        # Cria ID de conversa se não existir
        conversation_id = data.get('conversation_id', hashlib.sha256(str(time.time()).encode()).hexdigest())
        
        # Salva mensagem do usuário
        save_message(conversation_id, 'user', data['message'])
        
        # Obtém histórico
        history = get_conversation_history(conversation_id)
        messages = [{"role": msg[2], "content": msg[3]} for msg in history]
        messages.append({"role": "user", "content": data['message']})
        
        # Gera resposta
        response = ollama.generate_response(messages)
        
        # Salva resposta do assistente
        save_message(conversation_id, 'assistant', response)
        
        return jsonify({
            "response": response,
            "conversation_id": conversation_id
        })

    except Exception as e:
        app.logger.error(f"Erro: {str(e)}")
        return jsonify({"error": str(e)}), 500

def save_message(conversation_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
        (hashlib.sha256(f"{conversation_id}{content}{time.time()}".encode()).hexdigest(),
         conversation_id, role, content, time.time())
    )
    conn.commit()
    conn.close()

def get_conversation_history(conversation_id, limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?",
        (conversation_id, limit)
    )
    result = cursor.fetchall()
    conn.close()
    return result

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)