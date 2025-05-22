import streamlit as st
import pdfplumber
import pandas as pd
import io
import re
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Estrazione Listini Fornitori", layout="wide")
st.title("📦 Estrazione Listini Tabellare - VINUM")

uploaded_file = st.file_uploader("Carica un file PDF", type="pdf")
data_listino = st.date_input("Data a cui si riferisce il listino")

PAROLE_NOTE = ["BIO", "Piwi", "limitiert", "auf Anfrage", "Restmenge"]

def estrai_note(testo):
    return ", ".join([n for n in PAROLE_NOTE if n.lower() in str(testo).lower()])

def estrai_annata(desc):
    match = re.search(r"\b(19|20)\d{2}\b", desc)
    return match.group(0) if match else ""

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "VINUM"
    prodotti = []
    produttore_corrente = ""

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Skippa righe troppo corte
                    if not row or len([x for x in row if x]) < 2:
                        continue

                    # Se è un produttore tutto maiuscolo e breve, aggiorna
                    if len(row) == 1 and row[0] and row[0].isupper() and len(row[0].split()) <= 4:
                        produttore_corrente = row[0].strip()
                        continue

                    descrizione = row[0].strip() if len(row) > 0 else ""
                    formato = row[1].strip() if len(row) > 1 else ""
                    prezzo_raw = row[2].strip() if len(row) > 2 else ""
                    prezzo = prezzo_raw.replace("€", "").replace(".", "").replace(",", ".").strip() if "€" in prezzo_raw or re.search(r"\d+,\d{2}", prezzo_raw) else ""
                    note = estrai_note(" ".join(row))
                    annata = estrai_annata(descrizione)

                    prodotti.append({
                        "fornitore": fornitore,
                        "produttore": produttore_corrente,
                        "descrizione_prodotto": descrizione,
                        "formato": formato,
                        "prezzo": prezzo if prezzo else note if "auf Anfrage" in note or "Restmenge" in note else "",
                        "note": note,
                        "annata": annata,
                        "data_listino": data_listino.isoformat(),
                        "nome_file": nome_file
                    })

    df = pd.DataFrame(prodotti)
    st.success(f"✅ Trovati {len(df)} prodotti nel file.")
    st.dataframe(df)

    if st.button("📤 Carica su Supabase"):
        for r in prodotti:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
