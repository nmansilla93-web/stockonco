import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

st.set_page_config(page_title="Stock Oncología CIMA", layout="wide", page_icon="🧪")

DB_PATH = "oncologia.db"

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        password TEXT,
        rol TEXT,
        nombre TEXT
    )''')
    # Usuarios de prueba
    usuarios = [
        ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "Admin", "Administrador"),
        ("enfermeria", hashlib.sha256("123".encode()).hexdigest(), "Usuario", "Enfermería")
    ]
    for u in usuarios:
        c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", u)
    conn.commit()
    conn.close()

init_db()

# Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧪 Stock Oncología – CIMA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Iniciar Sesión")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            conn = get_db()
            df = pd.read_sql_query("SELECT * FROM usuarios WHERE username=?", conn, params=(username,))
            conn.close()
            if not df.empty and df.iloc[0]["password"] == hashlib.sha256(password.encode()).hexdigest():
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.rol = df.iloc[0]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# App principal
st.sidebar.success(f"👤 {st.session_state.username} ({st.session_state.rol})")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.logged_in = False
    st.rerun()

st.title("Control de Stock Oncología - CIMA")
st.caption("Buenas prácticas JCI · Seguridad del paciente")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📦 Stock", "📝 Registrar Uso", "💡 Recomendaciones"])

with tab1:
    st.header("Dashboard")
    st.info("Bienvenido. Aquí verás alertas y resúmenes.")

with tab2:
    st.header("Gestión de Stock")
    st.write("Aquí se cargará el stock de fármacos.")

with tab3:
    st.header("Registrar Uso")
    st.write("Registro de administración de medicamentos.")

with tab4:
    st.header("Recomendaciones Clínicas")
    st.write("Guías de medicamentos oncológicos.")

st.sidebar.info("App online – Datos en SQLite")