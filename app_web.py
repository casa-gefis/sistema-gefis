import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando)
# ==========================================
st.set_page_config(
    page_title="Sistema de Gestão Espírita",
    page_icon="🏠",
    layout="wide"
)

# Correção essencial para sistemas SQLite rodando no Linux do Streamlit Cloud
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

# Caminhos de armazenamento na Nuvem do Streamlit
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v9.db")
PASTA_PDFS = os.path.join(DIRETORIO_ATUAL, "termos_pdf")
os.makedirs(PASTA_PDFS, exist_ok=True)

# DETECTOR INTELIGENTE DE LOGO (Ignora maiúsculas/minúsculas no GitHub)
CAMINHO_LOGO = None
if os.path.exists(DIRETORIO_ATUAL):
    arquivos_na_pasta = os.listdir(DIRETORIO_ATUAL)
    for arquivo in arquivos_na_pasta:
        # Se o arquivo começar com "logo" (independente se for LOGO, Logo, logo) e for imagem
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
    # Cria a tabela de usuários caso ela suma na inicialização da nuvem
    executar_query('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nivel TEXT NOT NULL
    )
    ''')
    # Garante o cadastro do administrador padrão do sistema
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

# Garante que as outras tabelas existam no banco na nuvem
executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, escala TEXT, data_admissao TEXT, status TEXT, data_saida TEXT, termo_pdf TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)")

# ==========================================
# MONITORAMENTO DE ACESSO
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

if not st.session_state.logado:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("")
        st.write("")
        if CAMINHO_LOGO:
            st.image(CAMINHO_LOGO, width=280)
        st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema</h2>", unsafe_allow_html=True)
        
        with st.form(key="form_login"):
            input_usuario = st.text_input("Usuário").strip().lower()
            input_senha = st.text_input("Senha", type="password")
            botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_entrar:
                nivel_acesso = verificar_login(input_usuario, input_senha)
                if nivel_acesso:
                    st.session_state.logado = True
                    st.session_state.usuario = input_usuario
                    st.session_state.nivel = nivel_acesso
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")
else:
    # --- MENU PRINCIPAL ---
    with st.sidebar:
        if CAMINHO_LOGO:
            st.image(CAMINHO_LOGO, width=150)
        st.markdown(f"👤 Olá, **{st.session_state.usuario.capitalize()}**")
        st.markdown(f"🔑 Nível: `{st.session_state.nivel.upper()}`")
        st.divider()
        
        opcoes_menu = ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos / Faltas"]
        if st.session_state.nivel == "admin":
            opcoes_menu.append("⚙️ Gerenciar Usuários")
            
        aba_selecionada = st.radio("Escolha o módulo:", opcoes_menu)
        st.divider()
        if st.button("Sair / Logoff", use_container_width=True):
            st.session_state.logado = False
            st.session_state.usuario = ""
            st.session_state.nivel = ""
            st.rerun()

    # PALESTRANTES
    if "🎙️ Palestrantes" in aba_selecionada:
        st.title("🎙️ Cadastro e Agenda de Palestrantes")
        with st.expander("📝 Agendar Nova Palestra", expanded=True):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome do Palestrante")
            casa_origem = col1.text_input("Casa de Origem")
            contato = col2.text_input("Contato")
            tema = col2.text_input("Tema da Palestra")
            data_palestra = st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"))
                
            if st.button("Salvar Palestra", type="primary"):
                if nome:
                    executar_query("INSERT INTO palestrantes (nome, contato, casa_origem, tema, data_palestra) VALUES (?,?,?,?,?)", (nome, contato, casa_origem, tema, data_palestra))
                    st.success("Palestra salva com sucesso!")
                    st.rerun()

        st.subheader("🔍 Histórico de Palestras")
        registros = executar_query("SELECT nome, tema, data_palestra, casa_origem FROM palestrantes ORDER BY id DESC", retornar_dados=True)
        if registros:
            st.table([{"Palestrante": r[0], "Tema": r[1], "Data": r[2], "Casa": r[3]} for r in registros])

    # TRABALHADORES (COM EDIÇÃO E NOVOS CAMPOS)
    elif "👥 Trabalhadores" in aba_selecionada:
        st.title("👥 Equipe de Trabalhadores")
        with st.expander("➕ Cadastrar ou Alterar Integrante"):
            id_edicao = st.number_input("ID do Trabalhador (0 para Novo)", min_value=0, step=1)
            col1, col2 = st.columns(2)
            nome_trab = col1.text_input("Nome Completo")
            funcao_trab = col2.text_input("Função / Cargo")
            tel_trab = col1.text_input("Telefone")
            end_trab = col2.text_input("Endereço")
                
            if st.button("Salvar / Atualizar Integrante", type="primary"):
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

    # ALUNOS
    elif "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        nome_aluno = st.text_input("Nome do Aluno")
        curso_aluno = st.text_input("Curso")
        if st.button("Matricular Aluno", type="primary"):
            if nome_aluno:
                executar_query("INSERT INTO alunos (nome, curso, status) VALUES (?,?,'Ativo')", (nome_aluno, curso_aluno))
                st.success("Matriculado!")
                st.rerun()

    # GERENCIAR USUÁRIOS
    elif "⚙️ Gerenciar Usuários" in aba_selecionada:
        st.title("⚙️ Controle de Usuários e Senhas")
        with st.form("form_usuarios"):
            novo_usuario = st.text_input("Nome de Usuário (Login)").strip().lower()
            nova_senha = st.text_input("Nova Senha", type="password")
            novo_nivel = st.selectbox("Nível de Acesso", ["trabalhador", "admin"])
            botao_salvar = st.form_submit_button("Salvar / Atualizar Usuário")
            
            if botao_salvar:
                if novo_usuario and nova_senha:
                    existe = executar_query("SELECT id FROM usuarios WHERE usuario = ?", (novo_usuario,), retornar_dados=True)
                    if existe:
                        executar_query("UPDATE usuarios SET senha = ?, nivel = ? WHERE usuario = ?", (nova_senha, novo_nivel, novo_usuario))
                        st.success(f"Senha do usuário '{novo_usuario}' alterada com sucesso!")
                    else:
                        executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES (?,?,?)", (novo_usuario, nova_senha, novo_nivel))
                        st.success(f"Novo usuário '{novo_usuario}' cadastrado!")
                    st.rerun()
                else:
                    st.warning("Preencha o usuário e a senha!")
                    
        st.subheader("📋 Operadores Cadastrados")
        usuarios_lista = executar_query("SELECT usuario, nivel FROM usuarios", retornar_dados=True)
        if usuarios_lista:
            st.table([{"Usuário": u[0], "Nível de Acesso": u[1].upper()} for u in usuarios_lista])
