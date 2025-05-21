
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
st.title("📥 Carica Listino GRAUS (PDF)")

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
                if not line:
                    continue

                # Se contiene solo lettere maiuscole o inizia con #indVINI (identifica un produttore)
                if line.isupper() or re.match(r"#indVINI\d{5}#([A-Z ]+)", line):
                    match = re.search(r"#indVINI\d{5}#([A-ZÀ-ÖØ-Ý]+)", line)
                    current_producer = match.group(1).strip() if match else line.strip()
                    continue

                # Righe con prezzi e codici
                match = re.match(r".*?([0-9]{1,3},\d{2})\s+([0-9]{1,3},\d{2})\s+\d{5,}", line)
                if match:
                    # Estrai solo descrizione: escludi prezzo e codice
                    descrizione = re.sub(r"(\d{1,3},\d{2})\s+(\d{1,3},\d{2})\s+\d{5,}", "", line).strip("❖•-* ")

                    prezzo_unitario = match.group(2).replace(",", ".")
                    descrizione_prodotto = f"{current_producer} {descrizione}".strip()

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_prodotto,
                        "prezzo": prezzo_unitario,
                        "note": "",
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
