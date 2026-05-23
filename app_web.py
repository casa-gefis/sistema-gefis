import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO DE DADOS
# ==========================================
st.set_page_config(page_title="Gestão Espírita", layout="wide")

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v10.db") # Versão nova do banco

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Garantir estrutura do banco atualizada
executar_query('''CREATE TABLE IF NOT EXISTS trabalhadores (
    id INTEGER PRIMARY KEY, nome TEXT, funcao TEXT, whatsapp TEXT, 
    endereco TEXT, data_admissao TEXT, data_saida TEXT, status TEXT, termo_pdf TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, curso TEXT, 
    ano_inicio TEXT, status TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS presenca (
    id INTEGER PRIMARY KEY, aluno_id INTEGER, data_aula TEXT, 
    tema TEXT, status TEXT)''')

# ==========================================
# INTERFACE
# ==========================================
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    # (Manter sua lógica de login anterior aqui para economizar espaço)
    if st.button("Simular Login"): st.session_state.logado = True
else:
    with st.sidebar:
        aba_selecionada = st.radio("Módulos:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
    
    # --- MÓDULO TRABALHADORES ---
    if aba_selecionada == "👥 Trabalhadores":
        st.title("👥 Equipe de Trabalhadores")
        busca = st.text_input("🔍 Pesquisar trabalhador...")
        with st.expander("➕ Novo Cadastro"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome")
            wpp = col2.text_input("WhatsApp")
            end = st.text_input("Endereço")
            adm = col1.date_input("Data de Admissão")
            if st.button("Salvar Trabalhador"):
                executar_query("INSERT INTO trabalhadores (nome, whatsapp, endereco, data_admissao, status) VALUES (?,?,?,?,'Ativo')", (nome, wpp, end, str(adm)))
        
        # Exibição com busca
        query = "SELECT nome, whatsapp, endereco, status FROM trabalhadores WHERE nome LIKE ?"
        dados = executar_query(query, (f"%{busca}%",), retornar_dados=True)
        st.table(dados)

    # --- MÓDULO ALUNOS ---
    elif aba_selecionada == "🎓 Alunos":
        st.title("🎓 Gestão de Alunos")
        busca = st.text_input("🔍 Pesquisar aluno...")
        with st.expander("➕ Matricular Aluno"):
            n = st.text_input("Nome do Aluno")
            tel = st.text_input("Contato")
            cur = st.text_input("Nome do Curso")
            ano = st.selectbox("Ano de Início", [str(i) for i in range(2020, 2030)])
            if st.button("Matricular"):
                executar_query("INSERT INTO alunos (nome, telefone, curso, ano_inicio, status) VALUES (?,?,?,?,'Ativo')", (n, tel, cur, ano))
        
        dados = executar_query("SELECT nome, curso, ano_inicio FROM alunos WHERE nome LIKE ?", (f"%{busca}%",), retornar_dados=True)
        st.table(dados)

    # --- MÓDULO CHAMADA ---
    elif aba_selecionada == "✅ Chamada":
        st.title("✅ Registro de Presença")
        data_aula = st.date_input("Data da Aula")
        tema = st.text_input("Tema Estudado")
        
        alunos = executar_query("SELECT id, nome FROM alunos", retornar_dados=True)
        for id_aluno, nome_aluno in alunos:
            col1, col2 = st.columns([3, 1])
            col1.write(nome_aluno)
            presenca = col2.radio("Status", ["Presente", "Falta"], key=f"p_{id_aluno}", horizontal=True)
            if st.button(f"Registrar {nome_aluno}"):
                executar_query("INSERT INTO presenca (aluno_id, data_aula, tema, status) VALUES (?,?,?,?)", (id_aluno, str(data_aula), tema, presenca))
