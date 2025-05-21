
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
st.title("📥 Carica Listino GRAUS (via coordinate)")

uploaded_file = st.file_uploader("Seleziona il file PDF del listino GRAUS", type="pdf")
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "GRAUS"
    rows = []
    current_producer = ""

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=False)
            lines_by_top = {}

            for word in words:
                top = round(word["top"])
                if top not in lines_by_top:
                    lines_by_top[top] = []
                lines_by_top[top].append(word)

            for top in sorted(lines_by_top.keys()):
                line_words = sorted(lines_by_top[top], key=lambda w: w["x0"])

                full_line = " ".join(w["text"] for w in line_words).strip()

                # Riconosci produttore
                match_prod = re.match(r"#indVINI\d{5}#\s*(.+)", full_line)
                if match_prod:
                    current_producer = match_prod.group(1).strip()
                    continue

                if not current_producer:
                    continue

                # Separiamo parole per colonna
                prodotto_words = [w["text"] for w in line_words if 100 <= w["x0"] < 420]
                prezzo_words = [w["text"] for w in line_words if 420 <= w["x0"] < 490]
                codice_words = [w["text"] for w in line_words if w["x0"] >= 490]

                if len(prodotto_words) >= 2 and len(prezzo_words) == 1 and len(codice_words) == 1:
                    descrizione = f"{current_producer} {' '.join(prodotto_words).strip()}"
                    prezzo = prezzo_words[0].replace(",", ".").strip()
                    codice = codice_words[0].strip()
                    note = f"Codice: {codice}"

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione,
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
