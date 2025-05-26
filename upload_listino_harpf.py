
import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Upload Listino HARPF (Kod)", layout="wide")
st.title("📤 Carica PDF Listino HARPF (estrazione Kod.)")

uploaded_file = st.file_uploader("Carica il PDF HARPF", type=["pdf"])
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    prodotti = []

    with pdfplumber.open(uploaded_file) as pdf:
        in_prodotti = False
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")

            for line in lines:
                line = line.strip()

                # Attiva se trova la sezione "Kod."
                if "Kod" in line:
                    in_prodotti = True
                    continue

                # Se siamo nella sezione giusta e la riga inizia con codice numerico
                if in_prodotti and re.match(r"^\d{4,6}\s", line) and "€" in line:
                    # Estrai codice e contenuto
                    match = re.match(r"^(\d{4,6})\s+(.*)", line)
                    codice = match.group(1)
                    contenuto = match.group(2)

                    # Estrai prezzo
                    match_prezzo = re.search(r"(\d{1,3},\d{2})\s?€", contenuto)
                    prezzo = match_prezzo.group(1).replace(",", ".") if match_prezzo else ""
                    if match_prezzo:
                        contenuto = contenuto.replace(match_prezzo.group(0), "")

                    # Estrai gradazione (xx%)
                    gradi = ""
                    gradi_match = re.search(r"(\d{1,2}(?:[.,]\d)?)\s*%", contenuto)
                    if gradi_match:
                        gradi = gradi_match.group(1).replace(",", ".") + "%"
                        contenuto = contenuto.replace(gradi_match.group(0), "")

                    # Estrai formato (es. 0.5, 0,7)
                    formato = ""
                    formato_match = re.search(r"\b(0[.,]\d{1,3})\b", contenuto)
                    if formato_match:
                        formato = formato_match.group(1).replace(",", ".") + " l"
                        contenuto = contenuto.replace(formato_match.group(1), "")

                    # Estrai note da testo
                    note_match = re.findall(r"\b(BIO|RISERVA|LIMITIERT|barrique|Holz|Edelstahl|ciliegio|rovere)\b", contenuto, flags=re.IGNORECASE)
                    note = ", ".join(note_match)

                    # Ricostruisci descrizione
                    descrizione = " ".join(contenuto.split()).strip()
                    descrizione_finale = f"{descrizione} {formato} {gradi}".strip()

                    prodotti.append({
                        "fornitore": "HARPF",
                        "descrizione_prodotto": descrizione_finale,
                        "prezzo": prezzo,
                        "note": note,
                        "data_listino": data_listino.isoformat(),
                        "nome_file": nome_file
                    })

    df_out = pd.DataFrame(prodotti)
    st.success(f"✅ Trovati {len(df_out)} prodotti.")
    st.dataframe(df_out)

    if st.button("📤 Carica su Supabase"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(prodotti)
        for i, r in enumerate(prodotti):
            supabase.table("listini").insert(r).execute()
            progress_bar.progress((i + 1) / total)
            status_text.text(f"Caricamento... {i + 1} di {total}")
        st.success("✅ Dati caricati con successo!")
        progress_bar.empty()
        status_text.empty()
