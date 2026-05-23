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

# ==========================================
# FUNÇÕES DO BANCO DE DADOS
# ==========================================
def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Inicialização de Tabelas com colunas solicitadas
executar_query("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, escala TEXT, data_admissao TEXT, status TEXT, data_saida TEXT, termo_pdf TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, data_adm TEXT, data_desligamento TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, tema_estudado TEXT, status TEXT)")

# Admin Padrão
try: executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')")
except: pass

# ==========================================
# LOGIN
# ==========================================
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.subheader("Login de Acesso")
    u = st.text_input("Usuário").strip().lower()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        res = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if res:
            st.session_state.logado = True; st.session_state.usuario = u; st.session_state.nivel = res[0][0]
            st.rerun()
else:
    with st.sidebar:
        st.markdown(f"👤 {st.session_state.usuario.capitalize()}")
        aba = st.radio("Módulo:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos / Faltas", "⚙️ Gerenciar Usuários"])
        if st.button("Sair"): st.session_state.logado = False; st.rerun()

    # ALUNOS (Com novas colunas e botão de exclusão)
    if "🎓 Alunos" in aba:
        st.title("🎓 Gestão de Alunos")
        with st.expander("Matricular Novo Aluno"):
            n = st.text_input("Nome"); c = st.text_input("Curso"); ano = st.text_input("Ano Início")
            adm = st.date_input("Data Admissão"); sai = st.date_input("Data Desligamento", value=None)
            if st.button("Salvar"):
                executar_query("INSERT INTO alunos (nome, curso, ano_inicio, data_adm, data_desligamento, status) VALUES (?,?,?,?,?, 'Ativo')", (n, c, ano, str(adm), str(sai)))
                st.rerun()

        st.subheader("Lista de Alunos")
        for id_a, nome in executar_query("SELECT id, nome FROM alunos", retornar_dados=True):
            col1, col2 = st.columns([4, 1])
            col1.write(f"👤 {nome}")
            if col2.button("🗑️ Excluir", key=f"del_{id_a}"):
                executar_query("DELETE FROM alunos WHERE id=?", (id_a,))
                st.rerun()

    # TRABALHADORES
    elif "👥 Trabalhadores" in aba:
        st.title("👥 Trabalhadores")
        with st.expander("Cadastrar"):
            n = st.text_input("Nome"); f = st.text_input("Função"); end = st.text_input("Endereço")
            if st.button("Cadastrar"):
                executar_query("INSERT INTO trabalhadores (nome, funcao, endereco, status) VALUES (?,?,?, 'Ativo')", (n, f, end))
                st.rerun()
        for id_t, nome, func in executar_query("SELECT id, nome, funcao FROM trabalhadores", retornar_dados=True):
            st.write(f"**{nome}** - {func}")

    # PALESTRANTES
    elif "🎙️ Palestrantes" in aba:
        st.title("🎙️ Palestrantes")
        # (Sua lógica original aqui)
