import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import re
from datetime import datetime
from collections import Counter
from supabase import create_client, Client
import io
import math

# --- AUTENTICAZIONE ---
names = ["Utente Graus"]
usernames = ["utente@graus.bz.it"]
passwords = ["provapassword"]

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    names=names,
    usernames=usernames,
    passwords=hashed_passwords,
    cookie_name="graus_login",
    key="graus_secret_key",
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    if not username.endswith("@graus.bz.it"):
        st.error("Accesso negato: solo per email @graus.bz.it")
        st.stop()
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Loggato come {username}")





import streamlit as st
import pandas as pd
import re
from datetime import datetime
from collections import Counter
from supabase import create_client, Client
import io
import math

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Consulta Listini (interattivo)", layout="wide")

# Logo sopra al titolo
st.markdown("""
    <div style="text-align: right; margin-bottom: -10px;">
        <img src="https://images.squarespace-cdn.com/content/v1/663dbdc9ee50c97d394658a4/d630ab5c-24ad-4c20-af78-d18744394601/New+Project+%2825%29.png?format=1500w"
             style="height: 60px;">
    </div>
""", unsafe_allow_html=True)

st.markdown("<h3>📊 Consulta Listini Caricati</h3>", unsafe_allow_html=True)

# Caching caricamento dati
@st.cache_data
def carica_dati_supabase():
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
    return pd.DataFrame(data)

df_all = carica_dati_supabase()

if df_all.empty:
    st.warning("⚠️ Nessun dato trovato.")
    st.stop()

# Sidebar - Filtri
page_size = 500
total_pages = math.ceil(len(df_all) / page_size)
page_number = st.sidebar.number_input("📄 Pagina", min_value=1, max_value=total_pages, value=1)

with st.sidebar:
    st.header("🔍 Filtri")
    fornitori = sorted(df_all["fornitore"].dropna().unique())
    fornitore_sel = st.multiselect("Fornitore", fornitori, default=fornitori)
    
    date_min = pd.to_datetime(df_all["data_listino"]).min()
    date_max = pd.to_datetime(df_all["data_listino"]).max()
    date_range = st.date_input("Intervallo data listino", [date_min, date_max])

    search_text = st.text_input("Testo libero (prodotto, note...)")

# Filtraggio iniziale
df_filtrato = df_all[
    df_all["fornitore"].isin(fornitore_sel) &
    (pd.to_datetime(df_all["data_listino"]) >= pd.to_datetime(date_range[0])) &
    (pd.to_datetime(df_all["data_listino"]) <= pd.to_datetime(date_range[1]))
].copy()

# Ricerca parole chiave più veloce
parole = search_text.lower().split() if search_text else []
if parole:
    df_filtrato["testo_completo"] = df_filtrato.astype(str).agg(" ".join, axis=1).str.lower()
    for parola in parole:
        df_filtrato = df_filtrato[df_filtrato["testo_completo"].str.contains(parola, na=False)]
    df_filtrato.drop(columns="testo_completo", inplace=True)

# Calcolo parole più frequenti
if not df_filtrato.empty and "descrizione_prodotto" in df_filtrato.columns:
    testo = " ".join(df_filtrato["descrizione_prodotto"].dropna().str.lower())
    parole_grezze = re.findall(r'\b\w+\b', testo)
    parole_filtrate = [p for p in parole_grezze if len(p) > 1 and not p.isnumeric()]
    comuni = Counter(parole_filtrate).most_common(25)

    st.sidebar.markdown("### 🏷️ Parole più frequenti")
    tag_html = "<div style='display: flex; flex-wrap: wrap; gap: 6px;'>"
    for parola, count in comuni:
        tag_html += f"<span style='background-color:#005caa; color:white; padding:4px 10px; border-radius:16px; font-size:13px;'>{parola} ({count})</span>"
    tag_html += "</div>"
    st.sidebar.markdown(tag_html, unsafe_allow_html=True)

# Paginazione
offset = (page_number - 1) * page_size
df_filtrato = df_filtrato.sort_values(by=["fornitore", "descrizione_prodotto", "prezzo"], ascending=[True, True, True])
df_pagina = df_filtrato.iloc[offset:offset + page_size]


st.markdown(f"<h5>✅ {len(df_pagina)} risultati nella pagina {page_number} su {len(df_filtrato)} risultati totali filtrati • {math.ceil(len(df_filtrato)/page_size)} pagine totali</h5>", unsafe_allow_html=True)

# Ordine colonne
colonne_base = [col for col in df_pagina.columns if col not in ["id", "categoria", "data_caricamento", "nome_file"]]
if "prezzo" in colonne_base and "descrizione_prodotto" in colonne_base:
    colonne_base.remove("prezzo")
    colonne_base.insert(colonne_base.index("descrizione_prodotto"), "prezzo")
df_display = df_pagina[colonne_base].copy()

# Favicon per Fornitori
def aggiungi_favicon(fornitore):
    nome = str(fornitore).upper()
    if nome == "GRAUS":
        icona = '<img src="https://www.graus.bz.it/favicon.ico" style="height:16px; vertical-align:middle; margin-left:4px;">'
    elif nome == "VINUM":
        icona = '<img src="https://vinum.it/wp-content/uploads/favicon-1.png" style="height:16px; vertical-align:middle; margin-left:4px;">'
    elif nome == "WINESTORE":
        icona = '<img src="https://weindiele.com/media/image/storage/opc/Slider/wine.png" style="height:16px; vertical-align:middle; margin-left:4px;">'
    else:
        icona = ''
    return f"{fornitore}{icona}"

df_display["fornitore"] = df_display["fornitore"].apply(aggiungi_favicon)


# Evidenzia parole ricercate
def evidenzia_html(val, parole, fornitore=None):
    val_str = str(val)
    colore = "#d0ebff" if "graus" in str(fornitore).lower() else "yellow"
    for parola in parole:
        pattern = re.compile(re.escape(parola), re.IGNORECASE)
        val_str = pattern.sub(lambda m: f'<mark style="background-color:{colore}">{m.group(0)}</mark>', val_str)
    return val_str

if parole:
    for col in df_display.columns:
        df_display[col] = [
            evidenzia_html(val, parole, fornitore=row["fornitore"])
            for val, row in zip(df_display[col], df_pagina.to_dict("records"))
        ]

# Costruzione tabella HTML
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
    return f"""
        <table class='styled-table'>
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows}</tbody>
        </table>
    """

# CSS tabella
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
    .styled-table tr:nth-child(even){background-color: #f9f9f9;}
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

# Tabella
st.markdown(build_custom_html_table(df_display), unsafe_allow_html=True)

# Download Excel
if not df_pagina.empty:
    buffer = io.BytesIO()
    df_pagina.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button("📥 Scarica solo questa pagina", data=buffer, file_name="pagina.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if not df_filtrato.empty:
    all_buffer = io.BytesIO()
    df_filtrato.to_excel(all_buffer, index=False, engine="openpyxl")
    all_buffer.seek(0)
    st.download_button("📥 Scarica tutti i risultati filtrati", data=all_buffer, file_name="completo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
