import os
import sqlite3
import xml.etree.ElementTree as ET
import json
from collections import defaultdict
from datetime import datetime

def criar_banco():
    conn = sqlite3.connect('nfe.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave_emitente TEXT,
            nome_loja TEXT,
            data_emissao TEXT,
            valor_total REAL,
            UNIQUE(chave_emitente, data_emissao)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS itens_nota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nota_id INTEGER,
            nome_item TEXT,
            valor_item REAL,
            FOREIGN KEY (nota_id) REFERENCES notas_fiscais (id)
        )
    ''')

    conn.commit()
    conn.close()

def extrair_dados_nfe(caminho_xml: str) -> dict:
    tree = ET.parse(caminho_xml)
    root = tree.getroot()

    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    dados_nfe = {}

    try:
        emitente = root.find('.//nfe:emit/nfe:CNPJ', ns)
        if emitente is None:
            emitente = root.find('.//nfe:emit/nfe:CPF', ns)

        chave_emitente = emitente.text if emitente is not None else None

        nome_loja = root.find('.//nfe:emit/nfe:xNome', ns)

        data_emissao = root.find('.//nfe:ide/nfe:dhEmi', ns)
        if data_emissao is None:
            data_emissao = root.find('.//nfe:ide/nfe:dEmi', ns)

        itens = []
        for det in root.findall('.//nfe:det', ns):
            produto = det.find('nfe:prod', ns)
            if produto is not None:
                nome_item = produto.find('nfe:xProd', ns)
                valor_item = produto.find('nfe:vProd', ns)
                itens.append({
                    'nome_item': nome_item.text if nome_item is not None else None,
                    'valor_item': float(valor_item.text) if valor_item is not None else None
                })

        total = root.find('.//nfe:total/nfe:ICMSTot/nfe:vNF', ns)

        dados_nfe = {
            'chave_emitente': chave_emitente,
            'nome_loja': nome_loja.text if nome_loja is not None else None,
            'data_emissao': data_emissao.text if data_emissao is not None else None,
            'valor_total': float(total.text) if total is not None else None,
            'itens': itens
        }

    except Exception as e:
        print(f"Erro ao processar {caminho_xml}: {e}")

    return dados_nfe

def inserir_no_banco(dados_nfe: dict) -> None:
    conn = sqlite3.connect('nfe.db')
    c = conn.cursor()

    try:
        c.execute('''
            INSERT OR IGNORE INTO notas_fiscais (chave_emitente, nome_loja, data_emissao, valor_total)
            VALUES (?, ?, ?, ?)
        ''', (
            dados_nfe['chave_emitente'],
            dados_nfe['nome_loja'],
            dados_nfe['data_emissao'],
            dados_nfe['valor_total']
        ))

        c.execute('''
            SELECT id FROM notas_fiscais WHERE chave_emitente = ? AND data_emissao = ?
        ''', (dados_nfe['chave_emitente'], dados_nfe['data_emissao']))
        nota_id = c.fetchone()[0]

        for item in dados_nfe['itens']:
            c.execute('''
                INSERT INTO itens_nota (nota_id, nome_item, valor_item)
                VALUES (?, ?, ?)
            ''', (
                nota_id,
                item['nome_item'],
                item['valor_item']
            ))

        conn.commit()

    except Exception as e:
        print(f"Erro ao inserir dados no banco: {e}")

    finally:
        conn.close()

def processar_arquivo(caminho_arquivo: str) -> None:
    dados = extrair_dados_nfe(caminho_arquivo)
    if dados:
        inserir_no_banco(dados)

def processar_pasta(caminho_pasta: str) -> None:
    arquivos_xml = [f for f in os.listdir(caminho_pasta) if f.endswith('.xml')]

    if not arquivos_xml:
        print("Nenhum arquivo XML encontrado na pasta.")
        return

    for arquivo in arquivos_xml:
        caminho_arquivo = os.path.join(caminho_pasta, arquivo)
        processar_arquivo(caminho_arquivo)

def exportar_para_json(caminho_saida: str = 'exportacao_nfe.json') -> None:
    conn = sqlite3.connect('nfe.db')
    c = conn.cursor()

    c.execute('''
        SELECT n.id, n.chave_emitente, n.nome_loja, n.data_emissao, n.valor_total, i.nome_item, i.valor_item
        FROM notas_fiscais n
        LEFT JOIN itens_nota i ON n.id = i.nota_id
    ''')

    rows = c.fetchall()

    notas = defaultdict(lambda: {"itens": []})

    for row in rows:
        nota_id, chave_emitente, nome_loja, data_emissao, valor_total, nome_item, valor_item = row

        nota = notas[nota_id]
        nota['chave_emitente'] = chave_emitente
        nota['nome_loja'] = nome_loja
        nota['data_emissao'] = data_emissao
        nota['valor_total'] = valor_total

        if nome_item:
            nota['itens'].append({"nome_item": nome_item, "valor_item": valor_item})

    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(list(notas.values()), f, indent=4, ensure_ascii=False)

    conn.close()
    print(f"Exportação concluída para {caminho_saida}")

def consultar_por_cnpj(cnpj: str) -> None:
    conn = sqlite3.connect('nfe.db')
    c = conn.cursor()

    c.execute('''
        SELECT id, nome_loja, data_emissao, valor_total
        FROM notas_fiscais
        WHERE chave_emitente = ?
    ''', (cnpj,))

    resultados = c.fetchall()

    if resultados:
        print(f"Notas encontradas para CNPJ {cnpj}:")
        for r in resultados:
            print(f"ID: {r[0]} | Loja: {r[1]} | Data: {r[2]} | Valor: {r[3]}")
    else:
        print("Nenhuma nota encontrada para esse CNPJ.")

    conn.close()

def menu_interativo() -> None:
    criar_banco()

    while True:
        print("\nMenu:")
        print("1 - Processar um arquivo XML")
        print("2 - Processar uma pasta de XMLs")
        print("3 - Consultar notas por CPF/CNPJ")
        print("4 - Exportar banco para JSON")
        print("5 - Sair")

        escolha = input("Escolha uma opção (1/2/3/4/5): ")

        if escolha == '1':
            caminho = input("Informe o caminho completo do arquivo XML: ").strip()
            if os.path.isfile(caminho) and caminho.endswith('.xml'):
                processar_arquivo(caminho)
                print("Arquivo processado com sucesso!")
            else:
                print("Arquivo inválido. Tente novamente.")

        elif escolha == '2':
            while True:
                caminho = input("Informe o caminho completo da pasta: ").strip()
                if os.path.isdir(caminho):
                    arquivos_xml = [f for f in os.listdir(caminho) if f.endswith('.xml')]
                    if arquivos_xml:
                        processar_pasta(caminho)
                        print("Pasta processada com sucesso!")
                        break
                    else:
                        print("Nenhum arquivo XML encontrado na pasta. Tente outra pasta.")
                else:
                    print("Pasta inválida. Tente novamente.")

        elif escolha == '3':
            cnpj = input("Informe o CPF/CNPJ para consulta: ").strip()
            consultar_por_cnpj(cnpj)

        elif escolha == '4':
            exportar_para_json()

        elif escolha == '5':
            print("Saindo do programa. Obrigado!")
            break

        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    menu_interativo()
