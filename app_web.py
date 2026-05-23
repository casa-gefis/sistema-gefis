import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO DE DADOS (Mantido original)
# ==========================================
st.set_page_config(page_title="Sistema de Gestão Espírita", page_icon="🏠", layout="wide")

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v10.db")

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Garantir estrutura (Mesma do seu código original)
executar_query("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, escala TEXT, data_admissao TEXT, status TEXT, data_saida TEXT, termo_pdf TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, status TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY, aluno_id INTEGER, data_aula TEXT, status TEXT)")

# ==========================================
# LÓGICA DE LOGIN (Sua estrutura original)
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    # (Inserir aqui o seu código de login original - o layout de colunas e título)
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
    # MENU ORIGINAL
    aba_selecionada = st.sidebar.radio("Escolha o módulo:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos / Faltas", "✅ Chamada"])
    
    # --- PALESTRANTES ---
    if "🎙️ Palestrantes" in aba_selecionada:
        # (Seu código original de palestrantes)
        pass

    # --- TRABALHADORES (Adicionando novas colunas) ---
    elif "👥 Trabalhadores" in aba_selecionada:
        st.title("👥 Equipe de Trabalhadores")
        with st.expander("➕ Cadastrar Novo Integrante"):
            col1, col2 = st.columns(2)
            n = col1.text_input("Nome"); f = col2.text_input("Função")
            end = col1.text_input("Endereço"); tel = col2.text_input("WhatsApp")
            # Adição das novas colunas conforme pedido
            data_adm = col1.date_input("Data de Admissão")
            data_sai = col2.date_input("Data de Desligamento", value=None)
            
            if st.button("Salvar Novo Integrante"):
                executar_query("INSERT INTO trabalhadores (nome, funcao, endereco, telefone, data_admissao, data_saida, status) VALUES (?,?,?,?,?,?,'Ativo')", 
                               (n, f, end, tel, str(data_adm), str(data_sai)))
                st.rerun()

    # --- ALUNOS (Adicionando Frequência) ---
    elif "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        # Listagem com cálculo
        alunos = executar_query("SELECT id, nome, curso FROM alunos", retornar_dados=True)
        for id_a, nome, curso in alunos:
            presencas = executar_query("SELECT status FROM presenca_alunos WHERE aluno_id=?", (id_a,), True)
            freq = (sum(1 for p in presencas if p[0] == 'Presente') / len(presencas) * 100) if presencas else 0
            st.write(f"**{nome}** ({curso}) - Frequência: {freq:.1f}%")

    # --- CHAMADA (Nova lógica anti-duplicação) ---
    elif "✅ Chamada" in aba_selecionada:
        st.title("✅ Registrar Presença")
        hoje = str(datetime.now().date())
        for id_a, nome in executar_query("SELECT id, nome FROM alunos", retornar_dados=True):
            ja_gravado = executar_query("SELECT id FROM presenca_alunos WHERE aluno_id=? AND data_aula=?", (id_a, hoje), True)
            col1, col2 = st.columns([3, 1])
            col1.write(nome)
            if not ja_gravado:
                if col2.button("Presente", key=f"btn_{id_a}"):
                    executar_query("INSERT INTO presenca_alunos (aluno_id, data_aula, status) VALUES (?,?,?)", (id_a, hoje, 'Presente'))
                    st.rerun()
            else:
                col2.write("✅ Gravado")
