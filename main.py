from api.servidor1 import app, carregar_modelos

if __name__ == '__main__':
    print("""🔧 FusionIA Server Inicializando...
================================
Modelos encontrados:
""")
    for m in carregar_modelos():
        print(f" - {m}")
    print("""
Aguardando conexões em http://localhost:5000
================================
""")
    app.run(host="0.0.0.0", port=5000, debug=True)