
import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import re

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# URL CSV del Google Sheet pubblico
CSV_URL = "https://docs.google.com/spreadsheets/d/147uce6_Mj39nNxIjIWphu0Gt-CCpknDtzS0-MnR6XWo/export?format=csv&gid=953238786"

st.set_page_config(page_title="Listino GRAUS da Google Sheet", layout="wide")
st.title("📥 Estrazione automatica da Google Sheet")

data_listino = st.date_input("Data di riferimento del listino")

def pulisci_prezzo(val):
    if pd.isna(val):
        return None
    val = str(val).replace(",", ".")
    val = re.sub(r"[^\d.]", "", val)
    try:
        return round(float(val), 2)
    except:
        return None

def pulisci_codice(val):
    try:
        return str(int(float(val)))
    except:
        return str(val).strip()

if data_listino:
    try:
        df = pd.read_csv(CSV_URL, header=None)

        fornitore = "GRAUS"
        rows = []

        for i, row in df.iterrows():
            if i == 0:
                continue
            if (pd.isna(row[3]) or str(row[3]).strip() == "") and (pd.isna(row[4]) or str(row[4]).strip() == ""):
                continue

            prezzo = pulisci_prezzo(row[8])
            if prezzo is None:
                continue

            try:
                produttore = str(row[3]).replace("•", "").strip()
                descrizione = f"{produttore}, {str(row[4]).strip()}"
                codice = pulisci_codice(row[0])
                note = f"Codice: {codice}"

                rows.append({
                    "fornitore": fornitore,
                    "descrizione_prodotto": descrizione,
                    "prezzo": prezzo,
                    "note": note,
                    "data_listino": data_listino.isoformat(),
                    "nome_file": "estrazione_google_sheet"
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

    except Exception as e:
        st.error(f"Errore durante la lettura del foglio: {e}")
