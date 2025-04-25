import uuid
class Sessao:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.modelo = "llama3"
        self.personalidade = "default"
        self.historico = []

    def to_dict(self):
        return {
            "id": self.id,
            "modelo": self.modelo,
            "personalidade": self.personalidade,
            "historico": self.historico
        }

    def carregar(self, dados):
        self.id = dados["id"]
        self.modelo = dados["modelo"]
        self.personalidade = dados["personalidade"]
        self.historico = dados["historico"]
