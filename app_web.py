import os
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO E BANCO
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

# Inicialização das Tabelas com novas colunas
executar_query('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha TEXT, nivel TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS palestrantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, casa_origem TEXT, tema TEXT, data_palestra TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS trabalhadores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, funcao TEXT, telefone TEXT, endereco TEXT, data_admissao TEXT, data_saida TEXT, status TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, curso TEXT, ano_inicio TEXT, data_adm TEXT, data_desligamento TEXT, status TEXT)''')
executar_query('''CREATE TABLE IF NOT EXISTS presenca_alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data_aula TEXT, tema_estudado TEXT, status TEXT)''')

# Admin Padrão
try: executar_query("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('eduardo', '12345', 'admin')")
except: pass

# ==========================================
# LOGIN
# ==========================================
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário").strip().lower()
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if nivel:
            st.session_state.logado = True; st.session_state.usuario = u; st.session_state.nivel = nivel[0][0]
            st.rerun()
else:
    with st.sidebar:
        st.markdown(f"👤 {st.session_state.usuario.capitalize()}")
        aba = st.radio("Módulo:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
        if st.button("Sair"): st.session_state.logado = False; st.rerun()

    # PALESTRANTES
    if aba == "🎙️ Palestrantes":
        st.title("🎙️ Palestrantes")
        with st.expander("Agendar"):
            n = st.text_input("Nome"); c = st.text_input("Contato"); orig = st.text_input("Casa"); t = st.text_input("Tema")
            if st.button("Salvar"):
                executar_query("INSERT INTO palestrantes (nome, contato, casa_origem, tema, data_palestra) VALUES (?,?,?,?,?)", (n, c, orig, t, str(datetime.now().date())))
                st.rerun()
        for r in executar_query("SELECT nome, tema, casa_origem FROM palestrantes", retornar_dados=True):
            st.write(f"**{r[0]}** - {r[1]} ({r[2]})")

    # TRABALHADORES
    elif aba == "👥 Trabalhadores":
        st.title("👥 Trabalhadores")
        with st.expander("Cadastrar"):
            col1, col2 = st.columns(2)
            n = col1.text_input("Nome"); f = col2.text_input("Função"); end = col1.text_input("Endereço"); tel = col2.text_input("WhatsApp")
            adm = col1.date_input("Data Admissão"); sai = col2.date_input("Data Desligamento", value=None)
            if st.button("Salvar"):
                executar_query("INSERT INTO trabalhadores (nome, funcao, endereco, telefone, data_admissao, data_saida, status) VALUES (?,?,?,?,?,?,?,'Ativo')", (n, f, end, tel, str(adm), str(sai)))
                st.rerun()
        for t in executar_query("SELECT nome, funcao FROM trabalhadores", retornar_dados=True):
            st.write(f"**{t[0]}** - {t[1]}")

    # ALUNOS (Com Editor Visual para limpeza de duplicados)
    elif aba == "🎓 Alunos":
        st.title("🎓 Gestão de Alunos")
        with st.expander("Matricular"):
            n = st.text_input("Nome"); c = st.text_input("Curso"); ano = st.text_input("Ano Início")
            d_adm = st.date_input("Data Admissão"); d_sai = st.date_input("Data Desligamento", value=None)
            if st.button("Matricular"):
                executar_query("INSERT INTO alunos (nome, curso, ano_inicio, data_adm, data_desligamento, status) VALUES (?,?,?,?,?,?,'Ativo')", (n, c, ano, str(d_adm), str(d_sai)))
                st.rerun()
        
        st.subheader("📋 Editar / Excluir Alunos")
        dados = executar_query("SELECT id, nome, curso, ano_inicio FROM alunos", retornar_dados=True)
        if dados:
            df = pd.DataFrame(dados, columns=["ID", "Nome", "Curso", "Ano"])
            edited_df = st.data_editor(df, hide_index=True, use_container_width=True)
            if st.button("🗑️ Salvar alterações / Remover linhas deletadas"):
                # Deleta do banco o que não está no editor
                for id_banco in df['ID']:
                    if id_banco not in edited_df['ID'].values:
                        executar_query("DELETE FROM alunos WHERE id=?", (id_banco,))
                st.rerun()

    # CHAMADA
    elif aba == "✅ Chamada":
        st.title("✅ Registrar Presença")
        data_a = st.date_input("Data da Aula")
        tema = st.text_input("Tema Estudado")
        for id_a, nome in executar_query("SELECT id, nome FROM alunos", retornar_dados=True):
            col1, col2 = st.columns([3, 1])
            col1.write(nome)
            status = col2.radio("Status", ["Presente", "Falta"], key=f"s_{id_a}", horizontal=True)
            if col2.button("Gravar", key=f"b_{id_a}"):
                executar_query("INSERT INTO presenca_alunos (aluno_id, data_aula, tema_estudado, status) VALUES (?,?,?,?)", (id_a, str(data_a), tema, status))
                st.rerun()
