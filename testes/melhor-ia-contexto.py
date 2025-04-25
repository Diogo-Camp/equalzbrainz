import ollama
from typing import List, Dict, Optional, Tuple
import json
import time
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime
import hashlib

# Configurações globais
DEFAULT_DB_PATH = "chatbot_db.sqlite"
EMBEDDING_MODEL = "nomic-embed-text"  # Modelo para embeddings (rode `ollama pull nomic-embed-text` antes)

app = Flask(__name__)
CORS(app)  # Permite chamadas de outros computadores na rede

class ChatbotDatabase:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de conversas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at REAL,
                    updated_at REAL,
                    system_prompt TEXT
                )
            """)
            
            # Tabela de mensagens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp REAL,
                    embedding_id TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            # Tabela de embeddings (para RAG)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,
                    text TEXT,
                    embedding BLOB,
                    metadata TEXT
                )
            """)
            
            conn.commit()
    
    def save_conversation(self, conversation_id: str, title: str, system_prompt: str = None):
        """Salva ou atualiza uma conversa no banco de dados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Verifica se a conversa já existe
            cursor.execute("SELECT 1 FROM conversations WHERE id = ?", (conversation_id,))
            exists = cursor.fetchone()
            
            now = time.time()
            
            if exists:
                # Atualiza a conversa existente
                cursor.execute("""
                    UPDATE conversations 
                    SET title = ?, updated_at = ?, system_prompt = ?
                    WHERE id = ?
                """, (title, now, system_prompt, conversation_id))
            else:
                # Cria uma nova conversa
                cursor.execute("""
                    INSERT INTO conversations (id, title, created_at, updated_at, system_prompt)
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, title, now, now, system_prompt))
            
            conn.commit()
    
    def save_message(self, message: Dict):
        """Salva uma mensagem no banco de dados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO messages (id, conversation_id, role, content, timestamp, embedding_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message['id'],
                message['conversation_id'],
                message['role'],
                message['content'],
                message['timestamp'],
                message.get('embedding_id')
            ))
            
            conn.commit()
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Recupera as mensagens de uma conversa"""
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
    
    def search_similar_messages(self, query: str, conversation_id: str, limit: int = 3) -> List[Dict]:
        """Busca mensagens similares usando RAG (implementação simplificada)"""
        # Gera embedding da query
        query_embedding = self._generate_embedding(query)
        
        # Em uma implementação real, usaríamos um banco de vetores como FAISS ou Qdrant
        # Aqui vamos fazer uma busca por similaridade de texto simplificada
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT content FROM messages 
                WHERE conversation_id = ? 
                AND role IN ('user', 'assistant')
                ORDER BY timestamp DESC
                LIMIT 20
            """, (conversation_id,))
            
            messages = [dict(row) for row in cursor.fetchall()]
            
            # Classifica por similaridade (simplificado)
            messages.sort(
                key=lambda x: self._simple_similarity(query, x['content']),
                reverse=True
            )
            
            return messages[:limit]
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Gera embeddings para o texto usando Ollama"""
        # Pré-processa o texto
        text = self._preprocess_text(text)
        
        # Gera o embedding
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
        return response['embedding']
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade simplificada entre dois textos"""
        # Implementação simplificada - numa aplicação real usaríamos os embeddings
        text1 = self._preprocess_text(text1).lower()
        text2 = self._preprocess_text(text2).lower()
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        common_words = words1 & words2
        return len(common_words) / (len(words1) + 1e-9)
    
    def _preprocess_text(self, text: str) -> str:
        """Pré-processamento básico do texto"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove caracteres especiais exceto pontuação básica
        text = re.sub(r'[^\w\s.,!?]', '', text)
        # Remove espaços extras
        text = ' '.join(text.split())
        return text

