
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
import math

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Consulta Listini (interattivo)", layout="wide")
st.title("📊 Consulta Listini Caricati (Tabella Dinamica)")

# Recupera TUTTE le righe
data = []
limit = 1000
offset = 0
while True:
    resp = supabase.table("listini").select("*").range(offset, offset + limit - 1).execute()
    batch = resp.data
    if not batch:
        break
    data.extend(batch)
    if len(batch) < limit:
        break
    offset += limit

df_all = pd.DataFrame(data)

if df_all.empty:
    st.warning("⚠️ Nessun dato trovato.")
    st.stop()

# Paginazione
page_size = 500
total_pages = math.ceil(len(df_all) / page_size)

page_number = st.sidebar.number_input(
    "📄 Pagina",
    min_value=1,
    max_value=total_pages,
    value=1,
    step=1
)

# Filtri
with st.sidebar:
    st.header("🔍 Filtri")
    fornitori = sorted(df_all["fornitore"].dropna().unique().tolist())
    fornitore_sel = st.multiselect("Fornitore", fornitori, default=fornitori)

    date_min = pd.to_datetime(df_all["data_listino"]).min()
    date_max = pd.to_datetime(df_all["data_listino"]).max()
    date_range = st.date_input("Intervallo data listino", [date_min, date_max])

    search_text = st.text_input("Testo libero (prodotto, note...)")

df_filtrato = df_all[
    df_all["fornitore"].isin(fornitore_sel) &
    (pd.to_datetime(df_all["data_listino"]) >= pd.to_datetime(date_range[0])) &
    (pd.to_datetime(df_all["data_listino"]) <= pd.to_datetime(date_range[1]))
]

parole = search_text.lower().split() if search_text else []

def contiene_parole(row, parole):
    testo = " ".join(str(val).lower() for val in row)
    return all(p in testo for p in parole)

if parole:
    df_filtrato = df_filtrato[df_filtrato.apply(lambda row: contiene_parole(row, parole), axis=1)]

# Segmenta per pagina
offset = (page_number - 1) * page_size
df_pagina = df_filtrato.iloc[offset:offset + page_size]

st.markdown(f"### ✅ {len(df_pagina)} risultati nella pagina {page_number} su {len(df_filtrato)} risultati totali filtrati • {math.ceil(len(df_filtrato)/page_size)} pagine totali")

# Mostra tabella interattiva
st.dataframe(df_pagina, use_container_width=True)

# Download pagina corrente
if not df_pagina.empty:
    buffer = io.BytesIO()
    df_pagina.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    st.download_button(
        label="📥 Scarica solo questa pagina",
        data=buffer,
        file_name=f"listini_pagina_{page_number}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Download tutti i risultati filtrati
if not df_filtrato.empty:
    all_buffer = io.BytesIO()
    df_filtrato.to_excel(all_buffer, index=False, engine='openpyxl')
    all_buffer.seek(0)
    st.download_button(
        label="📥 Scarica tutti i risultati filtrati",
        data=all_buffer,
        file_name="listini_filtrati_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
