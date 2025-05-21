
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# CONFIGURAZIONE SUPABASE
SUPABASE_URL = "https://fkyvrsoiaoackpijprmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZreXZyc29pYW9hY2twaWpwcm1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MTE3NjgsImV4cCI6MjA2MzM4Nzc2OH0.KX6KlwgKitJxBYwEIEXeG2_ErBvkGLkYyOoxiL7s-Gw"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Consulta Listini", layout="wide")
st.title("📊 Consulta Listini Caricati")

# Caricamento dati da Supabase
with st.spinner("📥 Caricamento dati..."):
    response = supabase.table("listini").select("*").execute()
    data = response.data
    df = pd.DataFrame(data)

if df.empty:
    st.warning("⚠️ Nessun dato trovato.")
    st.stop()

# Filtri
with st.sidebar:
    st.header("🔍 Filtri")
    fornitori = df["fornitore"].unique().tolist()
    fornitore_sel = st.multiselect("Fornitore", fornitori, default=fornitori)

    date_min = pd.to_datetime(df["data_listino"]).min()
    date_max = pd.to_datetime(df["data_listino"]).max()
    date_range = st.date_input("Intervallo data listino", [date_min, date_max])

    search_text = st.text_input("Testo libero (prodotto, note...)")

# Applica filtri
df_filtrato = df[
    df["fornitore"].isin(fornitore_sel) &
    (pd.to_datetime(df["data_listino"]) >= pd.to_datetime(date_range[0])) &
    (pd.to_datetime(df["data_listino"]) <= pd.to_datetime(date_range[1]))
]

if search_text:
    df_filtrato = df_filtrato[df_filtrato.apply(lambda row: search_text.lower() in str(row).lower(), axis=1)]

st.success(f"✅ {len(df_filtrato)} risultati trovati.")
st.dataframe(df_filtrato)

# Esporta in Excel
if not df_filtrato.empty:
    excel = df_filtrato.to_excel(index=False, engine='openpyxl')
    st.download_button("📥 Scarica Excel", data=excel, file_name="listini_filtrati.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
