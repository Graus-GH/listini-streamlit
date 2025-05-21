
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
import math
from html import escape

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Consulta Listini", layout="wide")
st.title("📊 Consulta Listini Caricati")

# Recupera massimo 1000 righe per prestazioni
full_response = supabase.table("listini").select("*").limit(1000).execute()
df_all = pd.DataFrame(full_response.data)

if df_all.empty:
    st.warning("⚠️ Nessun dato trovato.")
    st.stop()

# Mostra totale righe caricate
st.markdown(f"<div style='text-align: right; font-size: 16px;'>📦 Righe caricate: <strong>{len(df_all):,}</strong></div>", unsafe_allow_html=True)

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
    fornitori = df_all["fornitore"].unique().tolist()
    fornitore_sel = st.multiselect("Fornitore", fornitori, default=fornitori)

    date_min = pd.to_datetime(df_all["data_listino"]).min()
    date_max = pd.to_datetime(df_all["data_listino"]).max()
    date_range = st.date_input("Intervallo data listino", [date_min, date_max])

    search_text = st.text_input("Testo libero (prodotto, note...)")

# Applica filtri
df_filtrato = df_all[
    df_all["fornitore"].isin(fornitore_sel) &
    (pd.to_datetime(df_all["data_listino"]) >= pd.to_datetime(date_range[0])) &
    (pd.to_datetime(df_all["data_listino"]) <= pd.to_datetime(date_range[1]))
]

# Ricerca con evidenziazione
parole = search_text.lower().split() if search_text else []

if parole:
    df_filtrato = df_filtrato[
        df_filtrato.apply(lambda row: all(p in str(row).lower() for p in parole), axis=1)
    ]

# Funzione evidenzia parole
def evidenzia_testo(testo, parole):
    testo_escaped = escape(str(testo))
    for parola in parole:
        testo_escaped = testo_escaped.replace(
            parola, f"<mark>{parola}</mark>"
        )
        testo_escaped = testo_escaped.replace(
            parola.capitalize(), f"<mark>{parola.capitalize()}</mark>"
        )
    return testo_escaped

# Segmenta per pagina
offset = (page_number - 1) * page_size
df_pagina = df_filtrato.iloc[offset:offset + page_size]

st.markdown(f"### ✅ {len(df_pagina)} risultati nella pagina {page_number} su {len(df_filtrato)} risultati totali filtrati • {math.ceil(len(df_filtrato)/page_size)} pagine totali")

# Mostra tabella con evidenziazione
if parole:
    df_html = df_pagina.copy()
    for col in df_html.columns:
        df_html[col] = df_html[col].apply(lambda x: evidenzia_testo(x, parole))
    st.markdown(df_html.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.dataframe(df_pagina, use_container_width=True, height=1000)

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
