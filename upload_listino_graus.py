
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
st.title("📥 Carica Listino GRAUS (tabella vera via extract_table)")

uploaded_file = st.file_uploader("Seleziona il file PDF del listino GRAUS", type="pdf")
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "GRAUS"
    rows = []
    current_producer = ""

    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    match = re.match(r"#indVINI\d{5}#\s*(.+)", line.strip())
                    if match:
                        current_producer = match.group(1).strip()
                        break  # Assumi che il produttore venga prima della tabella

            table = page.extract_table()
            if not table:
                continue

            for row in table:
                if not row or len(row) < 5:
                    continue
                prodotto = row[2]
                prezzo_unitario = row[3]
                codice = row[4]

                # Salta se dati non coerenti
                if not prodotto or not prezzo_unitario or not codice:
                    continue

                try:
                    prezzo = prezzo_unitario.replace(",", ".")
                    descrizione_completa = f"{current_producer} {prodotto.strip()}"
                    note = f"Codice: {codice.strip()}"

                    rows.append({
                        "fornitore": fornitore,
                        "descrizione_prodotto": descrizione_completa,
                        "prezzo": prezzo,
                        "note": note,
                        "data_listino": data_listino.isoformat(),
                        "nome_file": nome_file
                    })
                except:
                    continue

    df = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df)} prodotti.")
    st.dataframe(df)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
