import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib

st.set_page_config(page_title="Stock Oncología CIMA", layout="wide", page_icon="🧪")

DB_PATH = "oncologia.db"


def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def parse_venc(valor):
    if valor is None or str(valor).strip() in ("", "nan", "None"):
        return None
    texto = str(valor)[:10]
    for fmt in ("%Y-%m-%d", "%Y-%m", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto if fmt != "%Y-%m" else texto[:7], fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(valor, errors="coerce").date()
    except Exception:
        return None


def estado_venc(valor):
    d = parse_venc(valor)
    if d is None:
        return "sin_fecha"
    hoy = date.today()
    if d < hoy:
        return "vencido"
    if d <= hoy + pd.Timedelta(days=30):
        return "30"
    if d <= hoy + pd.Timedelta(days=90):
        return "90"
    return "ok"


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        password TEXT,
        rol TEXT,
        nombre TEXT
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origen TEXT DEFAULT 'donacion',
        paciente TEXT DEFAULT '',
        droga TEXT,
        dosis TEXT,
        lote TEXT,
        vencimiento TEXT,
        cantidad INTEGER DEFAULT 0,
        temperatura TEXT,
        categoria TEXT,
        lab TEXT,
        donante TEXT DEFAULT '',
        notas TEXT DEFAULT '',
        registrado_por TEXT DEFAULT '',
        fecha TEXT DEFAULT ''
    )"""
    )
    # Migrations para DBs con schema anterior (sin origen/paciente)
    for col, default in [("origen", "'donacion'"), ("paciente", "''")]:
        try:
            c.execute(f"ALTER TABLE stock ADD COLUMN {col} TEXT DEFAULT {default}")
        except Exception:
            pass

    c.execute(
        """CREATE TABLE IF NOT EXISTS recomendaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        droga TEXT UNIQUE,
        texto TEXT
    )"""
    )
    # Migration por si la tabla existía sin columnas correctas
    for col in ["droga", "texto"]:
        try:
            c.execute(f"ALTER TABLE recomendaciones ADD COLUMN {col} TEXT")
        except Exception:
            pass

    c.execute(
        """CREATE TABLE IF NOT EXISTS bajas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_id INTEGER,
        droga TEXT,
        dosis TEXT,
        lote TEXT,
        cantidad INTEGER,
        motivo TEXT,
        observaciones TEXT,
        usuario TEXT,
        fecha TEXT
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS usos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        paciente TEXT,
        droga TEXT,
        dosis TEXT,
        lote TEXT,
        cantidad INTEGER,
        origen TEXT,
        observaciones TEXT,
        usuario TEXT
    )"""
    )

    usuarios = [
        ("admin", hash_pw("admin123"), "Admin", "Administrador"),
        ("enfermeria", hash_pw("123"), "Usuario", "Enfermería"),
    ]
    for u in usuarios:
        c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", u)

    recs = [
        ("Cisplatino", "Nefrotoxicidad. Hidratación obligatoria. Monitoreo de función renal."),
        ("Paclitaxel", "Premedicación con dexametasona. Riesgo de hipersensibilidad."),
        ("Bevacizumab", "Riesgo de hemorragia y perforación. Control de presión arterial."),
        ("Trastuzumab", "Cardiotoxicidad. Evaluación de FEVI antes de iniciar."),
        ("Oxaliplatino", "Neurotoxicidad. Evitar exposición al frío."),
        ("5-Fluorouracilo", "Mucositis y diarrea. Monitoreo hematológico."),
        ("Carboplatino", "Mielosupresión. Ajuste de dosis según AUC y función renal."),
        ("Gemcitabina", "Toxicidad pulmonar. Monitoreo de función hepática."),
        ("Ciclofosfamida", "Cistitis hemorrágica. Hidratación y mesna según protocolo."),
        ("Irinotecan", "Diarrea precoz y tardía. Atropina / loperamida según momento."),
    ]
    for r in recs:
        c.execute("INSERT OR IGNORE INTO recomendaciones (droga, texto) VALUES (?,?)", r)

    c.execute("SELECT COUNT(*) FROM stock")
    if c.fetchone()[0] == 0:
        seed = [
            ("5FU", "500mg x 5 ampollas", "025164", "2027-08-01", 3, "ambiente", "citostático", "Microsules"),
            ("5FU", "500mg x 5 ampollas", "026170", "2028-03-01", 3, "ambiente", "citostático", "Microsules"),
            ("5FU", "500mg x 5 ampollas", "065571", "2017-10-01", 6, "ambiente", "citostático", "Microsules"),
            ("5FU", "500mg x 5 ampollas", "06600", "2027-08-01", 5, "ambiente", "citostático", "Kemex"),
            ("5FU", "500mg x 5 ampollas", "06720", "2027-09-01", 2, "ambiente", "citostático", "Kemex"),
            ("5FU", "500mg x 5 ampollas", "06771", "2017-10-01", 4, "ambiente", "citostático", "Kemex"),
            ("5FU", "500mg x 5 ampollas", "06937", "2027-12-01", 2, "ambiente", "citostático", "Kemex"),
            ("5FU", "500mg x 5 ampollas", "07090", "2028-02-01", 2, "ambiente", "citostático", "Kemex"),
            ("5FU", "500mg x 5 ampollas", "07141", "2028-03-01", 1, "ambiente", "citostático", "Kemex"),
            ("5FU", "500mg x 5 ampollas", "095871", "2027-11-01", 5, "ambiente", "citostático", "Microsules"),
            ("5FU", "500mg x 5 ampollas", "104899", "2027-02-01", 1, "ambiente", "citostático", "Microsules"),
            ("5FU", "500mg x 5 ampollas", "115092", "2027-12-01", 1, "ambiente", "citostático", "Microsules"),
            ("Aprepitant", "125mg/80mg", "B118828", "2027-01-01", 1, "ambiente", "soporte", "MSD"),
            ("Aprepitant", "125mg/80mg", "C124118", "2027-01-02", 1, "ambiente", "soporte", "MSD"),
            ("Aprepitant", "125mg/80mg", "C125875", "2027-10-01", 1, "ambiente", "soporte", "MSD"),
            ("Bleomicina", "15UI", "M363A", "2026-10-01", 4, "ambiente", "citostático", "Knight"),
            ("Bleomicina", "15UI", "M419A/01", "2026-12-01", 2, "ambiente", "citostático", "Knight"),
            ("Capecitabina", "500", "CA0198", "2027-04-01", 1, "ambiente", "citostático", "Exane"),
            ("Capecitabina", "500", "M522A", "2026-12-01", 1, "ambiente", "citostático", "Knight"),
            ("Carboplatino", "150", "015012", "2027-01-01", 7, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "150", "025124", "2027-03-01", 4, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "150", "06995", "2028-01-01", 1, "ambiente", "citostático", "Kemex"),
            ("Carboplatino", "150", "114934", "2026-12-01", 2, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "150", "31250010", "2026-12-01", 5, "ambiente", "citostático", "Glenmark"),
            ("Carboplatino", "150", "CA187B", "2027-11-01", 2, "ambiente", "citostático", "Tuteur"),
            ("Carboplatino", "450", "045299", "2027-05-01", 2, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "450", "054335", "2026-08-01", 1, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "450", "06365", "2027-04-01", 3, "ambiente", "citostático", "Kemex"),
            ("Carboplatino", "450", "06430", "2027-05-01", 2, "ambiente", "citostático", "Kemex"),
            ("Carboplatino", "450", "065506", "2027-06-01", 4, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "450", "06766", "2027-10-01", 5, "ambiente", "citostático", "Kemex"),
            ("Carboplatino", "450", "06873", "2027-11-01", 3, "ambiente", "citostático", "Kemex"),
            ("Carboplatino", "450", "094732", "2026-11-01", 1, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "450", "095803", "2027-09-01", 1, "ambiente", "citostático", "Microsules"),
            ("Carboplatino", "450", "1216A01", "2027-02-01", 3, "ambiente", "citostático", "GP Pharm"),
            ("Carboplatino", "450", "4008/C", "2027-08-01", 1, "ambiente", "citostático", "Laboratorio IMA"),
            ("Carboplatino", "450", "AAAI2B", "2027-09-01", 1, "ambiente", "citostático", "Laboratorio Richmond"),
            ("Carboplatino", "450", "CA186C", "2026-10-01", 1, "ambiente", "citostático", "Tuteur"),
            ("Carboplatino", "450", "CA187B", "2028-10-01", 3, "ambiente", "citostático", "Tuteur"),
            ("Ciclofosfamida", "1000", "05893", "2026-09-01", 2, "ambiente", "citostático", "Kemex"),
            ("Ciclofosfamida", "1000", "05984", "2026-10-01", 1, "ambiente", "citostático", "Kemex"),
            ("Ciclofosfamida", "1000", "1167A02", "2026-11-01", 2, "ambiente", "citostático", "GP Pharm"),
            ("Ciclofosfamida", "1000", "1188A01", "2026-12-01", 1, "ambiente", "citostático", "GP Pharm"),
            ("Ciclofosfamida", "1000", "1193A03", "2026-12-01", 1, "ambiente", "citostático", "GP Pharm"),
            ("Ciclofosfamida", "1000", "1223A01", "2027-03-01", 5, "ambiente", "citostático", "GP Pharm"),
            ("Ciclofosfamida", "1000", "124033", "2027-04-01", 1, "ambiente", "citostático", "Microsules"),
            ("Ciclofosfamida", "1000", "74505", "2026-09-01", 1, "ambiente", "citostático", "Microsules"),
            ("Ciclofosfamida", "1000", "84609", "2026-09-01", 1, "ambiente", "citostático", "Microsules"),
            ("Ciclofosfamida", "1000", "85710", "2027-10-01", 1, "ambiente", "citostático", "Microsules"),
            ("Ciclofosfamida", "1000", "95805", "2027-10-01", 1, "ambiente", "citostático", "Microsules"),
            ("Cisplatino", "50", "M979A", "2027-10-01", 3, "ambiente", "citostático", "Knight"),
            ("Cisplatino", "50", "M991A", "2027-10-02", 2, "ambiente", "citostático", "Knight"),
            ("Eribulina", "0.5", "7422", "2027-06-01", 1, "ambiente", "citostático", "Elea"),
            ("Etoposido", "100", "2410173-1", "2027-11-01", 2, "ambiente", "citostático", "Bago Pharma"),
            ("Gemcitabina", "1000", "016038", "2028-03-01", 2, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "025177", "2027-04-01", 1, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "035256", "2027-04-01", 2, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "045344", "2027-05-01", 4, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "045345", "2027-11-01", 1, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "055452", "2027-08-01", 2, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "06321", "2027-03-01", 2, "ambiente", "citostático", "Kemex"),
            ("Gemcitabina", "1000", "06424", "2027-05-01", 3, "ambiente", "citostático", "Kemex"),
            ("Gemcitabina", "1000", "06622", "2027-08-01", 2, "ambiente", "citostático", "Kemex"),
            ("Gemcitabina", "1000", "105934", "2027-11-02", 3, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "115054", "2027-12-01", 4, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "125128", "2028-03-01", 1, "ambiente", "citostático", "Microsules"),
            ("Gemcitabina", "1000", "31250082", "2027-06-01", 6, "ambiente", "citostático", "Glenmark"),
            ("Gemcitabina", "1000", "31250104", "2027-08-01", 2, "ambiente", "citostático", "Glenmark"),
            ("Irinotecan", "100", "1211A02", "2027-02-01", 2, "ambiente", "citostático", "GP Pharm"),
            ("Irinotecan", "100", "31250089", "2027-07-01", 1, "ambiente", "citostático", "Glenmark"),
            ("Leucovorina", "50", "025150", "2027-04-01", 31, "ambiente", "soporte", "Microsules"),
            ("Leucovorina", "50", "085749", "2027-08-01", 12, "ambiente", "soporte", "Microsules"),
            ("Oxaliplatino", "100", "06272", "2027-03-01", 1, "ambiente", "citostático", "Kemex"),
            ("Oxaliplatino", "100", "06328", "2027-04-01", 1, "ambiente", "citostático", "Kemex"),
            ("Oxaliplatino", "100", "06468", "2027-06-01", 3, "ambiente", "citostático", "Kemex"),
            ("Oxaliplatino", "100", "06770", "2027-10-01", 2, "ambiente", "citostático", "Kemex"),
            ("Oxaliplatino", "100", "06919", "2027-12-01", 6, "ambiente", "citostático", "Kemex"),
            ("Oxaliplatino", "100", "105932", "2027-05-01", 3, "ambiente", "citostático", "Microsules"),
            ("Oxaliplatino", "100", "31250106", "2027-09-01", 2, "ambiente", "citostático", "Glenmark"),
            ("Oxaliplatino", "100", "M833A/1", "2027-05-01", 1, "ambiente", "citostático", "Knight"),
            ("Oxaliplatino", "50", "1231A05", "2027-04-01", 1, "ambiente", "citostático", "GP Pharm"),
            ("Oxaliplatino", "50", "31250056", "2027-04-01", 1, "ambiente", "citostático", "Glenmark"),
            ("Pemetrexed", "500", "06851", "2027-11-01", 2, "ambiente", "citostático", "Kemex"),
            ("Pemetrexed", "500", "07017", "2028-01-01", 4, "ambiente", "citostático", "Kemex"),
            ("Pemetrexed", "500", "31240149", "2026-09-01", 4, "ambiente", "citostático", "Glenmarck"),
            ("Pemetrexed", "500", "31250120", "2027-10-01", 4, "ambiente", "citostático", "Glenmarck"),
        ]
        for s in seed:
            c.execute(
                """INSERT INTO stock
                (origen, paciente, droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, registrado_por, fecha)
                VALUES ('donacion','',?,?,?,?,?,?,?,?,?,?)""",
                (*s, "Sistema", datetime.now().strftime("%Y-%m-%d")),
            )
    conn.commit()
    conn.close()


def leer_stock(origen=None):
    conn = get_db()
    if origen:
        df = pd.read_sql_query(
            "SELECT * FROM stock WHERE origen=? ORDER BY droga, dosis",
            conn,
            params=(origen,),
        )
    else:
        df = pd.read_sql_query("SELECT * FROM stock ORDER BY droga, dosis", conn)
    conn.close()
    return df


def guardar_stock_editor(edited_df):
    conn = get_db()
    c = conn.cursor()
    for _, row in edited_df.iterrows():
        sid = row.get("id")
        vals = (
            str(row.get("origen") or "donacion"),
            str(row.get("paciente") or ""),
            str(row.get("droga") or ""),
            str(row.get("dosis") or ""),
            str(row.get("lote") or ""),
            str(row.get("vencimiento") or ""),
            int(row.get("cantidad") or 0),
            str(row.get("temperatura") or "ambiente"),
            str(row.get("categoria") or ""),
            str(row.get("lab") or ""),
            str(row.get("donante") or ""),
            str(row.get("notas") or ""),
            str(row.get("registrado_por") or st.session_state.get("username", "")),
            str(row.get("fecha") or datetime.now().strftime("%Y-%m-%d")),
        )
        if pd.isna(sid) or sid is None or str(sid).strip() == "":
            c.execute(
                """INSERT INTO stock
                (origen, paciente, droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, donante, notas, registrado_por, fecha)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                vals,
            )
        else:
            c.execute(
                """UPDATE stock SET
                origen=?, paciente=?, droga=?, dosis=?, lote=?, vencimiento=?, cantidad=?,
                temperatura=?, categoria=?, lab=?, donante=?, notas=?, registrado_por=?, fecha=?
                WHERE id=?""",
                vals + (int(sid),),
            )
    conn.commit()
    conn.close()


