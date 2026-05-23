import streamlit as st
import sqlite3
import os

# 1. CONEXÃO SEGURA
DB_PATH = "casa_espirita.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY, nome TEXT)")
    conn.commit()
    conn.close()

init_db()

# 2. LOGIN SIMPLIFICADO
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "eduardo" and pwd == "12345":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Login ou Senha incorretos")
else:
    # 3. MÓDULO DE ALUNOS (TESTE DE FUNCIONAMENTO)
    st.title("🎓 Gestão de Alunos")
    
    # Cadastro
    nome_novo = st.text_input("Nome do Aluno")
    if st.button("Adicionar Aluno"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO alunos (nome) VALUES (?)", (nome_novo,))
        conn.commit()
        conn.close()
        st.rerun()

    # Listagem com Exclusão (A parte que estava travando)
    st.divider()
    conn = sqlite3.connect(DB_PATH)
    alunos = conn.execute("SELECT id, nome FROM alunos").fetchall()
    conn.close()

    for id_aluno, nome in alunos:
        col1, col2 = st.columns([3, 1])
        col1.write(f"👤 {nome}")
        if col2.button("🗑️ Excluir", key=f"del_{id_aluno}"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM alunos WHERE id = ?", (id_aluno,))
            conn.commit()
            conn.close()
            st.rerun()
            
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()
