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
    
    # Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        password TEXT,
        rol TEXT,
        nombre TEXT
    )''')
    
    # Stock
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        droga TEXT,
        dosis TEXT,
        lote TEXT,
        vencimiento TEXT,
        cantidad INTEGER,
        temperatura TEXT,
        categoria TEXT,
        lab TEXT,
        notas TEXT
    )''')
    
    # Usuarios de prueba
    usuarios = [
        ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "Admin", "Administrador"),
        ("enfermeria", hashlib.sha256("123".encode()).hexdigest(), "Usuario", "Enfermería")
    ]
    for u in usuarios:
        c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", u)
    
    # Datos de ejemplo de stock (tomados de tu db.json)
    ejemplos = [
        ("5-Fluorouracilo", "500mg", "", "2026-06", 23, "ambiente", "citostático", "", ""),
        ("Capecitabina", "500mg", "", "2026-08", 1, "ambiente", "citostático", "", ""),
        ("Oxaliplatino", "100mg", "", "2026-08", 13, "ambiente", "citostático", "", ""),
        ("Ciclofosfamida", "1g", "035209", "2027-05", 4, "ambiente", "citostático", "Microsules", ""),
        ("Abraxane (nab-paclitaxel)", "100mg", "23L18NA", "2026-12", 9, "ambiente", "citostático", "Teva", ""),
        ("Irinotecan", "100mg", "", "2026-05", 26, "ambiente", "citostático", "", ""),
        ("Cisplatino", "50mg", "", "2026-10", 16, "ambiente", "citostático", "", ""),
        ("Gemcitabina", "1g", "", "2026-09", 41, "ambiente", "citostático", "", ""),
        ("Carboplatino", "450mg", "", "2026-02", 23, "ambiente", "citostático", "", ""),
        ("Carboplatino", "150mg", "", "2026-03", 42, "ambiente", "citostático", "", ""),
        ("Paclitaxel", "150mg", "07066", "2028-02", 3, "heladera", "citostático", "Kemex", "Refrigerado"),
        ("Bevacizumab", "100mg", "22698", "2027-06", 1, "heladera", "terapia dirigida", "Elea", ""),
        ("Bevacizumab", "400mg", "22026", "2027-02", 3, "heladera", "terapia dirigida", "Elea", ""),
        ("Trastuzumab", "440mg", "202410143", "2027-09", 3, "heladera", "terapia dirigida", "Elea", ""),
        ("Filgrastim", "30M", "", "2026-11", 10, "heladera", "soporte", "", ""),
    ]
    
    c.execute("SELECT COUNT(*) FROM stock")
    if c.fetchone()[0] == 0:
        for e in ejemplos:
            c.execute("INSERT INTO stock (droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, notas) VALUES (?,?,?,?,?,?,?,?,?)", e)
    
    conn.commit()
    conn.close()

init_db()

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧪 Stock Oncología – CIMA")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Iniciar Sesión")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar", type="primary"):
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

# ==================== SIDEBAR ====================
st.sidebar.success(f"👤 {st.session_state.username} ({st.session_state.rol})")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.logged_in = False
    st.rerun()

# Agregar usuarios (solo Admin)
if st.session_state.rol == "Admin":
    with st.sidebar.expander("➕ Agregar Nuevo Usuario"):
        new_user = st.text_input("Nuevo Usuario", key="new_user")
        new_pass = st.text_input("Contraseña", type="password", key="new_pass")
        new_rol = st.selectbox("Rol", ["Usuario", "Admin"], key="new_rol")
        new_nombre = st.text_input("Nombre Completo", key="new_nombre")
        if st.button("Crear Usuario"):
            if new_user and new_pass:
                conn = get_db()
                c = conn.cursor()
                hashed = hashlib.sha256(new_pass.encode()).hexdigest()
                try:
                    c.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (new_user, hashed, new_rol, new_nombre))
                    conn.commit()
                    st.success(f"Usuario '{new_user}' creado!")
                except:
                    st.error("El usuario ya existe")
                conn.close()

st.sidebar.info("App online – Datos en SQLite")

# ==================== MAIN ====================
st.title("Control de Stock Oncología - CIMA")
st.caption("Buenas prácticas JCI · Seguridad del paciente")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📦 Stock", "📝 Registrar Uso", "💡 Recomendaciones"])

