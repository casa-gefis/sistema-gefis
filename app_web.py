import os
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO
# ==========================================
st.set_page_config(page_title="Sistema de Gestão Espírita", page_icon="🏠", layout="wide")
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

# Garantir Tabelas
executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, curso TEXT, ano_inicio TEXT, data_adm TEXT, data_desligamento TEXT, status TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, tema_estudado TEXT, status TEXT)''')
# (Adicione as outras tabelas aqui conforme seu código original...)

try: executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')")
except: pass

# ==========================================
# LÓGICA DE LOGIN (Fixa no topo)
# ==========================================
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário").strip().lower()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if nivel:
            st.session_state.logado = True; st.session_state.usuario = u; st.session_state.nivel = nivel[0][0]
            st.rerun()
else:
    # --- MENU APÓS LOGIN ---
    with st.sidebar:
        aba = st.radio("Módulo:", ["🎓 Alunos", "✅ Chamada"])
        if st.button("Sair"): st.session_state.logado = False; st.rerun()

    # ALUNOS (Com sistema de exclusão por seletor)
    if aba == "🎓 Alunos":
        st.title("🎓 Gestão de Alunos")
        
        # Cadastro
        with st.expander("➕ Matricular"):
            n = st.text_input("Nome"); c = st.text_input("Curso"); ano = st.text_input("Ano Início")
            if st.button("Salvar Matrícula"):
                executar_query("INSERT INTO alunos (nome, curso, ano_inicio, status) VALUES (?,?,?, 'Ativo')", (n, c, ano))
                st.rerun()

        # Exclusão Segura
        st.subheader("🗑️ Remover Aluno")
        todos = executar_query("SELECT id, nome FROM alunos", retornar_dados=True)
        if todos:
            mapa_alunos = {f"{id_a} - {nome}": id_a for id_a, nome in todos}
            aluno_para_excluir = st.selectbox("Selecione o aluno para deletar:", list(mapa_alunos.keys()))
            if st.button("Confirmar Exclusão do Aluno"):
                executar_query("DELETE FROM alunos WHERE id=?", (mapa_alunos[aluno_para_excluir],))
                st.rerun()
        
        # Listagem
        st.table(pd.DataFrame(todos, columns=["ID", "Nome"]))

    # CHAMADA
    elif aba == "✅ Chamada":
        st.title("✅ Registrar Presença")
        data_a = st.date_input("Data da Aula")
        tema = st.text_input("Tema Estudado")
        for id_a, nome in executar_query("SELECT id, nome FROM alunos", retornar_dados=True):
            col1, col2 = st.columns([3, 1])
            col1.write(nome)
            if col2.button("Presente", key=f"p_{id_a}"):
                executar_query("INSERT INTO presenca_alunos (aluno_id, data_aula, tema_estudado, status) VALUES (?,?,?,?)", (id_a, str(data_a), tema, 'Presente'))
                st.success("Gravado")
