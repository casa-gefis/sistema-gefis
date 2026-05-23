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
CAMINHO_BANCO = os.path.join(DIRETORIO_ATUAL, "casa_espirita_v10.db")
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

# Garantir estrutura do banco com os novos campos
executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, data_admissao TEXT, data_saida TEXT, status TEXT, termo_pdf TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, curso TEXT, ano_inicio TEXT, data_entrada TEXT, data_saida TEXT, status TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, status TEXT)''')

# Admin padrão
try: executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')")
except: pass

# Função de Frequência
def calcular_frequencia(aluno_id):
    dados = executar_query("SELECT status FROM presenca_alunos WHERE aluno_id = ?", (aluno_id,), retornar_dados=True)
    if not dados: return 0.0
    total = len(dados)
    presentes = sum(1 for d in dados if d[0] == 'Presente')
    return (presentes / total) * 100

# ==========================================
# INTERFACE
# ==========================================
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.nivel = ""

if not st.session_state.logado:
    u = st.text_input("Usuário").strip().lower()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if nivel:
            st.session_state.logado = True
            st.session_state.usuario = u
            st.session_state.nivel = nivel[0][0]
            st.rerun()
else:
    with st.sidebar:
        st.write(f"👤 {st.session_state.usuario.capitalize()} | 🔑 {st.session_state.nivel.upper()}")
        aba = st.radio("Módulos:", ["👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
        if st.button("Sair"): st.session_state.logado = False; st.rerun()

    # --- TRABALHADORES ---
    if aba == "👥 Trabalhadores":
        st.title("👥 Equipe de Trabalhadores")
        busca = st.text_input("🔍 Buscar trabalhador")
        with st.expander("➕ Novo Cadastro"):
            col1, col2 = st.columns(2)
            n = col1.text_input("Nome"); f = col2.text_input("Função")
            tel = col1.text_input("WhatsApp"); end = col2.text_input("Endereço")
            adm = col1.date_input("Admissão"); sai = col2.date_input("Desligamento", value=None)
            if st.button("Salvar"):
                executar_query("INSERT INTO trabalhadores (nome, funcao, telefone, endereco, data_admissao, data_saida, status) VALUES (?,?,?,?,?,?,'Ativo')", (n,f,tel,end,str(adm),str(sai)))
                st.rerun()
        
        trabs = executar_query("SELECT nome, funcao, telefone, endereco FROM trabalhadores WHERE nome LIKE ?", (f"%{busca}%",), True)
        for t in trabs: st.write(f"**{t[0]}** - {t[1]} | {t[2]} | {t[3]}")

    # --- ALUNOS ---
    elif aba == "🎓 Alunos":
        st.title("🎓 Gestão de Alunos")
        with st.expander("➕ Matricular Aluno"):
            n = st.text_input("Nome do Aluno"); t = st.text_input("WhatsApp")
            c = st.text_input("Curso"); ano = st.text_input("Ano de Início")
            if st.button("Salvar Matrícula"):
                executar_query("INSERT INTO alunos (nome, telefone, curso, ano_inicio, status) VALUES (?,?,?,?,'Ativo')", (n,t,c,ano))
                st.rerun()
        
        for id_a, nome, cur in executar_query("SELECT id, nome, curso FROM alunos", retornar_dados=True):
            st.write(f"**{nome}** ({cur}) - Frequência: {calcular_frequencia(id_a):.1f}%")

    # --- CHAMADA ---
    elif aba == "✅ Chamada":
        st.title("✅ Registrar Presença")
        data = st.date_input("Data da aula")
        for id_a, nome in executar_query("SELECT id, nome FROM alunos", retornar_dados=True):
            col1, col2 = st.columns([3, 1])
            col1.write(nome)
            status = col2.radio("S", ["Presente", "Falta"], key=f"p_{id_a}", horizontal=True)
            if st.button(f"Confirmar {nome}", key=f"b_{id_a}"):
                executar_query("INSERT INTO presenca_alunos (aluno_id, data_aula, status) VALUES (?,?,?)", (id_a, str(data), status))
                st.rerun()
