import os
import sqlite3
import streamlit as st
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema de Gestão Espírita", page_icon="🏠", layout="wide")

# Correção para SQLite no Streamlit Cloud
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v9.db")

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# GARANTIR ESTRUTURA DAS TABELAS
executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, data_admissao TEXT, data_saida TEXT, status TEXT, termo_pdf TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, curso TEXT, ano_inicio TEXT, data_adm TEXT, data_desligamento TEXT, status TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, tema_estudado TEXT, status TEXT)''')

# Admin Padrão
try: executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')")
except: pass

# LOGIN
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("Login de Acesso")
        u = st.text_input("Usuário").strip().lower()
        s = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            resultado = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
            if resultado:
                st.session_state.logado = True
                st.session_state.usuario = u
                st.session_state.nivel = resultado[0][0]
                st.rerun()
            else:
                st.error("Dados incorretos")
else:
    with st.sidebar:
        st.write(f"Usuário: {st.session_state.usuario}")
        aba = st.radio("Módulo:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
        if st.button("Sair"): st.session_state.logado = False; st.rerun()

    # MÓDULO ALUNOS (Com o seu formato original, apenas adicionando a deleção)
    if aba == "🎓 Alunos":
        st.title("🎓 Gestão de Alunos")
        with st.expander("Cadastrar Aluno"):
            n = st.text_input("Nome")
            c = st.text_input("Curso")
            ano = st.text_input("Ano Início")
            if st.button("Matricular"):
                executar_query("INSERT INTO alunos (nome, curso, ano_inicio, status) VALUES (?,?,?, 'Ativo')", (n,c,ano))
                st.rerun()
        
        st.subheader("Lista de Alunos")
        lista = executar_query("SELECT id, nome FROM alunos", retornar_dados=True)
        for id_aluno, nome in lista:
            c1, c2 = st.columns([4, 1])
            c1.write(f"👤 {nome}")
            if c2.button("Excluir", key=f"del_{id_aluno}"):
                executar_query("DELETE FROM alunos WHERE id=?", (id_aluno,))
                st.rerun()

    # MÓDULOS DE PALESTRANTES E TRABALHADORES (Mantendo sua lógica estável)
    elif aba == "🎙️ Palestrantes":
        st.title("🎙️ Palestrantes")
        # ... (insira aqui a sua lógica original de palestrantes)
    
    elif aba == "👥 Trabalhadores":
        st.title("👥 Trabalhadores")
        # ... (insira aqui a sua lógica original de trabalhadores)

    elif aba == "✅ Chamada":
        st.title("✅ Chamada")
        # ... (insira aqui sua lógica de chamada)
