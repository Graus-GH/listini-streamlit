import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Upload Excel GRAUS", layout="wide")
st.title("📥 Carica Excel Listino GRAUS")

uploaded_file = st.file_uploader("Carica il file Excel", type=["xlsx"])
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    df = pd.read_excel(uploaded_file, sheet_name=0, header=None)

    fornitore = "GRAUS"
    rows = []
    produttore_corrente = ""

    for _, row in df.iterrows():
        if pd.notna(row[5]):
            produttore_corrente = str(row[5]).strip()
            continue

        descr = row[6]
        prezzo = row[7]
        codice = row[8]

        if pd.notna(descr) and pd.notna(prezzo) and pd.notna(codice):
            descrizione = f"{produttore_corrente} {str(descr).strip()}"
            note = f"Codice: {str(codice).strip()}"

            rows.append({
                "fornitore": fornitore,
                "descrizione_prodotto": descrizione,
                "prezzo": float(prezzo),
                "note": note,
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
