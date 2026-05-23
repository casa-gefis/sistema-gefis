import streamlit as st
import sqlite3
import os

# 1. Configuração da página (DEVE SER A PRIMEIRA COISA)
st.set_page_config(page_title="Gestão Espírita", layout="wide")

# 2. Inicialização do estado (O erro ocorria aqui porque vinha antes ou fora de ordem)
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.nivel = ""

# 3. Conexão com Banco
CAMINHO_BANCO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "casa_espirita_v12.db")

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Garantir tabelas
executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)''')
executar_query('''INSERT OR IGNORE INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')''')
executar_query('''CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY, nome TEXT, casa_origem TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS palestras (id INTEGER PRIMARY KEY, palestrante_id INTEGER, data TEXT, tema TEXT)''')

# 4. Interface
if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        usuario_db = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if usuario_db:
            st.session_state.logado = True
            st.session_state.nivel = usuario_db[0][0]
            st.rerun()
        else:
            st.error("Dados incorretos!")
else:
    with st.sidebar:
        st.write(f"🔑 Nível: {str(st.session_state.nivel).upper()}")
        aba = st.radio("Módulos:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
        if st.button("Sair"):
            st.session_state.logado = False
            st.session_state.nivel = ""
            st.rerun()

    if aba == "🎙️ Palestrantes":
        st.title("🎙️ Agenda de Palestras")
        busca = st.text_input("🔍 Pesquisar por nome...")
        
        # Área administrativa
        if st.session_state.nivel == 'admin':
            with st.expander("➕ Agendar Nova Palestra"):
                nome = st.text_input("Nome do Palestrante")
                casa = st.text_input("Casa de Origem")
                data = st.date_input("Data da Palestra")
                tema = st.text_input("Tema")
                if st.button("Salvar Palestra"):
                    executar_query("INSERT OR IGNORE INTO palestrantes (nome, casa_origem) VALUES (?,?)", (nome, casa))
                    p_id = executar_query("SELECT id FROM palestrantes WHERE nome=?", (nome,), True)[0][0]
                    executar_query("INSERT INTO palestras (palestrante_id, data, tema) VALUES (?,?,?)", (p_id, str(data), tema))
                    st.success("Palestra registrada!")

        # Exibição
        query = """SELECT p.nome, pl.data, pl.tema, p.casa_origem FROM palestrantes p 
                   JOIN palestras pl ON p.id = pl.palestrante_id 
                   WHERE p.nome LIKE ? ORDER BY pl.data DESC"""
        dados = executar_query(query, (f"%{busca}%",), True)
        if dados:
            st.table(dados)
        else:
            st.info("Nenhuma palestra encontrada.")
