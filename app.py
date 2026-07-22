import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io

st.set_page_config(page_title="Stock Oncología CIMA", layout="wide")

# ... (mantengo el login y db como antes)

# Función para generar PDF con membrete
def generar_comprobante_pdf(paciente, items, fecha):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Logo y membrete (usando el archivo que tenés)
    try:
        c.drawImage("Hoja membretada CIMA.png", 50, height - 150, width=400, height=100, preserveAspectRatio=True)  # ajusta según tu archivo
    except:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "CIMA - Grupo Oulton")
        c.drawString(50, height - 70, "Hospital de Día - Oncología")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 120, f"Fecha: {fecha}")
    c.drawString(50, height - 140, f"Paciente: {paciente}")

    y = height - 180
    c.drawString(50, y, "Medicamentos Entregados:")
    y -= 20
    for item in items:
        c.drawString(70, y, f"- {item['droga']} {item['dosis']} x {item['cantidad']}")
        y -= 20

    c.drawString(50, y - 40, "Firma del Paciente: ____________________")
    c.drawString(300, y - 40, "Firma del Profesional: ____________________")

    c.save()
    buffer.seek(0)
    return buffer

# Luego en la pestaña de Pacientes o Uso, agregamos botón:
# if st.button("Generar Comprobante PDF"):
#     pdf = generar_comprobante_pdf(...)
#     st.download_button("Descargar PDF", pdf, "comprobante.pdf", "application/pdf")

st.success("Versión con PDF lista")