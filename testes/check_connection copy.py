import requests

res = requests.post("http://192.168.0.36:5000/api/chat", json={"pergunta": "Qual é a capital do Japão?"})
print(res.json()['resposta'])
