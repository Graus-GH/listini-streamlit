import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
import math
import re
from collections import Counter

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # <-- usa la tua chiave
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Consulta Listini (interattivo)", layout="wide")

# Logo in alto a destra
st.markdown("""
    <div style="text-align: right; margin-bottom: -10px;">
        <img src="https://images.squarespace-cdn.com/content/v1/663dbdc9ee50c97d394658a4/d630ab5c-24ad-4c20-af78-d18744394601/New+Project+%2825%29.png?format=1500w"
             style="height: 60px;">
    </div>
""", unsafe_allow_html=True)

# Titolo ridotto
st.markdown("<h3>📊 Consulta Listini Caricati</h3>", unsafe_allow_html=True)

# Carica dati da Supabase
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

# Sidebar
page_size = 500
total_pages = math.ceil(len(df_all) / page_size)
page_number = st.sidebar.number_input("📄 Pagina", 1, total_pages, 1)

with st.sidebar:
    st.header("🔍 Filtri")
    fornitori = sorted(df_all["fornitore"].dropna().unique().tolist())
    fornitore_sel = st.multiselect("Fornitore", fornitori, default=fornitori)

    date_min = pd.to_datetime(df_all["data_listino"]).min()
    date_max = pd.to_datetime(df_all["data_listino"]).max()
    date_range = st.date_input("Intervallo data listino", [date_min, date_max])

    if "search_text" not in st.session_state:
        st.session_state.search_text = ""

    if st.button("🗑️ Rimuovi tutte le parole"):
        st.session_state.search_text = ""

    search_text = st.text_input("Testo libero (prodotto, note...)", value=st.session_state.search_text)
    st.session_state.search_text = search_text

# Applica filtri
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

# Calcola parole più frequenti
if not df_filtrato.empty and "descrizione_prodotto" in df_filtrato.columns:
    descrizioni = df_filtrato["descrizione_prodotto"].astype(str).str.lower().tolist()
    testo = " ".join(descrizioni)
    parole_grezze = re.findall(r'\b\w+\b', testo)
    parole_filtrate = [p for p in parole_grezze if len(p) > 1 and not p.isnumeric()]
    comuni = Counter(parole_filtrate).most_common(30)

    st.sidebar.markdown("### 🏷️ Le 30 parole più frequenti")

    tag_html = "<div>"
    for parola, count in comuni:
        tag_html += f'''
        <form action="" method="get">
            <button name="tag_add" value="{parola}" style="
                background-color:#005caa;
                color:white;
                border:none;
                border-radius:16px;
                padding:4px 10px;
                font-size:13px;
                cursor:pointer;
                margin-bottom:4px;
            ">+ {parola} ({count})</button>
        </form>
        '''
    tag_html += "</div>"
    st.sidebar.markdown(tag_html, unsafe_allow_html=True)

    tag_clicked = st.query_params.get("tag_add", [])
    if tag_clicked:
        tag = tag_clicked[0]
        if tag not in st.session_state.search_text.split():
            st.session_state.search_text += f" {tag}"
        st.query_params.clear()

# Visualizza risultati
offset = (page_number - 1) * page_size
df_pagina = df_filtrato.iloc[offset:offset + page_size]

st.markdown(
    f"<h5>✅ {len(df_pagina)} risultati nella pagina {page_number} su {len(df_filtrato)} risultati totali filtrati • {math.ceil(len(df_filtrato)/page_size)} pagine totali</h5>",
    unsafe_allow_html=True
)

# Ordina colonne
colonne_base = [col for col in df_pagina.columns if col not in ["id", "categoria", "data_caricamento", "nome_file"]]
if "prezzo" in colonne_base and "descrizione_prodotto" in colonne_base:
    colonne_base.remove("prezzo")
    colonne_base.insert(colonne_base.index("descrizione_prodotto"), "prezzo")

df_display = df_pagina[colonne_base].copy()

# Logo GRAUS accanto al nome
favicon_html = '<img src="https://www.graus.bz.it/favicon.ico" style="height:16px; vertical-align:middle; margin-left:4px;">'
df_display["fornitore"] = df_display["fornitore"].apply(
    lambda x: f"{x}{favicon_html}" if str(x).upper() == "GRAUS" else x
)

# Evidenziazione
def evidenzia_html(val, parole, colname, fornitore=None):
    val_str = str(val)
    colore = "#d0ebff" if "graus" in str(fornitore).lower() else "yellow"
    for parola in parole:
        pattern = re.compile(re.escape(parola), re.IGNORECASE)
        val_str = pattern.sub(lambda m: f'<mark style="background-color:{colore}">{m.group(0)}</mark>', val_str)
    return val_str

if parole:
    for idx, row in df_display.iterrows():
        for col in df_display.columns:
            df_display.at[idx, col] = evidenzia_html(row[col], parole, col, fornitore=row["fornitore"])

# HTML table rendering
def build_custom_html_table(df):
    headers = "".join(
        f"<th style='text-align:center'>{col}</th>" if col == "prezzo" else f"<th>{col}</th>"
        for col in df.columns
    )
    rows = ""
    for _, row in df.iterrows():
        is_graus = "graus" in str(row["fornitore"]).lower()
        row_html = "<tr>"
        for col in df.columns:
            val = row[col]
            style = ' style="text-align:center;"' if col == "prezzo" else ""
            cell_content = f"<strong>{val}</strong>" if is_graus else val
            row_html += f"<td{style}>{cell_content}</td>"
        row_html += "</tr>"
        rows += row_html
    return f"<table class='styled-table'><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table>"

# Styling
st.markdown("""
    <style>
    .styled-table {
        font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
        border-collapse: collapse;
        width: 100%;
    }
    .styled-table th, .styled-table td {
        border: 1px solid #ddd;
        padding: 6px;
        text-align: left;
        font-size: 14px;
    }
    .styled-table tr:nth-child(even) { background-color: #f9f9f9; }
    .styled-table th {
        background-color: #005caa;
        color: white;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #005caa !important;
    }
    .stMultiSelect [data-baseweb="tag"] span {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(build_custom_html_table(df_display), unsafe_allow_html=True)

# Download
if not df_pagina.empty:
    buffer = io.BytesIO()
    df_pagina.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button("📥 Scarica solo questa pagina", buffer, f"listini_pagina_{page_number}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if not df_filtrato.empty:
    all_buffer = io.BytesIO()
    df_filtrato.to_excel(all_buffer, index=False, engine="openpyxl")
    all_buffer.seek(0)
    st.download_button("📥 Scarica tutti i risultati filtrati", all_buffer, "listini_filtrati_completo.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
