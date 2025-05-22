
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

    # Trova dinamicamente la colonna che contiene l'articolo (es. codice + descrizione)
    colonna_descrizione = next((col for col in df.columns if "Artikel" in str(df[col].iloc[1])), df.columns[0])

    for _, row in df.iterrows():
        riga = str(row.get(colonna_descrizione, "")).strip()
        formato = str(row.get("Unnamed: 1", "")).strip()
        annata_raw = row.get("Unnamed: 2", "")
        annata = str(annata_raw).strip() if pd.notna(annata_raw) else ""
        prezzo_raw = str(row.get("Unnamed: 3", "")).strip()

        if re.match(r"^\d{5,}\s+.+", riga) and re.search(r"\d", prezzo_raw):
            descr = re.sub(r"^\d{5,}\s+", "", riga)
            descrizione_finale = f"{descr} {formato}".strip()
            if annata and annata.lower() != "nan":
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
