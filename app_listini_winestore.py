import streamlit as st
import pandas as pd
import re
from datetime import datetime
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Upload Tabula - Winestore", layout="wide")
st.title("📤 Carica dati Winestore estratti da Tabula")

uploaded_file = st.file_uploader("Carica il file CSV esportato da Tabula", type=["csv"])
data_listino = st.date_input("Data di riferimento del listino")

if uploaded_file and data_listino:
    nome_file = uploaded_file.name
    df = pd.read_csv(uploaded_file, on_bad_lines='skip', encoding='utf-8')

    fornitore = "Winestore"
    rows = []

    # Trova dinamicamente la colonna con 'Artikel'
    colonna_descrizione = next(
        (col for col in df.columns if len(df) > 1 and isinstance(df[col].iloc[1], str) and "Artikel" in df[col].iloc[1]),
        df.columns[0]
    )

    for _, row in df.iterrows():
        riga = str(row.get(colonna_descrizione, "")).strip()
        formato = str(row.get("Unnamed: 1", "")).strip()
        annata_raw = row.get("Unnamed: 2", "")
        annata = str(annata_raw).strip() if pd.notna(annata_raw) else ""
        prezzo_2 = str(row.get("Unnamed: 2", "")).strip()
        prezzo_3 = str(row.get("Unnamed: 3", "")).strip()

        prezzo_raw = prezzo_3 if re.search(r"\d", prezzo_3) else prezzo_2
        prezzo = re.sub(r"[€\s]", "", prezzo_raw).replace(",", ".")

        # Validazione annata (solo se 4 cifre plausibili)
        annata_valida = re.match(r"^(19|20)\d{2}$", annata)
        annata_finale = annata if annata_valida else ""

        # Nuovo match: qualsiasi stringa che inizia con almeno 4 cifre (anche attaccate)
        if re.match(r"^\d{4,}", riga) and re.search(r"\d", prezzo):
            descr = re.sub(r"^\d{4,}", "", riga).strip()
            descrizione_finale = f"{descr} {formato}".strip()
            if annata_finale:
                descrizione_finale += f" {annata_finale}"

            try:
                prezzo_float = float(prezzo)
                if not (0.5 <= prezzo_float <= 1000):
                    continue
            except:
                continue

            rows.append({
                "fornitore": fornitore,
                "descrizione_prodotto": descrizione_finale,
                "prezzo": prezzo_float,
                "note": "",
                "data_listino": data_listino.isoformat(),
                "nome_file": nome_file
            })

    df_out = pd.DataFrame(rows)
    st.success(f"✅ Trovati {len(df_out)} prodotti.")
    st.dataframe(df_out)

    if st.button("📤 Carica su Supabase"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(rows)
        for i, r in enumerate(rows):
            supabase.table("listini").insert(r).execute()
            progress_bar.progress((i + 1) / total)
            status_text.text(f"Caricamento... {i + 1} di {total}")
        st.success("✅ Dati caricati con successo!")
        progress_bar.empty()
        status_text.empty()
