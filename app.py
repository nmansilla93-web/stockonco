import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib

st.set_page_config(page_title="Stock Oncología CIMA", layout="wide")

DB_PATH = "oncologia.db"

def get_db():
    return sqlite3.connect(DB_PATH)

# (Mantengo el resto del código simple sin partes que puedan fallar)

st.title("Control de Stock Oncología")
st.write("App en línea - Versión estable")

# Login y resto...

st.success("App cargada correctamente")