class AdvancedChatbot:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db = ChatbotDatabase(db_path)
        self.active_conversation = None
        self.system_prompt = None
        
        # Configurações padrão do modelo
        self.default_configs = {
            'model': 'mistral',
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'num_ctx': 4096,
            'num_predict': 256,
            'repeat_penalty': 1.1,
            'seed': None
        }
    
    def start_new_conversation(self, title: str = "Nova Conversa", system_prompt: str = None):
        """Inicia uma nova conversa"""
        conversation_id = hashlib.sha256(f"{title}{time.time()}".encode()).hexdigest()
        self.active_conversation = conversation_id
        self.system_prompt = system_prompt
        
        self.db.save_conversation(conversation_id, title, system_prompt)
        
        if system_prompt:
            self._add_message('system', system_prompt)
        
        return conversation_id
    
    def _add_message(self, role: str, content: str, embedding_id: str = None) -> str:
        """Adiciona uma mensagem ao banco de dados"""
        if not self.active_conversation:
            raise ValueError("Nenhuma conversa ativa")
            
        message_id = hashlib.sha256(f"{role}{content}{time.time()}".encode()).hexdigest()
        
        message = {
            'id': message_id,
            'conversation_id': self.active_conversation,
            'role': role,
            'content': content,
            'timestamp': time.time(),
            'embedding_id': embedding_id
        }
        
        self.db.save_message(message)
        return message_id
    
    def generate_response(self, user_message: str, config_overrides: Dict = None) -> Dict:
        """Gera uma resposta para a mensagem do usuário com contexto"""
        if not self.active_conversation:
            self.start_new_conversation()
        
        # Pré-processa a mensagem do usuário
        processed_message = self.db._preprocess_text(user_message)
        self._add_message('user', processed_message)
        
        # Busca contexto relevante (RAG)
        relevant_context = self.db.search_similar_messages(
            processed_message, 
            self.active_conversation
        )
        
        # Prepara as configurações
        current_configs = self.default_configs.copy()
        if config_overrides:
            current_configs.update(config_overrides)
        
        # Obtém o histórico recente
        history_messages = self.db.get_conversation_messages(
            self.active_conversation,
            limit=5  # Ajuste conforme necessário
        )
        
        # Prepara o prompt com contexto
        messages = [{'role': m['role'], 'content': m['content']} for m in history_messages]
        
        # Adiciona contexto relevante se encontrado
        if relevant_context:
            context_str = "\n".join([m['content'] for m in relevant_context])
            messages.append({
                'role': 'system',
                'content': f"Contexto relevante:\n{context_str}"
            })
        
        # Adiciona a mensagem atual do usuário
        messages.append({'role': 'user', 'content': processed_message})
        
        try:
            # Chama o modelo Ollama
            response = ollama.chat(
                model=current_configs['model'],
                messages=messages,
                options={
                    k: v for k, v in current_configs.items() 
                    if k in ['temperature', 'top_p', 'top_k', 'num_ctx', 
                            'num_predict', 'repeat_penalty', 'seed']
                }
            )
            
            # Processa a resposta
            assistant_reply = response['message']['content']
            self._add_message('assistant', assistant_reply)
            
            # Atualiza o título da conversa se for a primeira resposta
            if len(history_messages) <= 1:
                self._update_conversation_title(user_message)
            
            return {
                'response': assistant_reply,
                'conversation_id': self.active_conversation,
                'metadata': {
                    'model': response['model'],
                    'response_time': response.get('total_duration'),
                    'tokens_used': response.get('eval_count'),
                    'context_tokens': response.get('prompt_eval_count'),
                    'relevant_context': [m['content'] for m in relevant_context]
                }
            }
        
        except Exception as e:
            return {
                'error': str(e),
                'response': None
            }
    
    def _update_conversation_title(self, first_message: str):
        """Atualiza o título da conversa baseado na primeira mensagem"""
        if not self.active_conversation:
            return
            
        # Gera um título resumido usando o modelo
        try:
            response = ollama.chat(
                model=self.default_configs['model'],
                messages=[{
                    'role': 'system',
                    'content': 'Gere um título muito curto (3-5 palavras) para esta conversa'
                }, {
                    'role': 'user',
                    'content': first_message[:200]  # Limita o tamanho
                }],
                options={
                    'temperature': 0.3,
                    'num_predict': 20
                }
            )
            
            title = response['message']['content'].strip('"\'')
            self.db.save_conversation(self.active_conversation, title, self.system_prompt)
        
        except:
            # Fallback para um título padrão
            title = f"Conversa {datetime.now().strftime('%Y-%m-%d')}"
            self.db.save_conversation(self.active_conversation, title, self.system_prompt)

# Inicializa o chatbot
chatbot = AdvancedChatbot()

# Rotas da API Flask
@app.route('/api/start', methods=['POST'])
def start_conversation():
    data = request.json
    conversation_id = chatbot.start_new_conversation(
        title=data.get('title', 'Nova Conversa'),
        system_prompt=data.get('system_prompt')
    )
    return jsonify({
        'conversation_id': conversation_id,
        'status': 'success'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    response = chatbot.generate_response(
        user_message=data['message'],
        config_overrides=data.get('configs')
    )
    return jsonify(response)

@app.route('/api/history', methods=['GET'])
def get_history():
    conversation_id = request.args.get('conversation_id')
    if not conversation_id:
        return jsonify({'error': 'conversation_id required'}), 400
    
    messages = chatbot.db.get_conversation_messages(conversation_id)
    return jsonify({'messages': messages})

if __name__ == "__main__":
    # Inicia a API Flask
    print("Iniciando servidor Flask na porta 5000")
    print("Acesse de outro computador usando: http://<SEU_IP>:5000/api/chat")
    app.run(host='0.0.0.0', port=5000)