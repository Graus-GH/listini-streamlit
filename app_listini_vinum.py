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
                line = line.strip()

                # Produttore in MAIUSCOLO
                if line.isupper() and len(line.split()) <= 4:
                    current_producer = line
                    continue

                # Cerca righe con prezzo o indicazioni alternative
                if "€" in line or any(k in line for k in ["auf Anfrage", "Restmenge"]):
                    prezzo_match = re.search(r"(\d{1,3},\d{2})\s*€", line)
                    prezzo = prezzo_match.group(1).replace(",", ".") if prezzo_match else None

                    # Note rilevanti
                    note = estrai_note(line)

                    # Pulizia descrizione
                    line_cleaned = line
                    if prezzo_match:
                        line_cleaned = line_cleaned.replace(prezzo_match.group(0), "")
                    line_cleaned = line_cleaned.replace("€", "").replace("auf Anfrage", "").replace("Restmenge", "").strip()
                    descrizione_prodotto = f"{current_producer} - {line_cleaned}"

                    # Se prezzo è mancante, usa la nota principale
                    prezzo_finale = prezzo if prezzo else note if "auf Anfrage" in note or "Restmenge" in note else ""

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_prodotto,
                        "prezzo": prezzo_finale,
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
