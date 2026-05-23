import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO DE DADOS
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

# Garantir estrutura inicial
executar_query("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, data_admissao TEXT, data_saida TEXT, status TEXT, termo_pdf TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY, nome TEXT, curso TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY, aluno_id INTEGER, data_aula TEXT, status TEXT)")

# ==========================================
# LÓGICA DE LOGIN
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário").strip().lower()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        usuario = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if usuario:
            st.session_state.logado = True
            st.session_state.usuario = u
            st.session_state.nivel = usuario[0][0]
            st.rerun()
        else:
            st.error("Dados incorretos.")
else:
    # ==========================================
    # MENU E MÓDULOS
    # ==========================================
    aba = st.sidebar.radio("Módulo:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
    if st.sidebar.button("Sair"): st.session_state.logado = False; st.rerun()

    # 🎙️ PALESTRANTES
    if aba == "🎙️ Palestrantes":
        st.title("🎙️ Palestrantes")
        with st.expander("Cadastrar Novo"):
            n = st.text_input("Nome"); c = st.text_input("Contato"); orig = st.text_input("Casa"); t = st.text_input("Tema")
            if st.button("Salvar"):
                executar_query("INSERT INTO palestrantes (nome, contato, casa_origem, tema, data_palestra) VALUES (?,?,?,?,?)", (n, c, orig, t, str(datetime.now().date())))
                st.rerun()
        for r in executar_query("SELECT nome, tema, casa_origem FROM palestrantes", retornar_dados=True):
            st.write(f"**{r[0]}** | Tema: {r[1]} ({r[2]})")

    # 👥 TRABALHADORES
    elif aba == "👥 Trabalhadores":
        st.title("👥 Trabalhadores")
        with st.expander("Cadastrar Novo"):
            col1, col2 = st.columns(2)
            n = col1.text_input("Nome"); f = col2.text_input("Função"); end = col1.text_input("Endereço"); tel = col2.text_input("WhatsApp")
            if st.button("Salvar Integrante"):
                executar_query("INSERT INTO trabalhadores (nome, funcao, endereco, telefone, status) VALUES (?,?,?,?,'Ativo')", (n, f, end, tel))
                st.rerun()
        for t in executar_query("SELECT nome, funcao FROM trabalhadores", retornar_dados=True):
            st.write(f"**{t[0]}** - {t[1]}")

    # 🎓 ALUNOS
    elif aba == "🎓 Alunos":
        st.title("🎓 Gestão de Alunos")
        with st.expander("Matricular Aluno"):
            n = st.text_input("Nome"); c = st.text_input("Curso")
            if st.button("Matricular"):
                executar_query("INSERT INTO alunos (nome, curso, status) VALUES (?,?,'Ativo')", (n, c))
                st.rerun()
        for id_a, nome, curso in executar_query("SELECT id, nome, curso FROM alunos", retornar_dados=True):
            freq_dados = executar_query("SELECT status FROM presenca_alunos WHERE aluno_id=?", (id_a,), True)
            freq = (sum(1 for d in freq_dados if d[0] == 'Presente') / len(freq_dados) * 100) if freq_dados else 0
            st.write(f"**{nome}** ({curso}) - Frequência: {freq:.1f}%")

    # ✅ CHAMADA (Lógica anti-duplicação)
    elif aba == "✅ Chamada":
        st.title("✅ Chamada do Dia")
        data_hoje = str(datetime.now().date())
        for id_a, nome in executar_query("SELECT id, nome FROM alunos", retornar_dados=True):
            col1, col2 = st.columns([3, 1])
            col1.write(nome)
            # Verifica se já existe registro hoje
            ja_registrado = executar_query("SELECT id FROM presenca_alunos WHERE aluno_id=? AND data_aula=?", (id_a, data_hoje), True)
            if not ja_registrado:
                if col2.button("Registrar Presença", key=f"btn_{id_a}"):
                    executar_query("INSERT INTO presenca_alunos (aluno_id, data_aula, status) VALUES (?,?,?)", (id_a, data_hoje, 'Presente'))
                    st.rerun()
            else:
                col2.write("✅ OK")
