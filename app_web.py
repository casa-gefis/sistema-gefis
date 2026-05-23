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

# ==========================================
# FUNÇÕES DO BANCO DE DADOS
# ==========================================
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
    executar_query('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nivel TEXT NOT NULL
    )
    ''')
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

# Tabelas originais
executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, escala TEXT, data_admissao TEXT, status TEXT, data_saida TEXT, termo_pdf TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)")

# ==========================================
# ESTADO DA SESSÃO
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""
if 'id_edicao_ativa' not in st.session_state:
    st.session_state.id_edicao_ativa = 0

# ==========================================
# INTERFACE
# ==========================================
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
                    st.session_state.logado = True
                    st.session_state.usuario = input_usuario
                    st.session_state.nivel = nivel
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
            st.rerun()

    # MÓDULOS
    if "🎙️ Palestrantes" in aba_selecionada:
        st.title("🎙️ Cadastro e Agenda de Palestrantes")
        with st.expander("📝 Agendar Nova Palestra"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome do Palestrante")
            casa = col1.text_input("Casa de Origem")
            contato = col2.text_input("Contato")
            tema = col2.text_input("Tema da Palestra")
            data = st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"))
            if st.button("Salvar Palestra"):
                executar_query("INSERT INTO palestrantes (nome, contato, casa_origem, tema, data_palestra) VALUES (?,?,?,?,?)", (nome, contato, casa, tema, data))
                st.rerun()
        st.subheader("🔍 Lista")
        registros = executar_query("SELECT nome, tema, data_palestra, casa_origem FROM palestrantes", retornar_dados=True)
        if registros: st.table([{"P": r[0], "T": r[1], "D": r[2], "C": r[3]} for r in registros])

    elif "👥 Trabalhadores" in aba_selecionada:
        st.title("👥 Equipe de Trabalhadores")
        
        # Carregar dados se houver ID em edição
        dados_edit = [None, None, None, None]
        if st.session_state.id_edicao_ativa > 0:
            res = executar_query("SELECT nome, funcao, telefone, endereco FROM trabalhadores WHERE id=?", (st.session_state.id_edicao_ativa,), retornar_dados=True)
            if res: dados_edit = res[0]

        with st.expander("➕ Cadastrar / Alterar Integrante", expanded=True):
            id_input = st.number_input("ID (0 para novo)", value=st.session_state.id_edicao_ativa, step=1)
            col1, col2 = st.columns(2)
            nome_n = col1.text_input("Nome", value=dados_edit[0] or "")
            func_n = col2.text_input("Função", value=dados_edit[1] or "")
            tel_n = col1.text_input("Telefone", value=dados_edit[2] or "")
            end_n = col2.text_input("Endereço", value=dados_edit[3] or "")
                
            if st.button("Salvar / Alterar"):
                if id_input == 0:
                    executar_query("INSERT INTO trabalhadores (nome, funcao, telefone, endereco, status) VALUES (?,?,?,?,'Ativo')", (nome_n, func_n, tel_n, end_n))
                else:
                    executar_query("UPDATE trabalhadores SET nome=?, funcao=?, telefone=?, endereco=? WHERE id=?", (nome_n, func_n, tel_n, end_n, id_input))
                st.session_state.id_edicao_ativa = 0
                st.rerun()

        st.subheader("🔍 Lista Integrantes")
        trabalhadores = executar_query("SELECT id, nome, funcao, telefone, endereco FROM trabalhadores", retornar_dados=True)
        for i in trabalhadores:
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.write(f"**ID {i[0]}:** {i[1]} | {i[2]} | {i[3]} | {i[4]}")
            if c2.button("✏️", key=f"alt_{i[0]}"):
                st.session_state.id_edicao_ativa = i[0]
                st.rerun()
            if c3.button("🗑️", key=f"del_{i[0]}"):
                executar_query("DELETE FROM trabalhadores WHERE id=?", (i[0],))
                st.rerun()

    elif "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        nome_aluno = st.text_input("Nome do Aluno")
        curso_aluno = st.text_input("Curso")
        if st.button("Matricular"):
            executar_query("INSERT INTO alunos (nome, curso, status) VALUES (?,?,'Ativo')", (nome_aluno, curso_aluno))
            st.rerun()

    elif "⚙️ Gerenciar Usuários" in aba_selecionada:
        st.title("⚙️ Controle de Usuários")
        with st.form("form_usuarios"):
            u_nome = st.text_input("Login").lower()
            u_senha = st.text_input("Senha", type="password")
            u_nivel = st.selectbox("Nível", ["trabalhador", "admin"])
            if st.form_submit_button("Salvar"):
                executar_query("INSERT OR REPLACE INTO usuarios (usuario, senha, nivel) VALUES (?,?,?)", (u_nome, u_senha, u_nivel))
                st.rerun()
        st.table(executar_query("SELECT usuario, nivel FROM usuarios", retornar_dados=True))