# ---------- DASHBOARD ----------
with tab1:
    st.header("Dashboard")
    conn = get_db()
    stock_df = pd.read_sql_query("SELECT * FROM stock", conn)
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de registros", len(stock_df))
    with col2:
        bajo = len(stock_df[stock_df["cantidad"] <= 5]) if not stock_df.empty else 0
        st.metric("Stock bajo (≤5)", bajo)
    with col3:
        st.metric("Categorías", stock_df["categoria"].nunique() if not stock_df.empty else 0)
    
    if not stock_df.empty:
        st.subheader("Últimos registros de stock")
        st.dataframe(stock_df.head(10), use_container_width=True)

# ---------- STOCK ----------
with tab2:
    st.header("Gestión de Stock")
    
    conn = get_db()
    stock_df = pd.read_sql_query("SELECT * FROM stock ORDER BY droga", conn)
    conn.close()
    
    st.dataframe(stock_df, use_container_width=True)
    
    with st.expander("➕ Agregar nuevo fármaco al stock"):
        with st.form("form_stock"):
            col1, col2, col3 = st.columns(3)
            with col1:
                droga = st.text_input("Droga *")
                dosis = st.text_input("Dosis")
                lote = st.text_input("Lote")
            with col2:
                vencimiento = st.text_input("Vencimiento (AAAA-MM)")
                cantidad = st.number_input("Cantidad", min_value=0, value=1)
                temperatura = st.selectbox("Temperatura", ["ambiente", "heladera"])
            with col3:
                categoria = st.selectbox("Categoría", ["citostático", "terapia dirigida", "inmunoterapia", "soporte", "bomba", "otro"])
                lab = st.text_input("Laboratorio")
                notas = st.text_input("Notas")
            
            if st.form_submit_button("Guardar"):
                if droga:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""INSERT INTO stock 
                        (droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, notas)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                        (droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, notas))
                    conn.commit()
                    conn.close()
                    st.success("Fármaco agregado correctamente")
                    st.rerun()
                else:
                    st.error("La droga es obligatoria")

# ---------- REGISTRAR USO ----------
with tab3:
    st.header("Registrar Uso de Medicamentos")
    
    conn = get_db()
    stock_df = pd.read_sql_query("SELECT id, droga, dosis, cantidad FROM stock WHERE cantidad > 0 ORDER BY droga", conn)
    conn.close()
    
    if stock_df.empty:
        st.warning("No hay stock disponible para registrar uso.")
    else:
        with st.form("form_uso"):
            paciente = st.text_input("Nombre del paciente")
            droga_sel = st.selectbox("Medicamento", stock_df.apply(lambda x: f"{x['droga']} {x['dosis']} (Stock: {x['cantidad']})", axis=1))
            cantidad_uso = st.number_input("Cantidad a descontar", min_value=1, value=1)
            observaciones = st.text_area("Observaciones")
            
            if st.form_submit_button("Registrar uso y descontar stock"):
                if paciente:
                    # Extraer el id del medicamento seleccionado
                    idx = stock_df.index[stock_df.apply(lambda x: f"{x['droga']} {x['dosis']} (Stock: {x['cantidad']})", axis=1) == droga_sel][0]
                    id_med = stock_df.loc[idx, "id"]
                    
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("UPDATE stock SET cantidad = cantidad - ? WHERE id = ?", (cantidad_uso, id_med))
                    conn.commit()
                    conn.close()
                    st.success(f"Uso registrado para {paciente}. Stock actualizado.")
                    st.rerun()
                else:
                    st.error("Ingresá el nombre del paciente")

# ---------- RECOMENDACIONES ----------
with tab4:
    st.header("Recomendaciones Clínicas (JCI)")
    
    recomendaciones = {
        "Cisplatino": "Nefrotoxicidad · Hidratación obligatoria · Monitoreo de función renal",
        "Paclitaxel": "Premedicación con dexametasona · Riesgo de hipersensibilidad",
        "Bevacizumab": "Riesgo de hemorragia y perforación · Control de presión arterial",
        "Trastuzumab": "Cardiotoxicidad · Evaluación de FEVI antes de iniciar",
        "Oxaliplatino": "Neurotoxicidad · Evitar exposición al frío",
        "5-Fluorouracilo": "Mucositis · Diarrea · Monitoreo de toxicidad hematológica",
        "Carboplatino": "Mielosupresión · Ajuste de dosis según AUC y función renal",
        "Gemcitabina": "Toxicidad pulmonar · Monitoreo de función hepática"
    }
    
    for droga, texto in recomendaciones.items():
        with st.expander(droga):
            st.write(texto)

st.caption("Sistema de Stock Oncología · CIMA · Hospital de Día")