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

# FUNÇÕES DO BANCO
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
# Tabela Alunos Expandida
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, data_adm TEXT, data_desligamento TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)")

# MONITORAMENTO DE ACESSO
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

if not st.session_state.logado:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if CAMINHO_LOGO: st.image(CAMINHO_LOGO, width=280)
        st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema</h2>", unsafe_allow_html=True)
        with st.form(key="form_login"):
            input_usuario = st.text_input("Usuário").strip().lower()
            input_senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                nivel = verificar_login(input_usuario, input_senha)
                if nivel:
                    st.session_state.logado = True; st.session_state.usuario = input_usuario; st.session_state.nivel = nivel
                    st.rerun()
                else: st.error("Dados incorretos!")
else:
    with st.sidebar:
        if CAMINHO_LOGO: st.image(CAMINHO_LOGO, width=150)
        st.markdown(f"👤 Olá, **{st.session_state.usuario.capitalize()}**")
        aba_selecionada = st.radio("Escolha o módulo:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos / Faltas", "⚙️ Gerenciar Usuários"])
        if st.button("Sair / Logoff", use_container_width=True):
            st.session_state.logado = False; st.rerun()

    # MÓDULO ALUNOS (Adicionado campos e exclusão)
    if "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        with st.expander("➕ Matricular Novo Aluno"):
            col1, col2 = st.columns(2)
            n = col1.text_input("Nome do Aluno")
            t = col2.text_input("Telefone")
            c = col1.text_input("Curso")
            a = col2.text_input("Ano Início")
            adm = col1.text_input("Data Admissão (dd/mm/aaaa)")
            sai = col2.text_input("Data Desligamento (dd/mm/aaaa)")
            if st.button("Salvar Matrícula", type="primary"):
                executar_query("INSERT INTO alunos (nome, telefone, curso, ano_inicio, data_adm, data_desligamento, status) VALUES (?,?,?,?,?,?,?)", (n,t,c,a,adm,sai,'Ativo'))
                st.rerun()

        st.subheader("📋 Lista de Alunos")
        registros = executar_query("SELECT id, nome, curso FROM alunos", retornar_dados=True)
        if registros:
            for id_a, nome, curso in registros:
                c1, c2 = st.columns([4, 1])
                c1.write(f"👤 **{nome}** - {curso}")
                if c2.button("🗑️ Excluir", key=f"excluir_{id_a}"):
                    executar_query("DELETE FROM alunos WHERE id=?", (id_a,))
                    st.rerun()
    
    # ... (o restante dos seus módulos seguem aqui exatamente como eram)
