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

st.set_page_config(page_title="Estrazione Listini Fornitori", layout="wide")
st.title("📦 Estrazione Listini PDF - Fornitore VINUM")

uploaded_file = st.file_uploader("Carica un file PDF", type="pdf")
data_listino = st.date_input("Data a cui si riferisce il listino")

PAROLE_NOTE = ["BIO", "Piwi", "limitiert", "auf Anfrage", "Restmenge"]

def estrai_note(testo):
    return ", ".join([n for n in PAROLE_NOTE if n.lower() in testo.lower()])

def estrai_prezzo(testo):
    match = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", testo)
    return match.group(1).replace(".", "").replace(",", ".") if match else None

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "VINUM"
    rows = []
    current_producer = ""

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            buffer = []

            for line in lines:
                line = line.strip()
                # Nuovo produttore?
                if line.isupper() and 1 <= len(line.split()) <= 5:
                    current_producer = line
                    continue

                # Righe vuote = fine blocco prodotto
                if not line:
                    buffer = []
                    continue

                # Accoda linee
                buffer.append(line)
                full_line = " ".join(buffer)

                # Se trovi prezzo o nota chiave, è fine del blocco
                if re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}", full_line) or any(k in full_line for k in PAROLE_NOTE):
                    prezzo = estrai_prezzo(full_line)
                    note = estrai_note(full_line)
                    descrizione = re.sub(r"(\d{1,3}(?:\.\d{3})*,\d{2})|€|auf Anfrage|Restmenge|limitiert|BIO|Piwi", "", full_line, flags=re.IGNORECASE).strip()
                    descrizione_prodotto = f"{current_producer} - {descrizione}"

                    prezzo_finale = prezzo if prezzo else note if "auf Anfrage" in note or "Restmenge" in note else ""

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_prodotto,
                        "prezzo": prezzo_finale,
                        "note": note,
                        "data_listino": data_listino.isoformat(),
                        "nome_file": nome_file
                    })

                    buffer = []  # reset

    df = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df)} prodotti nel file.")
    st.dataframe(df)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
