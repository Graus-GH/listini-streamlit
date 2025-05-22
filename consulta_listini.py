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
st.title("📊 Consulta Listini Caricati")

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

# Escludi colonne non richieste e rioridina
colonne_base = [col for col in df_pagina.columns if col not in ["id", "categoria", "data_caricamento", "nome_file"]]

# Sposta 'prezzo' prima di 'descrizione_prodotto'
if "prezzo" in colonne_base and "descrizione_prodotto" in colonne_base:
    colonne_base.remove("prezzo")
    insert_idx = colonne_base.index("descrizione_prodotto")
    colonne_base.insert(insert_idx, "prezzo")

df_display = df_pagina[colonne_base].copy()

# Inserisci favicon accanto a GRAUS
favicon_html = '<img src="https://www.graus.bz.it/favicon.ico" style="height:16px; vertical-align:middle; margin-left:4px;">'
df_display["fornitore"] = df_display["fornitore"].apply(
    lambda x: f'{x}{favicon_html}' if str(x).upper() == "GRAUS" else x
)

# Funzione per evidenziare le parole
import re

def evidenzia_html(val, parole, colname, fornitore=None):
    val_str = str(val)
    colore = "yellow"
    if "graus" in str(fornitore).lower():
        colore = "#d0ebff"  # blu chiaro

    for parola in parole:
        pattern = re.compile(re.escape(parola), re.IGNORECASE)
        val_str = pattern.sub(
            lambda m: f'<mark style="background-color:{colore}">{m.group(0)}</mark>',
            val_str
        )
    return val_str

# Applica evidenziazione cella per cella
if parole:
    for idx, row in df_display.iterrows():
        for col in df_display.columns:
            df_display.at[idx, col] = evidenzia_html(row[col], parole, col, fornitore=row["fornitore"])

# Stile tabella HTML
st.markdown("""
    <style>
    .styled-table {
        font-family: Courier, monospace;
        border-collapse: collapse;
        width: 100%;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #ddd;
        padding: 6px;
        text-align: left;
        font-size: 14px;
    }
    .styled-table tr:nth-child(even){background-color: #f9f9f9;}
    .styled-table th {
        background-color: #4CAF50;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Costruzione HTML
html_table = df_display.to_html(escape=False, index=False, classes='styled-table')
st.markdown(html_table, unsafe_allow_html=True)

# Download Excel pagina
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

# Download Excel completo filtrato
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
