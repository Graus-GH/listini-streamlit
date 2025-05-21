
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

st.set_page_config(page_title="Upload Listino GRAUS", layout="wide")
st.title("📥 Carica Listino GRAUS (PDF)")

uploaded_file = st.file_uploader("Seleziona il file PDF del listino GRAUS", type="pdf")
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "GRAUS"
    rows = []

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        current_producer = ""
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                line = line.strip()

                # Rimuove frammenti tipici di colonne grafiche errate
                line = re.sub(r"^([A-Z]{2,}\s)?BIA.?N", "", line)
                line = re.sub(r"[❖•*→←◆▪️]", "", line).strip()

                # Identifica il nome del produttore: tutto MAIUSCOLO, centrato, senza numeri o prezzi
                if (
                    line.isupper()
                    and len(line.split()) <= 4
                    and not any(c in line for c in "€0123456789")
                    and not line.startswith("PREZZO")
                ):
                    current_producer = line.strip()
                    continue

                # Cerca riga di prodotto con prezzo singolo e codice a fine riga
                match = re.match(r"(.*?)(\d{1,3},\d{2})\s+(\d{5,})$", line)
                if match:
                    descr_raw = match.group(1).strip()
                    prezzo = match.group(2).replace(",", ".")
                    codice = match.group(3)

                    # Costruzione descrizione finale
                    descrizione_prodotto = f"{current_producer} {descr_raw}".strip()
                    note = f"Codice: {codice}"

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_prodotto,
                        "prezzo": prezzo,
                        "note": note,
                        "data_listino": data_listino.isoformat(),
                        "nome_file": nome_file
                    })

    df = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df)} prodotti.")
    st.dataframe(df)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
