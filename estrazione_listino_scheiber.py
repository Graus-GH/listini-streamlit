
import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # <-- Inserisci la tua chiave anon
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Estrazione Listino SCHEIBER", layout="wide")
st.title("📦 Estrazione Listini PDF - Fornitore SCHEIBER")

uploaded_file = st.file_uploader("Carica un file PDF", type="pdf")
data_listino = st.date_input("Data a cui si riferisce il listino")

def estrai_note(testo):
    note_trovate = []
    parole_chiave = ["BIO", "Piwi", "Demeter", "limitiert", "auf Reservierung", "im Magazin"]
    for parola in parole_chiave:
        if parola.lower() in testo.lower():
            note_trovate.append(parola)
    return ", ".join(note_trovate)

def estrai_annata(testo):
    match = re.search(r"\b(19|20)\d{2}\b", testo)
    return match.group(0) if match else ""

def estrai_produttore(testo):
    match = re.search(r"DOC\s+(.*)$", testo)
    return match.group(1).strip().upper() if match else ""

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "SCHEIBER"
    rows = []

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')
            for line in lines:
                line = line.strip()

                if not line or "Preis €/Fl." in line or "Kodex" in line or "Beschreibung" in line:
                    continue

                prezzo_match = re.search(r"(\d{1,3},\d{2})\s*€?", line)
                if prezzo_match:
                    prezzo = prezzo_match.group(1).replace(",", ".")
                    codice_match = re.match(r"•?\s*([A-Z]{3}\d{4,})", line)
                    codice = codice_match.group(1) if codice_match else ""

                    descrizione_clean = line
                    if codice:
                        descrizione_clean = descrizione_clean.replace(codice, "")
                    descrizione_clean = descrizione_clean.replace(prezzo_match.group(0), "").strip("• -").strip()

                    note = estrai_note(line)
                    annata = estrai_annata(descrizione_clean)
                    produttore = estrai_produttore(descrizione_clean)

                    if annata:
                        descrizione_clean = descrizione_clean.replace(annata, "").strip()

                    if produttore:
                        descrizione_clean = descrizione_clean.replace(produttore, "").strip()

                    descrizione_prodotto = f"{produttore} – {descrizione_clean}"
                    if annata:
                        descrizione_prodotto += f" [{annata}]"

                    rows.append({
                        "fornitore": fornitore,
                        "codice": codice,
                        "descrizione_prodotto": descrizione_prodotto,
                        "annata": annata,
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
