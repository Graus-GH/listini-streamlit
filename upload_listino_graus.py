import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Aggiorna da Google Sheets", layout="wide")
st.title("📥 Aggiorna Listino da Google Sheets")

data_listino = st.date_input("Data di riferimento del listino")

CSV_URL = "https://docs.google.com/spreadsheets/d/147uce6_Mj39nNxIjIWphu0Gt-CCpknDtzS0-MnR6XWo/export?format=csv&gid=953238786"

if data_listino:
    df = pd.read_csv(CSV_URL)

    fornitore = "GRAUS"
    rows = []

    for i, row in df.iterrows():
        if i == 0 or pd.isna(row[4]):
            continue  # salta intestazione o righe con colonna E vuota

        try:
            produttore = str(row[3]).replace("•", "").strip()
            descrizione = f"{produttore}, {str(row[4]).strip()}"
            prezzo = float(row[8])
            codice = str(row[0]).strip()
            note = f"Codice: {codice}"

            rows.append({
                "fornitore": fornitore,
                "descrizione_prodotto": descrizione,
                "prezzo": prezzo,
                "note": note,
                "data_listino": data_listino.isoformat(),
                "nome_file": "GoogleSheet"
            })
        except Exception:
            continue

    df_out = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df_out)} prodotti.")
    st.dataframe(df_out)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
