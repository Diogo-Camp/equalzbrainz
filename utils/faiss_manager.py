# utils/faiss_manager.py
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os
import pickle

class FaissMemory:
    def __init__(self, model_name="all-MiniLM-L6-v2", index_path="dados/faiss_index.index", meta_path="dados/faiss_metadata.pkl"):
        self.encoder = SentenceTransformer(model_name)
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = None
        self.metadata = []

        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.load()
        else:
            self.index = faiss.IndexFlatL2(384)  # 384 dimensões do MiniLM
            self.metadata = []

    def add_memory(self, texto, info_extra=None):
        vetor = self.encoder.encode([texto])[0]
        self.index.add(np.array([vetor]))
        self.metadata.append(info_extra if info_extra else {"texto": texto})
        self.save()

    def buscar_similar(self, texto, k=3):
        vetor = self.encoder.encode([texto])[0]
        if self.index.ntotal == 0:
            return []
        distancias, indices = self.index.search(np.array([vetor]), k)
        resultados = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                resultados.append(self.metadata[idx])
        return resultados

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, \"wb\") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, \"rb\") as f:
            self.metadata = pickle.load(f)
