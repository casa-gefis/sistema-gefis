import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Sistema de Gestão Espírita", page_icon="🏠", layout="wide")

try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v9.db")
PASTA_PDFS = os.path.join(DIRETORIO_ATUAL, "termos_pdf")
os.makedirs(PASTA_PDFS, exist_ok=True)

# DETECTOR DE LOGO
CAMINHO_LOGO = None
if os.path.exists(DIRETORIO_ATUAL):
    for arquivo in os.listdir(DIRETORIO_ATUAL):
        if arquivo.lower().startswith("logo") and arquivo.lower().endswith((".png", ".jpg", ".jpeg")):
            CAMINHO_LOGO = os.path.join(DIRETORIO_ATUAL, arquivo)
            break

# ==========================================
# FUNÇÕES DE BANCO DE DADOS
# ==========================================
def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

def verificar_login(usuario, senha):
    executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)''')
    try: executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')")
    except: pass
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute("SELECT nivel FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

# GARANTIR TABELAS
executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, escala TEXT, data_admissao TEXT, status TEXT, data_saida TEXT, termo_pdf TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, data_adm TEXT, data_desligamento TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)")

# ==========================================
# MONITORAMENTO DE ACESSO
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

if st.session_state.logado:
    with st.sidebar:
        if CAMINHO_LOGO: st.image(CAMINHO_LOGO, width=150)
        st.markdown(f"👤 Olá, **{st.session_state.usuario.capitalize()}**")
        st.markdown(f"🔑 Nível: `{st.session_state.nivel.upper()}`")
        st.divider()
        opcoes = ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos / Faltas"]
        if st.session_state.nivel == "admin": opcoes.append("⚙️ Gerenciar Usuários")
        aba_selecionada = st.radio("Escolha o módulo:", opcoes)
        if st.button("Sair / Logoff", use_container_width=True):
            st.session_state.logado = False; st.rerun()

    # MÓDULOS
    if "🎙️ Palestrantes" in aba_selecionada:
        st.title("🎙️ Palestrantes")
        # (Sua lógica de palestrantes aqui)
        
    elif "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        with st.expander("➕ Matricular Novo Aluno"):
            col1, col2 = st.columns(2)
            n = col1.text_input("Nome")
            t = col2.text_input("Telefone")
            c = col1.text_input("Curso")
            a = col2.text_input("Ano Início")
            adm = col1.text_input("Data Admissão")
            sai = col2.text_input("Data Desligamento")
            if st.button("Salvar Matrícula"):
                executar_query("INSERT INTO alunos (nome, telefone, curso, ano_inicio, data_adm, data_desligamento, status) VALUES (?,?,?,?,?,?,?)", (n,t,c,a,adm,sai,'Ativo'))
                st.rerun()
        
        st.subheader("📋 Lista de Alunos")
        for id_a, nome, curso in executar_query("SELECT id, nome, curso FROM alunos", retornar_dados=True):
            c1, c2 = st.columns([4, 1])
            c1.write(f"👤 **{nome}** - {curso}")
            if c2.button("🗑️ Excluir", key=f"del_{id_a}"):
                executar_query("DELETE FROM alunos WHERE id=?", (id_a,))
                st.rerun()

    elif "⚙️ Gerenciar Usuários" in aba_selecionada:
        st.title("⚙️ Gerenciar Usuários")

else:
    # TELA DE LOGIN
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if CAMINHO_LOGO: st.image(CAMINHO_LOGO, width=280)
        with st.form("login"):
            u = st.text_input("Usuário").strip().lower()
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                nivel = verificar_login(u, s)
                if nivel:
                    st.session_state.logado = True; st.session_state.usuario = u; st.session_state.nivel = nivel
                    st.rerun()
                else: st.error("Dados incorretos")
