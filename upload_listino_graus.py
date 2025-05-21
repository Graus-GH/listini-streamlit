
import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Upload Listino GRAUS", layout="wide")
st.title("📥 Carica Listino GRAUS (PDF da struttura tabellare)")

uploaded_file = st.file_uploader("Seleziona il file PDF del listino GRAUS", type="pdf")
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "GRAUS"
    rows = []

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        current_producer = ""
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                line = line.strip()

                # Rileva nuovo produttore (es. #indVINI00004#		ABRAHAM)
                match_prod = re.match(r"#indVINI\d{5}#\s+(.*?)\s+(PREZZO|$)", line)
                if match_prod:
                    current_producer = match_prod.group(1).strip()
                    continue

                # Salta righe intestazione o categoria (BIANCHI, ROSSI, ROSE')
                if re.match(r"^(BIANCHI|ROSSI|ROSE')\s*(\❖)?$", line):
                    continue

                # Rileva riga con prodotto, prezzo unitario e codice (con o senza prezzo confezione)
                match_prod_row = re.match(
                    r"(?:BIANCHI|ROSSI|ROSE')?\s*[❖\-*•]?(.*?)\s+(\d{1,3},\d{2})\s+(\d{5,})$", line
                )
                if match_prod_row:
                    descrizione = match_prod_row.group(1).strip()
                    prezzo = match_prod_row.group(2).replace(",", ".")
                    codice = match_prod_row.group(3)
                    descrizione_completa = f"{current_producer} {descrizione}"
                    note = f"Codice: {codice}"
                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_completa,
                        "prezzo": prezzo,
                        "note": note,
                        "data_listino": data_listino.isoformat(),
                        "nome_file": nome_file
                    })

    df = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df)} prodotti.")
    st.dataframe(df)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
