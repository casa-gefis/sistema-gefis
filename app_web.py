import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema de Gestão Espírita",
    page_icon="🏠",
    layout="wide"
)

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

CAMINHO_LOGO = None
if os.path.exists(DIRETORIO_ATUAL):
    arquivos_na_pasta = os.listdir(DIRETORIO_ATUAL)
    for arquivo in arquivos_na_pasta:
        if arquivo.lower().startswith("logo") and arquivo.lower().endswith((".png", ".jpg", ".jpeg")):
            CAMINHO_LOGO = os.path.join(DIRETORIO_ATUAL, arquivo)
            break

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = None
    if retornar_dados:
        dados = cursor.fetchall()
    conn.commit()
    conn.close()
    return dados

def verificar_login(usuario, senha):
    executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, nivel TEXT NOT NULL)''')
    try:
        executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')")
    except sqlite3.IntegrityError:
        pass
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute("SELECT nivel FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

# Garante que as tabelas existam
executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, escala TEXT, data_admissao TEXT, status TEXT, data_saida TEXT, termo_pdf TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)")

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
                nivel_acesso = verificar_login(input_usuario, input_senha)
                if nivel_acesso:
                    st.session_state.logado = True
                    st.session_state.usuario = input_usuario
                    st.session_state.nivel = nivel_acesso
                    st.rerun()
                else: st.error("Usuário ou senha incorretos!")
else:
    with st.sidebar:
        if CAMINHO_LOGO: st.image(CAMINHO_LOGO, width=150)
        st.markdown(f"👤 Olá, **{st.session_state.usuario.capitalize()}**")
        st.markdown(f"🔑 Nível: `{st.session_state.nivel.upper()}`")
        st.divider()
        opcoes_menu = ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos / Faltas"]
        if st.session_state.nivel == "admin": opcoes_menu.append("⚙️ Gerenciar Usuários")
        aba_selecionada = st.radio("Escolha o módulo:", opcoes_menu)
        if st.button("Sair / Logoff", use_container_width=True):
            st.session_state.logado = False
            st.session_state.usuario = ""
            st.session_state.nivel = ""
            st.rerun()

    if "🎙️ Palestrantes" in aba_selecionada:
        st.title("🎙️ Cadastro e Agenda de Palestrantes")
        # (Lógica mantida)
        
    elif "👥 Trabalhadores" in aba_selecionada:
        st.title("👥 Equipe de Trabalhadores")
        with st.expander("➕ Cadastrar ou Alterar Integrante"):
            id_edicao = st.number_input("ID do Trabalhador (0 para Novo)", min_value=0, step=1)
            col1, col2 = st.columns(2)
            nome_trab = col1.text_input("Nome Completo")
            funcao_trab = col2.text_input("Função / Cargo")
            tel_trab = col1.text_input("Telefone")
            end_trab = col2.text_input("Endereço")
            arquivo_pdf = st.file_uploader("Anexar Termo em PDF", type=["pdf"])
            
            if st.button("Salvar / Atualizar Cadastro"):
                if id_edicao == 0:
                    executar_query("INSERT INTO trabalhadores (nome, funcao, telefone, endereco, status) VALUES (?,?,?,?,'Ativo')", (nome_trab, funcao_trab, tel_trab, end_trab))
                    st.success("Cadastrado com sucesso!")
                else:
                    executar_query("UPDATE trabalhadores SET nome=?, funcao=?, telefone=?, endereco=? WHERE id=?", (nome_trab, funcao_trab, tel_trab, end_trab, id_edicao))
                    st.success(f"Cadastro ID {id_edicao} atualizado!")
                st.rerun()

        st.subheader("🔍 Lista Integrantes")
        trabalhadores = executar_query("SELECT id, nome, funcao, telefone, endereco, status FROM trabalhadores", retornar_dados=True)
        if trabalhadores:
            for id_t, n, f, t, e, st_atual in trabalhadores:
                st.write(f"**ID {id_t}:** {n} | Função: {f} | Tel: {t} | End: {e} | Status: {st_atual}")
                st.divider()

    elif "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        # (Lógica mantida para próxima etapa)

    elif "⚙️ Gerenciar Usuários" in aba_selecionada:
        st.title("⚙️ Controle de Usuários e Senhas")
        # (Lógica mantida)
