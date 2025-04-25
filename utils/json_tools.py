import json

def salvar_json(path, dados):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def carregar_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
