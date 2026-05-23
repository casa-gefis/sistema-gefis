# ==========================================
# LOGIN E CONTROLE DE NÍVEL
# ==========================================
if 'logado' not in st.session_state: 
    st.session_state.logado = False
    st.session_state.nivel = ""

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        # Busca o nível no banco
        usuario_db = executar_query("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (u, s), True)
        if usuario_db:
            st.session_state.logado = True
            st.session_state.nivel = usuario_db[0][0]
            st.rerun()
        else: 
            st.error("Usuário ou senha incorretos!")
else:
    # Sidebar segura
    with st.sidebar:
        nivel_atual = st.session_state.get('nivel', 'usuario')
        st.write(f"🔑 Nível: {str(nivel_atual).upper()}")
        aba = st.radio("Módulos:", ["🎙️ Palestrantes", "👥 Trabalhadores", "🎓 Alunos", "✅ Chamada"])
        
        if st.button("Sair"): 
            st.session_state.logado = False
            st.session_state.nivel = ""
            st.rerun()
