
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
            words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
            lines_by_top = {}
            for word in words:
                top = round(word["top"])
                if top not in lines_by_top:
                    lines_by_top[top] = []
                lines_by_top[top].append(word)

            for top in sorted(lines_by_top):
                line_words = lines_by_top[top]
                line_text = " ".join(w["text"] for w in line_words).strip()

                # Ignora righe vuote o "BIANCHI", "ROSSI", simboli
                if not line_text or line_text.lower() in ["bianchi", "rossi"]:
                    continue

                # Identifica produttore: centrale, tutto maiuscolo e nessun numero
                if (
                    all(w["x0"] > 200 and w["x0"] < 400 for w in line_words) and
                    line_text.isupper() and
                    not any(char.isdigit() for char in line_text)
                ):
                    current_producer = line_text.strip()
                    continue

                # Cerca prezzo unitario e codice
                match = re.match(r"(.*?)(\d{1,3},\d{2})\s+(\d{5,})$", line_text)
                if match and current_producer:
                    descr_raw = match.group(1).strip()
                    prezzo = match.group(2).replace(",", ".")
                    codice = match.group(3)

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
