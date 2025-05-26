
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

st.set_page_config(page_title="Upload Listino HARPF", layout="wide")
st.title("📤 Carica PDF Listino HARPF")

uploaded_file = st.file_uploader("Carica il listino HARPF in formato PDF", type=["pdf"])
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    prodotti = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                line = line.strip()

                if re.search(r"\d{1,3},\d{2}\s?€", line):
                    match_prezzo = re.search(r"(\d{1,3},\d{2})\s?€", line)
                    prezzo = match_prezzo.group(1).replace(",", ".") if match_prezzo else ""

                    produttore_match = re.search(r"^(\d{4,6})\s+(.*?)\s{2,}", line)
                    produttore = produttore_match.group(2).strip() if produttore_match else ""

                    line_clean = re.sub(r"^\d{4,6}\s+", "", line)
                    if match_prezzo:
                        line_clean = line_clean.replace(match_prezzo.group(0), "")

                    annata_match = re.search(r"(19|20)\d{2}", line_clean)
                    annata = annata_match.group(0) if annata_match else ""

                    formato_match = re.search(r"\b(0[.,]\d{1,3}|[.,]\d{1,3})\b", line_clean)
                    formato = formato_match.group(1).replace(",", ".") if formato_match else ""
                    formato_str = f"{formato} l" if formato else ""

                    gradi_match = re.search(r"(\d{1,2}[.,]\d)\s?%", line_clean)
                    gradi = gradi_match.group(1).replace(",", ".") + "%" if gradi_match else ""

                    descr = line_clean.strip()

                    # Evita doppio formato
                    if formato and formato in descr:
                        descr = descr.replace(formato, "").strip()

                    # Costruzione finale
                    extra = " ".join(x for x in [formato_str, gradi, annata] if x).strip()
                    if extra:
                        descr += f" {extra}"

                    note_match = re.findall(r"\b(BIO|RISERVA|LIMITIERT|\d+\s*M\.|Holz|Edelstahl)\b", line, flags=re.IGNORECASE)
                    note = ", ".join(note_match)

                    descrizione_finale = f"{produttore.upper()} {descr}".strip()

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
        for r in prodotti:
            supabase.table("listini").insert(r).execute()
             progress_bar.progress((i + 1) / total)
                status_text.text(f"Caricamento... {i + 1} di {total}")
        st.success("✅ Dati caricati con successo!")
