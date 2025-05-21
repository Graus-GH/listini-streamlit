
import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"  # <-- Inserisci il tuo URL Supabase
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"  # <-- Inserisci la tua chiave anon
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Estrazione Listini Fornitori", layout="wide")
st.title("📦 Estrazione Listini PDF - Fornitore VINUM")

uploaded_file = st.file_uploader("Carica un file PDF", type="pdf")
data_listino = st.date_input("Data a cui si riferisce il listino")

def estrai_note(testo):
    note_trovate = []
    parole_chiave = ["BIO", "Piwi", "limitiert", "auf Anfrage", "Restmenge"]
    for parola in parole_chiave:
        if parola.lower() in testo.lower():
            note_trovate.append(parola)
    return ", ".join(note_trovate)

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "VINUM"
    rows = []

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        current_producer = ""
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')
            for line in lines:
                if line.strip().isupper() and len(line.strip().split()) <= 4:
                    current_producer = line.strip()
                    continue
                if "€" in line or re.search(r"(auf Anfrage|Restmenge|\d{1,3}[,.]\d{2})", line):
                    match_prezzo = re.search(r"(auf Anfrage|Restmenge|\d{1,3}[,.]\d{2})\s*$", line)
                    prezzo = match_prezzo.group(1).replace(",", ".") if match_prezzo else ""
                    left = line.replace(prezzo, "").replace("€", "").strip()
                    descrizione_prodotto = f"{current_producer} - {left}"
                    note = estrai_note(line)

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_prodotto,
                        "prezzo": prezzo,
                        "note": note,
                        "data_listino": data_listino.isoformat(),
                        "nome_file": nome_file
                    })

    df = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df)} prodotti nel file.")
    st.dataframe(df)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
