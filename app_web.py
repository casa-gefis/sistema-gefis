import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO DE DADOS
# ==========================================
st.set_page_config(page_title="Gestão Espírita", layout="wide")
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v11.db")

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Garantir tabelas
executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT)''')
executar_query('''INSERT OR IGNORE INTO usuarios (usuario, senha) VALUES ('eduardo', '12345')''')
executar_query('''CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY, nome TEXT, tema TEXT, contato TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY, nome TEXT, funcao TEXT, whatsapp TEXT, endereco TEXT, adm TEXT, saida TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY, nome TEXT, tel TEXT, curso TEXT, ano TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS presenca (id INTEGER PRIMARY KEY, aluno_id INTEGER, data TEXT, tema TEXT, status TEXT)''')

# ==========================================
# INTERFACE E LOGIN
# ==========================================
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = executar_query("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if user: 
            st.session_state.logado = True
            st.rerun()
        else: st.error("Dados incorretos!")
else:
    with st.sidebar:
        aba = st.radio("Módulos:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
        if st.button("Sair"): st.session_state.logado = False; st.rerun()

    # --- PALESTRANTES ---
    if aba == "🎙️ Palestrantes":
        st.title("🎙️ Palestrantes")
        busca = st.text_input("🔍 Pesquisar...")
        with st.expander("➕ Novo"):
            n = st.text_input("Nome"); t = st.text_input("Tema"); c = st.text_input("Contato")
            if st.button("Salvar"): executar_query("INSERT INTO palestrantes (nome, tema, contato) VALUES (?,?,?)", (n, t, c))
        dados = executar_query("SELECT nome, tema, contato FROM palestrantes WHERE nome LIKE ?", (f"%{busca}%",), True)
        st.table(dados)

    # --- TRABALHADORES ---
    elif aba == "👥 Trabalhadores":
        st.title("👥 Trabalhadores")
        busca = st.text_input("🔍 Pesquisar trabalhador...")
        with st.expander("➕ Novo Cadastro"):
            col1, col2 = st.columns(2)
            n = col1.text_input("Nome"); w = col2.text_input("WhatsApp")
            end = st.text_input("Endereço")
            adm = col1.text_input("Data Admissão (DD/MM/AAAA)")
            sai = col2.text_input("Data Desligamento")
            if st.button("Salvar Trabalhador"):
                executar_query("INSERT INTO trabalhadores (nome, whatsapp, endereco, adm, saida) VALUES (?,?,?,?,?)", (n, w, end, adm, sai))
        dados = executar_query("SELECT nome, whatsapp, endereco, adm FROM trabalhadores WHERE nome LIKE ?", (f"%{busca}%",), True)
        st.table(dados)

    # --- ALUNOS ---
    elif aba == "🎓 Alunos":
        st.title("🎓 Gestão de Alunos")
        busca = st.text_input("🔍 Pesquisar aluno...")
        with st.expander("➕ Novo"):
            n = st.text_input("Nome"); t = st.text_input("Contato")
            c = st.text_input("Curso"); a = st.text_input("Ano de Início")
            if st.button("Salvar"): executar_query("INSERT INTO alunos (nome, tel, curso, ano) VALUES (?,?,?,?)", (n, t, c, a))
        dados = executar_query("SELECT nome, curso, ano FROM alunos WHERE nome LIKE ?", (f"%{busca}%",), True)
        st.table(dados)

    # --- CHAMADA ---
    elif aba == "✅ Chamada":
        st.title("✅ Chamada e Tema")
        data = st.date_input("Data"); tema = st.text_input("Tema Estudado")
        alunos = executar_query("SELECT id, nome FROM alunos", retornar_dados=True)
        for id_a, n in alunos:
            col1, col2 = st.columns([3, 1])
            col1.write(n)
            pres = col2.radio("Status", ["Presente", "Falta"], key=f"p_{id_a}", horizontal=True)
            if st.button(f"Salvar {n}"):
                executar_query("INSERT INTO presenca (aluno_id, data, tema, status) VALUES (?,?,?,?)", (id_a, str(data), tema, pres))
