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
        donante TEXT,
        notas TEXT,
        registrado_por TEXT,
        fecha TEXT
    )''')
    for col in ["donante", "registrado_por", "fecha"]:
        try:
            c.execute(f"ALTER TABLE stock ADD COLUMN {col} TEXT")
        except Exception:
            pass

    # Recomendaciones (en DB para poder editarlas)
    c.execute('''CREATE TABLE IF NOT EXISTS recomendaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        droga TEXT,
        texto TEXT
    )''')
    for col in ["droga", "texto"]:
        try:
            c.execute(f"ALTER TABLE recomendaciones ADD COLUMN {col} TEXT")
        except Exception:
            pass

    # Usuarios de prueba
    usuarios = [
        ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "Admin", "Administrador"),
        ("enfermeria", hashlib.sha256("123".encode()).hexdigest(), "Usuario", "Enfermería")
    ]
    for u in usuarios:
        c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", u)

    # Datos de ejemplo de stock
    c.execute("SELECT COUNT(*) FROM stock")
    if c.fetchone()[0] == 0:
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
        for e in ejemplos:
            c.execute("INSERT INTO stock (droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, notas) VALUES (?,?,?,?,?,?,?,?,?)", e)

    # Recomendaciones por defecto
    c.execute("SELECT COUNT(*) FROM recomendaciones")
    if c.fetchone()[0] == 0:
        rec_defaults = [
            ("Cisplatino", "Nefrotoxicidad · Hidratación obligatoria · Monitoreo de función renal"),
            ("Paclitaxel", "Premedicación con dexametasona · Riesgo de hipersensibilidad"),
            ("Bevacizumab", "Riesgo de hemorragia y perforación · Control de presión arterial"),
            ("Trastuzumab", "Cardiotoxicidad · Evaluación de FEVI antes de iniciar"),
            ("Oxaliplatino", "Neurotoxicidad · Evitar exposición al frío"),
            ("5-Fluorouracilo", "Mucositis · Diarrea · Monitoreo de toxicidad hematológica"),
            ("Carboplatino", "Mielosupresión · Ajuste de dosis según AUC y función renal"),
            ("Gemcitabina", "Toxicidad pulmonar · Monitoreo de función hepática"),
        ]
        for r in rec_defaults:
            c.execute("INSERT INTO recomendaciones (droga, texto) VALUES (?,?)", r)

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
                except Exception:
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

    # Editor editable
    edited_df = st.data_editor(
        stock_df,
        use_container_width=True,
        num_rows="dynamic",
        key="stock_editor"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Guardar cambios", type="primary"):
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM stock")
            for _, row in edited_df.iterrows():
                c.execute("""INSERT INTO stock
                    (id, droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, donante, notas, registrado_por, fecha)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        row.get("id"),
                        row.get("droga"),
                        row.get("dosis"),
                        row.get("lote"),
                        row.get("vencimiento"),
                        row.get("cantidad"),
                        row.get("temperatura"),
                        row.get("categoria"),
                        row.get("lab"),
                        row.get("donante"),
                        row.get("notas"),
                        row.get("registrado_por"),
                        row.get("fecha")
                    ))
            conn.commit()
            conn.close()
            st.success("Cambios guardados correctamente")
            st.rerun()

    with col2:
        if st.button("🔄 Actualizar vista"):
            st.rerun()

    st.divider()

    # ===== DAR DE BAJA =====
    st.subheader("🗑️ Dar de baja un fármaco")

    if not stock_df.empty:
        opciones = stock_df.apply(
            lambda x: f"ID {x['id']} | {x['droga']} {x['dosis']} | Lote: {x['lote']} | Cant: {x['cantidad']}",
            axis=1
        ).tolist()

        seleccionado = st.selectbox("Seleccionar fármaco a dar de baja", opciones)
        motivo = st.selectbox("Motivo de baja", ["Vencimiento", "Rotura", "Pérdida", "Otro"])
        observaciones_baja = st.text_input("Observaciones (opcional)")

        if st.button("Confirmar baja", type="secondary"):
            id_baja = int(seleccionado.split("|")[0].replace("ID ", "").strip())

            conn = get_db()
            c = conn.cursor()
            c.execute("""UPDATE stock SET cantidad = 0,
                          notas = COALESCE(notas, '') || ' | BAJA: ' || ? || ' - ' || ?
                          WHERE id = ?""",
                      (motivo, observaciones_baja or "Sin observaciones", id_baja))
            conn.commit()
            conn.close()
            st.success(f"Fármaco dado de baja por: {motivo}")
            st.rerun()
    else:
        st.info("No hay stock para dar de baja.")

    st.divider()

    # ===== AGREGAR NUEVO =====
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
                        (droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, notas, registrado_por, fecha)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, notas,
                         st.session_state.username, datetime.now().strftime("%Y-%m-%d")))
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
    stock_uso = pd.read_sql_query("SELECT id, droga, dosis, cantidad FROM stock WHERE cantidad > 0 ORDER BY droga", conn)
    conn.close()

    if stock_uso.empty:
        st.warning("No hay stock disponible para registrar uso.")
    else:
        with st.form("form_uso"):
            paciente = st.text_input("Nombre del paciente")
            opciones = stock_uso.apply(lambda x: f"{x['droga']} {x['dosis']} (Stock: {x['cantidad']})", axis=1).tolist()
            droga_sel = st.selectbox("Medicamento", opciones)
            cantidad_uso = st.number_input("Cantidad a descontar", min_value=1, value=1)
            observaciones = st.text_area("Observaciones")

            if st.form_submit_button("Registrar uso y descontar stock"):
                if paciente:
                    idx = opciones.index(droga_sel)
                    id_med = stock_uso.iloc[idx]["id"]
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

    conn = get_db()
    rec_df = pd.read_sql_query("SELECT * FROM recomendaciones ORDER BY droga", conn)
    conn.close()

    for _, row in rec_df.iterrows():
        with st.expander(f"📋 {row['droga']}"):
            st.write(row["texto"])
            if st.session_state.rol == "Admin":
                st.divider()
                nuevo_texto = st.text_area("Editar recomendación", value=row["texto"], key=f"rec_txt_{row['id']}")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("💾 Guardar", key=f"save_rec_{row['id']}"):
                        conn = get_db()
                        conn.execute("UPDATE recomendaciones SET texto=? WHERE id=?", (nuevo_texto, row["id"]))
                        conn.commit()
                        conn.close()
                        st.success("Guardado")
                        st.rerun()
                with col2:
                    if st.button("🗑️ Eliminar", key=f"del_rec_{row['id']}"):
                        conn = get_db()
                        conn.execute("DELETE FROM recomendaciones WHERE id=?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()

    if st.session_state.rol == "Admin":
        st.divider()
        with st.expander("➕ Agregar nueva recomendación"):
            with st.form("form_rec"):
                nueva_droga = st.text_input("Droga")
                nuevo_texto_add = st.text_area("Texto de recomendación")
                if st.form_submit_button("Agregar"):
                    if nueva_droga and nuevo_texto_add:
                        conn = get_db()
                        conn.execute("INSERT INTO recomendaciones (droga, texto) VALUES (?,?)", (nueva_droga, nuevo_texto_add))
                        conn.commit()
                        conn.close()
                        st.success("Recomendación agregada")
                        st.rerun()
                    else:
                        st.error("Completá todos los campos")

st.caption("Sistema de Stock Oncología · CIMA · Hospital de Día")