init_db()

# ---------- LOGIN ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🧪 Stock Oncología – CIMA")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.subheader("Iniciar Sesión")
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Ingresar", type="primary"):
            conn = get_db()
            df = pd.read_sql_query(
                "SELECT * FROM usuarios WHERE username=?", conn, params=(username,)
            )
            conn.close()
            if not df.empty and df.iloc[0]["password"] == hash_pw(password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.rol = df.iloc[0]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# ---------- SIDEBAR ----------
st.sidebar.success(f"👤 {st.session_state.username} ({st.session_state.rol})")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.logged_in = False
    st.rerun()

if st.session_state.rol == "Admin":
    with st.sidebar.expander("➕ Agregar usuario"):
        nu = st.text_input("Usuario nuevo", key="nu")
        npw = st.text_input("Contraseña", type="password", key="npw")
        nr = st.selectbox("Rol", ["Usuario", "Admin"], key="nr")
        nn = st.text_input("Nombre", key="nn")
        if st.button("Crear usuario"):
            if nu and npw:
                conn = get_db()
                try:
                    conn.execute(
                        "INSERT INTO usuarios VALUES (?,?,?,?)",
                        (nu, hash_pw(npw), nr, nn),
                    )
                    conn.commit()
                    st.success(f"Usuario {nu} creado")
                except sqlite3.IntegrityError:
                    st.error("El usuario ya existe")
                conn.close()

st.sidebar.caption("CIMA · Hospital de Día · JCI")

st.title("Control de Stock Oncología - CIMA")
st.caption("Donaciones institucionales · Stock de paciente · Alertas de vencimiento")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "📊 Dashboard",
        "🏥 Donaciones",
        "👤 Stock paciente",
        "📝 Registrar uso",
        "🔔 Alertas",
        "💡 Recomendaciones",
    ]
)

