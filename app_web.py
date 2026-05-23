import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO DE DADOS
# ==========================================
st.set_page_config(page_title="Sistema de Gestão Espírita", page_icon="🏠", layout="wide")

# Correção para o Streamlit Cloud
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v10.db") # Versão atualizada
PASTA_PDFS = os.path.join(DIRETORIO_ATUAL, "termos_pdf")
os.makedirs(PASTA_PDFS, exist_ok=True)

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Garante que as tabelas tenham as novas colunas
executar_query('''CREATE TABLE IF NOT EXISTS trabalhadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, 
    endereco TEXT, data_admissao TEXT, data_saida TEXT, status TEXT, termo_pdf TEXT)''')

executar_query('''CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, 
    ano_inicio TEXT, data_entrada TEXT, data_saida TEXT, status TEXT)''')

executar_query('''CREATE TABLE IF NOT EXISTS presenca_alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)''')

# ==========================================
# INTERFACE TRABALHADORES (Campos novos)
# ==========================================
# Dentro da aba Trabalhadores:
# Substitua o formulário de cadastro por este:
"""
col1, col2 = st.columns(2)
nome_trab = col1.text_input("Nome Completo")
end_trab = col2.text_input("Endereço")
tel_trab = col1.text_input("WhatsApp")
adm_trab = col2.date_input("Data de Admissão")
sai_trab = col2.date_input("Data de Desligamento", value=None)
"""

# ==========================================
# INTERFACE ALUNOS (Campos novos e Cálculo de Frequência)
# ==========================================
# Lógica para calcular porcentagem:
def calcular_frequencia(aluno_id):
    dados = executar_query("SELECT status FROM presenca_alunos WHERE aluno_id = ?", (aluno_id,), retornar_dados=True)
    if not dados: return 0
    total = len(dados)
    presentes = sum(1 for d in dados if d[0] == 'Presente')
    return (presentes / total) * 100

# Aba Alunos:
# Ao listar os alunos, adicione:
"""
st.write(f"Frequência: {calcular_frequencia(id_aluno):.1f}%")
"""
