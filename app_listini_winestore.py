
import streamlit as st
import pandas as pd
import re
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Upload Listino Winestore Excel", layout="wide")
st.title("📥 Carica Listino Winestore da Excel")

uploaded_file = st.file_uploader("Carica il file Excel", type=["xlsx"])
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    df = pd.read_excel(uploaded_file, header=None)
    fornitore = "Winestore"
    rows = []

    for row in df.itertuples(index=False):
        celle_testo = [str(cell).strip() for cell in row if isinstance(cell, str) and len(str(cell).strip()) > 4]

        for cell in celle_testo:
            if re.search(r"\d{1,2}[.,]\d{2}", cell):  # formato probabile
                descrizione = cell

                # Estrai formato
                formato_match = re.search(r"(\d{1,2}[.,]\d{2})\s?l?", descrizione)
                formato = formato_match.group(1).replace(",", ".") if formato_match else ""

                # Estrai annata
                annata_match = re.search(r"(19|20)\d{2}", descrizione)
                annata = annata_match.group(0) if annata_match else ""

                descrizione_finale = descrizione
                if formato:
                    descrizione_finale += f" {formato}"
                if annata:
                    descrizione_finale += f" {annata}"

                rows.append({
                    "fornitore": fornitore,
                    "descrizione_prodotto": descrizione_finale.strip(),
                    "prezzo": "",  # non disponibile nel file
                    "note": "",
                    "data_listino": data_listino.isoformat(),
                    "nome_file": nome_file
                })

    df_out = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df_out)} prodotti.")
    st.dataframe(df_out)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
