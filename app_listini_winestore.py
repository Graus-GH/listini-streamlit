
import streamlit as st
import pandas as pd
import re
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Upload Tabula - Winestore", layout="wide")
st.title("📤 Carica dati Winestore estratti da Tabula")

uploaded_file = st.file_uploader("Carica il file CSV esportato da Tabula", type=["csv"])
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    df = pd.read_csv(uploaded_file)

    fornitore = "Winestore"
    rows = []

    for _, row in df.iterrows():
        riga = str(row.get("Schaumweine", "")).strip()
        formato = str(row.get("Unnamed: 1", "")).strip()
        prezzo_raw = str(row.get("Unnamed: 3", "")).strip()

        if re.match(r"^\d{5,}\s+.+", riga) and re.search(r"\d", prezzo_raw):
            descr = re.sub(r"^\d{5,}\s+", "", riga)

            # Estrai annata dalla descrizione (es. 2017–2025)
            annata_match = re.search(r"(19|20)\d{2}", descr)
            annata = annata_match.group(0) if annata_match else ""

            # Costruisci descrizione finale
            descrizione_finale = f"{descr} {formato}".strip()
            if annata:
                descrizione_finale += f" {annata}"

            prezzo = re.sub(r"[€\s]", "", prezzo_raw).replace(",", ".")
            try:
                prezzo_float = float(prezzo)
            except:
                prezzo_float = ""

            rows.append({
                "fornitore": fornitore,
                "descrizione_prodotto": descrizione_finale,
                "prezzo": prezzo_float,
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
