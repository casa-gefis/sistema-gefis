import os
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO DE DADOS
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

def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Função de atualização automática das tabelas
def atualizar_banco():
    executar_query("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)")
    executar_query("CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)")
    executar_query("CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, escala TEXT, data_admissao TEXT, status TEXT, data_saida TEXT, termo_pdf TEXT)")
    executar_query("CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, data_entrada TEXT, data_saida TEXT, status TEXT)")
    executar_query("CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)")

atualizar_banco()

def calcular_frequencia(aluno_id):
    dados = executar_query("SELECT status FROM presenca_alunos WHERE aluno_id = ?", (aluno_id,), retornar_dados=True)
    if not dados or len(dados) == 0: return 0.0
    presentes = sum(1 for d in dados if d[0] == 'Presente')
    return (presentes / len(dados)) * 100

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

if not st.session_state.logado:
    st.title("Acesso ao Sistema")
    input_usuario = st.text_input("Usuário").strip().lower()
    input_senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = executar_query("SELECT nivel FROM usuarios WHERE usuario = ? AND senha = ?", (input_usuario, input_senha), True)
        if nivel:
            st.session_state.logado = True
            st.session_state.usuario = input_usuario
            st.session_state.nivel = nivel[0][0]
            st.rerun()
        else: st.error("Usuário ou senha incorretos!")
else:
    with st.sidebar:
        st.markdown(f"👤 {st.session_state.usuario.capitalize()}")
        opcoes = ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos / Faltas", "✅ Chamada"]
        if st.session_state.nivel == "admin": opcoes.append("⚙️ Gerenciar Usuários")
        aba_selecionada = st.radio("Módulo:", opcoes)
        if st.button("Sair"): st.session_state.logado = False; st.rerun()

    # TRABALHADORES
    if "👥 Trabalhadores" in aba_selecionada:
        st.title("👥 Equipe de Trabalhadores")
        with st.expander("➕ Cadastrar Novo Integrante"):
            col1, col2 = st.columns(2)
            nome_trab = col1.text_input("Nome Completo")
            funcao_trab = col2.text_input("Função / Cargo")
            endereco = col1.text_input("Endereço")
            whatsapp = col2.text_input("WhatsApp")
            data_adm = col1.date_input("Data Admissão")
            data_sai = col2.date_input("Data Desligamento", value=None)
            arquivo_pdf = st.file_uploader("Anexar Termo em PDF", type=["pdf"])
            
            if st.button("Cadastrar Integrante"):
                caminho_pdf = ""
                if arquivo_pdf:
                    caminho_pdf = os.path.join(PASTA_PDFS, f"{nome_trab.replace(' ', '_')}.pdf")
                    with open(caminho_pdf, "wb") as f: f.write(arquivo_pdf.getbuffer())
                
                executar_query("INSERT INTO trabalhadores (nome, funcao, endereco, telefone, data_admissao, data_saida, status, termo_pdf) VALUES (?,?,?,?,?,?,'Ativo',?)", 
                               (nome_trab, funcao_trab, endereco, whatsapp, str(data_adm), str(data_sai), caminho_pdf))
                st.rerun()

    # ALUNOS
    elif "🎓 Alunos / Faltas" in aba_selecionada:
        st.title("🎓 Gestão de Alunos")
        # Listagem com Frequência
        for id_aluno, nome, curso in executar_query("SELECT id, nome, curso FROM alunos", retornar_dados=True):
            freq = calcular_frequencia(id_aluno)
            st.write(f"**{nome}** - Curso: {curso} | Frequência: {freq:.1f}%")

    # CHAMADA
    elif "✅ Chamada" in aba_selecionada:
        st.title("✅ Registrar Presença")
        alunos = executar_query("SELECT id, nome FROM alunos", retornar_dados=True)
        for id_a, nome in alunos:
            col1, col2 = st.columns([3, 1])
            col1.write(nome)
            status = col2.radio("S", ["Presente", "Falta"], key=f"aluno_{id_a}", horizontal=True)
            if col2.button("Gravar", key=f"btn_{id_a}"):
                executar_query("INSERT INTO presenca_alunos (aluno_id, data_aula, status) VALUES (?,?,?)", (id_a, str(datetime.now().date()), status))
                st.rerun()
