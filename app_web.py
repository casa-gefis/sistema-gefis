import os
import sqlite3
import streamlit as st
from datetime import datetime
from google.oauth2.service_account import Credentials
import gdown

# ==========================================
# CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando)
# ==========================================
st.set_page_config(
    page_title="Sistema de Gestão Espírita",
    page_icon="🏠",
    layout="wide"
)

# Caminhos locais temporários na nuvem do Streamlit
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_LOCAL_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v9.db")
PASTA_LOCAL_PDFS = os.path.join(DIRETORIO_ATUAL, "termos_pdf")
os.makedirs(PASTA_LOCAL_PDFS, exist_ok=True)

# DETECTOR AUTOMÁTICO DE LOGO LOCAL
if os.path.exists(os.path.join(DIRETORIO_ATUAL, "logo.png")):
    CAMINHO_LOGO = os.path.join(DIRETORIO_ATUAL, "logo.png")
elif os.path.exists(os.path.join(DIRETORIO_ATUAL, "logo.jpg")):
    CAMINHO_LOGO = os.path.join(DIRETORIO_ATUAL, "logo.jpg")
else:
    CAMINHO_LOGO = None

# ==========================================
# CONEXÃO COM O GOOGLE DRIVE (SEGREDO DA NUVEM)
# ==========================================
# Pegamos as credenciais que você salvou secretamente na configuração do Streamlit
if "gdrive_credentials" in st.secrets:
    info_chaves = dict(st.secrets["gdrive_credentials"])
    # ID da pasta 'Sistema_GEFIS' que você criou no Drive (vamos configurar no Streamlit depois)
    ID_PASTA_DRIVE = st.secrets["gdrive_folder_id"]
else:
    st.error("Chaves de acesso ao Google Drive não configuradas no Streamlit Cloud!")
    st.stop()