stock_all = leer_stock()
if not stock_all.empty:
    stock_all["est_venc"] = stock_all["vencimiento"].apply(estado_venc)
else:
    stock_all = stock_all.copy()
    stock_all["est_venc"] = pd.Series(dtype=str)

# ---------- DASHBOARD ----------
with tab1:
    st.header("Dashboard")
    don = stock_all[stock_all["origen"] == "donacion"] if not stock_all.empty else stock_all
    pac = stock_all[stock_all["origen"] == "paciente"] if not stock_all.empty else stock_all

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ítems donación", len(don))
    m2.metric("Ítems paciente", len(pac))
    m3.metric("Vencidos", int((stock_all["est_venc"] == "vencido").sum()) if not stock_all.empty else 0)
    m4.metric("Vencen <30 días", int((stock_all["est_venc"] == "30").sum()) if not stock_all.empty else 0)

    st.subheader("Totales por fármaco (todos los lotes)")
    if not stock_all.empty:
        tot = (
            stock_all.groupby(["droga", "dosis", "origen"], dropna=False)["cantidad"]
            .sum()
            .reset_index()
            .sort_values(["droga", "origen"])
        )
        st.dataframe(tot, hide_index=True, use_container_width=True)
    else:
        st.info("Sin stock cargado.")

# ---------- DONACIONES ----------
with tab2:
    st.header("Stock institucional (Donaciones)")
    df_don = leer_stock("donacion")
    st.info("Editá celdas (cantidad, lote, vencimiento, etc.) y pulsá Guardar cambios.")
    edited_don = st.data_editor(
        df_don,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "origen": st.column_config.SelectboxColumn("Origen", options=["donacion", "paciente"]),
            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0),
            "temperatura": st.column_config.SelectboxColumn("Temperatura", options=["ambiente", "heladera"]),
            "categoria": st.column_config.SelectboxColumn(
                "Categoría",
                options=["citostático", "terapia dirigida", "inmunoterapia", "soporte", "bomba", "otro"],
            ),
        },
        key="ed_don",
    )
    if st.button("💾 Guardar cambios donaciones", type="primary"):
        guardar_stock_editor(edited_don)
        st.success("Guardado")
        st.rerun()

    st.divider()
    st.subheader("Asignar donación a paciente")
    if not df_don.empty:
        opts = df_don.apply(
            lambda x: f"{x['id']}| {x['droga']} {x['dosis']} lote {x['lote']} cant {x['cantidad']}",
            axis=1,
        ).tolist()
        sel = st.selectbox("Ítem", opts, key="asig_sel")
        pac_nom = st.text_input("Paciente (apellido y nombre)", key="asig_pac")
        cant_asig = st.number_input("Cantidad a asignar", min_value=1, value=1, key="asig_cant")
        if st.button("Asignar a paciente"):
            sid = int(str(sel).split("|")[0])
            fila = df_don[df_don["id"] == sid].iloc[0]
            if cant_asig > int(fila["cantidad"]):
                st.error("No hay stock suficiente")
            elif not pac_nom.strip():
                st.error("Ingresá el paciente")
            else:
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE stock SET cantidad = cantidad - ? WHERE id=?", (cant_asig, sid))
                c.execute(
                    """INSERT INTO stock
                    (origen, paciente, droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, donante, notas, registrado_por, fecha)
                    VALUES ('paciente',?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        pac_nom.strip(),
                        fila["droga"],
                        fila["dosis"],
                        fila["lote"],
                        fila["vencimiento"],
                        cant_asig,
                        fila["temperatura"],
                        fila["categoria"],
                        fila["lab"],
                        fila.get("donante", ""),
                        "Asignado desde donación",
                        st.session_state.username,
                        datetime.now().strftime("%Y-%m-%d"),
                    ),
                )
                conn.commit()
                conn.close()
                st.success("Asignado")
                st.rerun()

    st.divider()
    st.subheader("Dar de baja")
    if not df_don.empty:
        opts_b = df_don.apply(
            lambda x: f"{x['id']}| {x['droga']} {x['dosis']} lote {x['lote']} cant {x['cantidad']}",
            axis=1,
        ).tolist()
        sel_b = st.selectbox("Ítem a dar de baja", opts_b, key="baja_sel")
        mot = st.selectbox("Motivo", ["Vencimiento", "Rotura", "Pérdida", "Otro"], key="baja_mot")
        obs = st.text_input("Observaciones", key="baja_obs")
        cant_b = st.number_input("Cantidad a dar de baja", min_value=1, value=1, key="baja_cant")
        if st.button("Confirmar baja"):
            sid = int(str(sel_b).split("|")[0])
            fila = df_don[df_don["id"] == sid].iloc[0]
            cant_baja = min(cant_b, int(fila["cantidad"]))
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE stock SET cantidad = cantidad - ? WHERE id=?", (cant_baja, sid))
            c.execute(
                """INSERT INTO bajas (stock_id, droga, dosis, lote, cantidad, motivo, observaciones, usuario, fecha)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    sid,
                    fila["droga"],
                    fila["dosis"],
                    fila["lote"],
                    cant_baja,
                    mot,
                    obs,
                    st.session_state.username,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
            conn.commit()
            conn.close()
            st.success(f"Baja registrada: {mot}")
            st.rerun()

# ---------- STOCK PACIENTE ----------
with tab3:
    st.header("Stock propio del paciente")
    df_pac = leer_stock("paciente")
    edited_pac = st.data_editor(
        df_pac,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "origen": st.column_config.SelectboxColumn("Origen", options=["paciente", "donacion"]),
            "cantidad": st.column_config.NumberColumn("Cantidad", min_value=0),
            "temperatura": st.column_config.SelectboxColumn("Temperatura", options=["ambiente", "heladera"]),
        },
        key="ed_pac",
    )
    if st.button("💾 Guardar cambios stock paciente", type="primary"):
        guardar_stock_editor(edited_pac)
        st.success("Guardado")
        st.rerun()

    st.divider()
    st.subheader("Devolver stock de paciente a donación")
    if not df_pac.empty:
        opts_p = df_pac.apply(
            lambda x: f"{x['id']}| {x.get('paciente', '')} | {x['droga']} {x['dosis']} cant {x['cantidad']}",
            axis=1,
        ).tolist()
        sel_p = st.selectbox("Ítem del paciente", opts_p, key="dev_sel")
        cant_d = st.number_input("Cantidad a devolver", min_value=1, value=1, key="dev_cant")
        if st.button("Pasar a donación"):
            sid = int(str(sel_p).split("|")[0])
            fila = df_pac[df_pac["id"] == sid].iloc[0]
            if cant_d > int(fila["cantidad"]):
                st.error("Cantidad mayor al stock del paciente")
            else:
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE stock SET cantidad = cantidad - ? WHERE id=?", (cant_d, sid))
                c.execute(
                    """INSERT INTO stock
                    (origen, paciente, droga, dosis, lote, vencimiento, cantidad, temperatura, categoria, lab, notas, registrado_por, fecha)
                    VALUES ('donacion','',?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        fila["droga"],
                        fila["dosis"],
                        fila["lote"],
                        fila["vencimiento"],
                        cant_d,
                        fila["temperatura"],
                        fila["categoria"],
                        fila["lab"],
                        f"Devuelto desde paciente {fila.get('paciente', '')}",
                        st.session_state.username,
                        datetime.now().strftime("%Y-%m-%d"),
                    ),
                )
                conn.commit()
                conn.close()
                st.success("Movido a donaciones")
                st.rerun()

# ---------- REGISTRAR USO ----------
with tab4:
    st.header("Registrar uso")
    origen_uso = st.radio("Origen del medicamento", ["donacion", "paciente"], horizontal=True)
    df_disp = leer_stock(origen_uso)
    df_disp = df_disp[df_disp["cantidad"] > 0] if not df_disp.empty else df_disp
    if df_disp.empty:
        st.warning("No hay stock disponible en ese origen.")
    else:
        with st.form("form_uso"):
            paciente_u = st.text_input("Paciente")
            labels = df_disp.apply(
                lambda x: f"{x['id']}| {x['droga']} {x['dosis']} lote {x['lote']} cant {x['cantidad']}",
                axis=1,
            ).tolist()
            med = st.selectbox("Medicamento", labels)
            cant_u = st.number_input("Cantidad", min_value=1, value=1)
            obs_u = st.text_area("Observaciones")
            if st.form_submit_button("Registrar y descontar"):
                if not paciente_u.strip():
                    st.error("Ingresá el paciente")
                else:
                    sid = int(str(med).split("|")[0])
                    fila = df_disp[df_disp["id"] == sid].iloc[0]
                    if cant_u > int(fila["cantidad"]):
                        st.error("Stock insuficiente")
                    else:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("UPDATE stock SET cantidad = cantidad - ? WHERE id=?", (cant_u, sid))
                        c.execute(
                            """INSERT INTO usos (fecha, paciente, droga, dosis, lote, cantidad, origen, observaciones, usuario)
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            (
                                datetime.now().strftime("%Y-%m-%d %H:%M"),
                                paciente_u.strip(),
                                fila["droga"],
                                fila["dosis"],
                                fila["lote"],
                                cant_u,
                                origen_uso,
                                obs_u,
                                st.session_state.username,
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.success("Uso registrado y stock descontado")
                        st.rerun()

    conn = get_db()
    hist = pd.read_sql_query("SELECT * FROM usos ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    st.subheader("Últimos usos")
    st.dataframe(hist, hide_index=True, use_container_width=True)

# ---------- ALERTAS ----------
with tab5:
    st.header("Alertas de vencimiento")
    if stock_all.empty:
        st.success("Sin stock cargado.")
    else:
        vencidos = stock_all[stock_all["est_venc"] == "vencido"]
        d30 = stock_all[stock_all["est_venc"] == "30"]
        d90 = stock_all[stock_all["est_venc"] == "90"]
        cols_alerta = ["origen", "paciente", "droga", "dosis", "lote", "vencimiento", "cantidad"]
        if not vencidos.empty:
            st.error(f"VENCIDOS ({len(vencidos)})")
            st.dataframe(vencidos[cols_alerta], hide_index=True, use_container_width=True)
        if not d30.empty:
            st.warning(f"Vencen en menos de 30 días ({len(d30)})")
            st.dataframe(d30[cols_alerta], hide_index=True, use_container_width=True)
        if not d90.empty:
            st.info(f"Vencen en 30–90 días ({len(d90)})")
            st.dataframe(d90[cols_alerta], hide_index=True, use_container_width=True)
        if vencidos.empty and d30.empty and d90.empty:
            st.success("Sin alertas de vencimiento.")

    conn = get_db()
    bajas_df = pd.read_sql_query("SELECT * FROM bajas ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    st.subheader("Historial de bajas")
    st.dataframe(bajas_df, hide_index=True, use_container_width=True)

# ---------- RECOMENDACIONES ----------
with tab6:
    st.header("Recomendaciones clínicas")
    conn = get_db()
    rec_df = pd.read_sql_query("SELECT * FROM recomendaciones ORDER BY droga", conn)
    conn.close()

    for _, row in rec_df.iterrows():
        droga_rec = row.get("droga", "") or ""
        texto_rec = row.get("texto", "") or ""
        rid = row.get("id")
        with st.expander(str(droga_rec)):
            st.write(texto_rec)
            if st.session_state.rol == "Admin" and rid is not None:
                nuevo = st.text_area("Editar texto", value=texto_rec, key=f"rec_{rid}")
                if st.button("Guardar recomendación", key=f"btn_rec_{rid}"):
                    conn = get_db()
                    conn.execute("UPDATE recomendaciones SET texto=? WHERE id=?", (nuevo, int(rid)))
                    conn.commit()
                    conn.close()
                    st.success("Actualizado")
                    st.rerun()

    with st.expander("➕ Nueva recomendación"):
        nd = st.text_input("Fármaco", key="nr_d")
        nt = st.text_area("Texto / precauciones", key="nr_t")
        if st.button("Agregar recomendación"):
            if nd.strip() and nt.strip():
                conn = get_db()
                try:
                    conn.execute(
                        "INSERT INTO recomendaciones (droga, texto) VALUES (?,?)",
                        (nd.strip(), nt.strip()),
                    )
                    conn.commit()
                    st.success("Agregada")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Ese fármaco ya tiene recomendación")
                conn.close()
            else:
                st.error("Completá fármaco y texto")
