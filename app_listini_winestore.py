
import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import pandas as pd
import re
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="OCR Listino Winestore", layout="wide")
st.title("🧾 Estrazione OCR - Fornitore Winestore")

uploaded_file = st.file_uploader("Carica un listino PDF scansionato", type="pdf")
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    fornitore = "Winestore"
    rows = []

    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=300)
    image = Image.open(io.BytesIO(pix.tobytes("png")))

    st.image(image, caption="Anteprima pagina 1 (OCR)", use_column_width=True)

    text = pytesseract.image_to_string(image, lang="eng")

    for line in text.split("\n"):
        line = line.strip()
        match = re.match(r"^(\d{1,3}(?:[.,]\d{2}))\s+(.*)$", line)
        if match:
            prezzo = match.group(1).replace(",", ".")
            descrizione = match.group(2)

            # Estrai formato (es. 0,75 o 1,5)
            formato_match = re.search(r"(\d{1,2}[,.]\d{2})\s?l?", descrizione)
            formato = formato_match.group(1).replace(",", ".") if formato_match else ""

            # Estrai annata (es. 2017–2025)
            annata_match = re.search(r"(19|20)\d{2}", descrizione)
            annata = annata_match.group(0) if annata_match else ""

            descrizione_pulita = descrizione
            if formato:
                descrizione_pulita += f" {formato}"
            if annata:
                descrizione_pulita += f" {annata}"

            rows.append({
                "fornitore": fornitore,
                "descrizione_prodotto": descrizione_pulita.strip(),
                "prezzo": prezzo,
                "note": "",
                "data_listino": data_listino.isoformat(),
                "nome_file": nome_file
            })

    df = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df)} prodotti dalla prima pagina.")
    st.dataframe(df)

    if st.button("📤 Carica su Supabase"):
        for r in rows:
            supabase.table("listini").insert(r).execute()
        st.success("✅ Dati caricati con successo!")
