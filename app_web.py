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
# FUNÇÕES DE BANCO E ESTRUTURA
# ==========================================
def executar_query(query, params=(), retornar_dados=False):
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall() if retornar_dados else None
    conn.commit()
    conn.close()
    return dados

# Função para garantir que colunas novas existam sem apagar dados antigos
def atualizar_banco():
    # Trabalhadores
    cols_trab = [c[1] for c in executar_query("PRAGMA table_info(trabalhadores)", retornar_dados=True)]
    if 'endereco' not in cols_trab: executar_query("ALTER TABLE trabalhadores ADD COLUMN endereco TEXT")
    if 'data_admissao' not in cols_trab: executar_query("ALTER TABLE trabalhadores ADD COLUMN data_admissao TEXT")
    if 'data_saida' not in cols_trab: executar_query("ALTER TABLE trabalhadores ADD COLUMN data_saida TEXT")
    
    # Alunos
    cols_aluno = [c[1] for c in executar_query("PRAGMA table_info(alunos)", retornar_dados=True)]
    if 'whatsapp' not in cols_aluno: executar_query("ALTER TABLE alunos ADD COLUMN whatsapp TEXT")
    if 'ano_inicio' not in cols_aluno: executar_query("ALTER TABLE alunos ADD COLUMN ano_inicio TEXT")
    if 'data_entrada' not in cols_aluno: executar_query("ALTER TABLE alunos ADD COLUMN data_entrada TEXT")
    if 'data_saida' not in cols_aluno: executar_query("ALTER TABLE alunos ADD COLUMN data_saida TEXT")

atualizar_banco()

# ==========================================
# CÁLCULO DE FREQUÊNCIA
# ==========================================
def calcular_frequencia(aluno_id):
    dados = executar_query("SELECT status FROM presenca_alunos WHERE aluno_id = ?", (aluno_id,), retornar_dados=True)
    if not dados or len(dados) == 0: return 0
    presentes = sum(1 for d in dados if d[0] == 'Presente')
    return (presentes / len(dados)) * 100

# ==========================================
# INTERFACE E LÓGICA (Simplificada para o seu fluxo)
# ==========================================
# [Manter a parte de login e menu lateral original...]

# --- TRABALHADORES (Modificado) ---
# Substitua o trecho original dos trabalhadores por este:
"""
# Dentro do Expander de Cadastro:
endereco = col1.text_input("Endereço")
whatsapp = col2.text_input("WhatsApp")
data_adm = col1.date_input("Data Admissão")
data_sai = col2.date_input("Data Desligamento", value=None)

# No INSERT:
executar_query("INSERT INTO trabalhadores (nome, funcao, endereco, telefone, data_admissao, data_saida, status, termo_pdf) VALUES (?,?,?,?,?,?,'Ativo',?)", 
               (nome_trab, funcao_trab, endereco, whatsapp, str(data_adm), str(data_sai), caminho_salvar_pdf))
"""

# --- ALUNOS (Modificado) ---
# Adicione a exibição da frequência na listagem:
"""
for id_aluno, nome, curso in executar_query("SELECT id, nome, curso FROM alunos", retornar_dados=True):
    freq = calcular_frequencia(id_aluno)
    st.write(f"**{nome}** - Curso: {curso} | **Frequência: {freq:.1f}%**")
"""

# --- CHAMADA (Nova funcionalidade) ---
# Adicione uma nova opção no menu "opcoes_menu" chamada "✅ Chamada"
# E no código principal:
"""
elif "✅ Chamada" in aba_selecionada:
    st.subheader("Registrar Presença")
    alunos = executar_query("SELECT id, nome FROM alunos", retornar_dados=True)
    for id_a, nome in alunos:
        status = st.radio(f"{nome}", ["Presente", "Falta"], key=f"aluno_{id_a}", horizontal=True)
        if st.button("Gravar", key=f"btn_{id_a}"):
            executar_query("INSERT INTO presenca_alunos (aluno_id, data_aula, status) VALUES (?,?,?)", (id_a, str(datetime.now().date()), status))
"""