# Função simples para simular o banco local puxando/enviando pro Drive
def executar_query(query, params=(), retornar_dados=False):
    # Nota: Em sistemas de alta escala usaríamos APIs diretas do Drive ou bancos como Supabase,
    # mas mantendo o seu SQLite atual, conectamos via persistência temporária.
    conn = sqlite3.connect(CAMINHO_LOCAL_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = None
    if retornar_dados:
        dados = cursor.fetchall()
    conn.commit()
    conn.close()
    return dados

def verificar_login(usuario, senha):
    conn = sqlite3.connect(CAMINHO_LOCAL_BANCO)
    cursor = conn.cursor()
    cursor.execute("SELECT nivel FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

# ==========================================
# GERENCIAMENTO DE SESSÃO (AUTENTICAÇÃO)
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("") 
        if CAMINHO_LOGO:
            st.image(CAMINHO_LOGO, use_container_width=True)
            
        st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema</h2>", unsafe_allow_html=True)
        
        with st.form(key="form_login"):
            input_usuario = st.text_input("Usuário").strip().lower()
            input_senha = st.text_input("Senha", type="password")
            botao_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_entrar:
                # Login fixo temporário de segurança ou via banco
                if input_usuario == "eduardo" and input_senha == "12345":
                    st.session_state.logado = True
                    st.session_state.usuario = "eduardo"
                    st.session_state.nivel = "admin"
                    st.rerun()
                else:
                    nivel_acesso = verificar_login(input_usuario, input_senha)
                    if nivel_acesso:
                        st.session_state.logado = True
                        st.session_state.usuario = input_usuario
                        st.session_state.nivel = nivel_acesso
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos!")

# --- INTERFACE PRINCIPAL ---
else:
    with st.sidebar:
        if CAMINHO_LOGO:
            st.image(CAMINHO_LOGO, width=150)
        st.markdown(f"👤 Olá, **{st.session_state.usuario.capitalize()}**")
        st.markdown(f"🔑 Nível: `{st.session_state.nivel.upper()}`")
        st.divider()
        
        st.markdown("### 🏠 Menu Principal")
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

    # MÓDULO: PALESTRANTES
    if "🎙️ Palestrantes" in aba_selecionada:
        st.title("🎙️ Cadastro e Agenda de Palestrantes")
        with st.expander("📝 Agendar Nova Palestra", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Palestrante")
                casa_origem = st.text_input("Casa de Origem")
            with col2:
                contato = st.text_input("Contato")
                tema = st.text_input("Tema da Palestra")
            data_palestra = st.text_input("Data", value=datetime.now().strftime("%d/%m/%Y"))
                
            if st.button("Salvar Palestra", type="primary"):
                if nome:
                    executar_query("INSERT INTO palestrantes (nome, contato, casa_origem, tema, data_palestra) VALUES (?,?,?,?,?)", (nome, contato, casa_origem, tema, data_palestra))
                    st.success("Palestra salva!")
                    st.rerun()

        st.subheader("🔍 Histórico")
        registros = executar_query("SELECT nome, tema, data_palestra, casa_origem, contato FROM palestrantes ORDER BY id DESC", retornar_dados=True)
        if registros:
            st.table([{"Palestrante": r[0], "Tema": r[1], "Data": r[2], "Casa de Origem": r[3]} for r in registros])

    # MÓDULO: TRABALHADORES
    elif "👥 Trabalhadores" in aba_selecionada:
        st.title("👥 Equipe de Trabalhadores")
        with st.expander("➕ Cadastrar Novo Integrante"):
            col1, col2 = st.columns(2)
            nome_trab = col1.text_input("Nome Completo")
            funcao_trab = col2.text_input("Função / Cargo")
            arquivo_pdf = st.file_uploader("Anexar Termo em PDF", type=["pdf"])
                
            if st.button("Cadastrar Integrante", type="primary"):
                if nome_trab:
                    caminho_salvar_pdf = ""
                    if arquivo_pdf is not None:
                        nome_limpo = f"{nome_trab.replace(' ', '_')}.pdf"
                        caminho_salvar_pdf = os.path.join(PASTA_LOCAL_PDFS, nome_limpo)
                        with open(caminho_salvar_pdf, "wb") as f:
                            f.write(arquivo_pdf.getbuffer())
                    
                    executar_query("INSERT INTO trabalhadores (nome, funcao, status, termo_pdf) VALUES (?,?,'Ativo',?)", (nome_trab, funcao_trab, caminho_salvar_pdf))
                    st.success("Cadastrado com sucesso!")
                    st.rerun()

        st.subheader("🔍 Lista Integrantes")
        trabalhadores = executar_query("SELECT id, nome, funcao, status, termo_pdf FROM trabalhadores", retornar_dados=True)
        if trabalhadores:
            for id_t, n, f, st_atual, pdf_path in trabalhadores:
                col_n, col_f, col_s, col_pdf = st.columns([3, 2, 2, 2])
                col_n.write(f"**{n}**")
                col_f.write(f"Função: {f}")
                col_s.write("🟢 Ativo" if st_atual == "Ativo" else "🔴 Inativo")
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pdf_file:
                        col_pdf.download_button("📄 Baixar Termo", data=pdf_file.read(), file_name=os.path.basename(pdf_path), key=f"pdf_{id_t}")
                else:
                    col_pdf.write("⚠️ Sem termo")
                st.divider()

    # MÓDULO: ALUNOS
    elif "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        nome_aluno = st.text_input("Nome do Aluno")
        curso_aluno = st.text_input("Curso")
        if st.button("Matricular", type="primary"):
            if nome_aluno:
                executar_query("INSERT INTO alunos (nome, curso, status) VALUES (?,?,'Ativo')", (nome_aluno, curso_aluno))
                st.success("Matriculado!")
                st.rerun()

    # MÓDULO: USUÁRIOS
    elif "⚙️ Gerenciar Usuários" in aba_selecionada:
        st.title("⚙️ Painel de Controle de Usuários")
        novo_usuario = st.text_input("Login").strip().lower()
        nova_senha = st.text_input("Senha", type="password")
        novo_nivel = st.selectbox("Nível", ["trabalhador", "admin"])
        if st.button("Salvar Usuário"):
            if novo_usuario and nova_senha:
                executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES (?,?,?)", (novo_usuario, nova_senha, novo_nivel))
                st.success("Salvo!")
                st.rerun()