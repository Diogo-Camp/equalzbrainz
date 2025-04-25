import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import pickle


class FaissMemory:
    def __init__(self, model_name="all-MiniLM-L6-v2", index_path="dados/faiss_index.index",
                 meta_path="dados/faiss_metadata.pkl"):
        """
        Inicializa o gerenciador de memória Faiss.

        :param model_name: Nome do modelo SentenceTransformer a ser utilizado.
        :param index_path: Caminho para o arquivo do índice Faiss.
        :param meta_path: Caminho para o arquivo de metadados.
        """
        self.encoder = SentenceTransformer(model_name)
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = None
        self.metadata = []

        self._load_if_exists()

    def _load_if_exists(self):
        """Carrega o índice e metadados se os arquivos existirem."""
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.load()
        else:
            self._init_new_index()

    def _init_new_index(self):
        """Inicializa um novo índice Faiss se não houver um existente."""
        # Verifique se a dimensão (384) está correta para o modelo escolhido
        self.index = faiss.IndexFlatL2(self.encoder.get_max_seq_length())  # Utilize a dimensão do modelo
        self.metadata = []

    def add_memory(self, texto, info_extra=None):
        """
        Adiciona um novo texto à memória com informações extras opcionais.

        :param texto: Texto a ser encodeado e adicionado.
        :param info_extra: Dicionário com informações extras (opcional).
        """
        vetor = self.encoder.encode([texto])[0]
        self.index.add(np.array([vetor]))
        self.metadata.append(info_extra if info_extra else {"texto": texto})
        self.save()

    def buscar_similar(self, texto, k=3):
        """
        Busca por textos similares no índice.

        :param texto: Texto de consulta.
        :param k: Número de resultados a retornar. Default=3.
        :return: Lista de metadados dos textos mais similares.
        """
        vetor = self.encoder.encode([texto])[0]
        if self.index.ntotal == 0:
            return []
        distancias, indices = self.index.search(np.array([vetor]), k)
        resultados = [self.metadata[idx] for idx in indices[0] if idx < len(self.metadata)]
        return resultados

    def save(self):
        """Salva o índice Faiss e os metadados."""
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        """Carrega o índice Faiss e os metadados."""
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, "rb") as f:
            self.metadata = pickle.load(f)