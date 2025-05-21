
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

st.set_page_config(page_title="Estrazione Listino Winestore", layout="wide")
st.title("📦 Estrazione Listino PDF - Fornitore Winestore")

uploaded_file = st.file_uploader("Carica un file PDF", type="pdf")
data_listino = st.date_input("Data a cui si riferisce il listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "Winestore"
    rows = []

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                line = line.strip()

                # Cerca righe con prezzo iniziale (es. 17,90 ...)
                match = re.match(r"^(\d{1,3}[.,]\d{2})\s+\d+\s+(.*)", line)
                if match:
                    prezzo = match.group(1).replace(",", ".")
                    descrizione = match.group(2).strip()

                    # Estrai formato
                    formato_match = re.search(r"(\d{1,2}[.,]\d{2})\s?l?", descrizione)
                    formato = formato_match.group(1).replace(",", ".") if formato_match else ""

                    # Estrai annata
                    annata_match = re.search(r"(19|20)\d{2}", descrizione)
                    annata = annata_match.group(0) if annata_match else ""

                    # Costruisci descrizione finale
                    descrizione_finale = descrizione
                    if formato:
                        descrizione_finale += f" {formato}"
                    if annata:
                        descrizione_finale += f" {annata}"

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_finale,
                        "prezzo": prezzo,
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
