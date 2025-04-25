import ollama
from typing import List, Dict
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
import time
import re
import hashlib
import json

app = Flask(__name__)
CORS(app)

# Configurações
DEFAULT_DB_PATH = "chatbot_db.sqlite"
EMBEDDING_MODEL = "nomic-embed-text"  # Atualize se usar outro modelo

class ChatbotDatabase:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa o banco de dados simplificado"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp REAL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            conn.commit()

    def save_conversation(self, conversation_id: str, title: str):
        """Versão simplificada sem embeddings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO conversations VALUES (?, ?, ?)",
                (conversation_id, title, time.time())
            )
            conn.commit()

    def save_message(self, message: Dict):
        """Versão simplificada sem embeddings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
                (
                    message['id'],
                    message['conversation_id'],
                    message['role'],
                    message['content'],
                    message['timestamp']
                )
            )
            conn.commit()

    def get_conversation_messages(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Busca simplificada sem RAG"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (conversation_id, limit))
            return [dict(row) for row in cursor.fetchall()]

class Chatbot:
    def __init__(self):
        self.db = ChatbotDatabase()
    
    def start_conversation(self, title: str = "Nova Conversa") -> str:
        """Versão simplificada sem system prompt"""
        conversation_id = hashlib.sha256(f"{title}{time.time()}".encode()).hexdigest()
        self.db.save_conversation(conversation_id, title)
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """Adiciona mensagem sem embeddings"""
        message_id = hashlib.sha256(f"{role}{content}{time.time()}".encode()).hexdigest()
        self.db.save_message({
            'id': message_id,
            'conversation_id': conversation_id,
            'role': role,
            'content': content,
            'timestamp': time.time()
        })
    
    def generate_response(self, conversation_id: str, user_message: str) -> Dict:
        """Versão simplificada sem RAG"""
        # Adiciona mensagem do usuário
        self.add_message(conversation_id, 'user', user_message)
        
        # Obtém histórico
        history = self.db.get_conversation_messages(conversation_id)
        messages = [{'role': msg['role'], 'content': msg['content']} for msg in history]
        
        try:
            # Chama o Ollama (configurações fixas para simplificar)
            response = ollama.chat(
                model='mistral',
                messages=messages,
                options={
                    'temperature': 0.7,
                    'num_ctx': 4096
                }
            )
            
            # Salva resposta
            assistant_reply = response['message']['content']
            self.add_message(conversation_id, 'assistant', assistant_reply)
            
            return {
                'response': assistant_reply,
                'conversation_id': conversation_id,
                'metadata': {
                    'model': response['model'],
                    'tokens_used': response.get('eval_count', 0)
                }
            }
        except Exception as e:
            return {'error': str(e)}

# Rotas da API
@app.route('/')
def home():
    return "Chatbot API está rodando. Use /api/ endpoints."

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'ollama': 'running'})

@app.route('/api/start', methods=['POST'])
def start_conversation():
    chatbot = Chatbot()
    data = request.json
    conversation_id = chatbot.start_conversation(data.get('title', 'Nova Conversa'))
    return jsonify({
        'conversation_id': conversation_id,
        'status': 'success'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    chatbot = Chatbot()
    data = request.json
    
    if not data or 'message' not in data or 'conversation_id' not in data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    response = chatbot.generate_response(
        conversation_id=data['conversation_id'],
        user_message=data['message']
    )
    
    if 'error' in response:
        return jsonify(response), 500
    
    return jsonify(response)

if __name__ == "__main__":
    print("Iniciando servidor Flask...")
    print("Verifique se Ollama está rodando (ollama serve)")
    app.run(host='0.0.0.0', port=5000, threaded=True)