
import streamlit as st
import pandas as pd
from xhtml2pdf import pisa
import tempfile

# URL CSV Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/147uce6_Mj39nNxIjIWphu0Gt-CCpknDtzS0-MnR6XWo/export?format=csv&gid=384822597"
df = pd.read_csv(sheet_url)

# Funzione per il colore della colonna E
def get_font_color(value):
    v = str(value).upper()
    if 'BIANCHI FRIZZANTI' in v:
        return '#89B34B'
    elif 'ROSSI FRIZZANTI' in v:
        return '#A63E3E'
    elif 'BIANCHI' in v:
        return '#FFD700'
    elif 'ROSE' in v:
        return '#F15C77'
    elif 'ROSSI' in v and 'FRIZZANTI' not in v:
        return '#B13232'
    elif any(x in v for x in ['PROSECCO', 'CHAMPAGNE', 'SPUMANTI']):
        return '#005caa'
    elif any(x in v for x in ['DOLCI', 'PASSITI', 'LIQUOROSI', 'FORTIFICATI']):
        return '#E9967A'
    elif 'CIDER' in v:
        return '#E5A000'
    elif 'ORANGE' in v:
        return '#D4631A'
    elif 'BRULE' in v:
        return '#D6551C'
    else:
        return '#000000'

# Costruisci HTML della tabella
html = "<div style='font-family: Nunito; font-size: 12px;'>"
html += "<h2>📋 Listino Vini Formattato</h2>"
html += "<table style='border-collapse: collapse; width: 100%;'>"

html += "<tr>"
for col in df.columns:
    html += f"<th style='border-bottom: 2px solid #005caa; padding: 6px; text-align: left;'>{col}</th>"
html += "</tr>"

for _, row in df.iterrows():
    color = get_font_color(row['E']) if pd.notna(row['E']) else '#000000'
    html += "<tr>"
    for i, cell in enumerate(row):
        style = "padding: 6px; border-bottom: 1px dotted #ccc;"
        if i == 2:
            style += "font-family: Bree Serif; font-size: 20px; color: #005caa;"
        elif i == 3:
            style += "font-weight: bold; font-size: 10px; color: #005caa;"
        elif i == 4:
            style += f"font-family: Comfortaa; font-size: 10px; color: white; background-color: {color};"
        elif i == 5:
            style += "font-size: 10px;"
        elif i in [6, 7, 8, 9]:
            style += "font-size: 10px; border: 1px dotted black;"
        html += f"<td style='{style}'>{cell}</td>"
    html += "</tr>"

html += "</table></div>"

# Mostra in Streamlit
st.markdown(html, unsafe_allow_html=True)

# Pulsante per salvare come PDF
if st.button("📄 Scarica PDF"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pisa.CreatePDF(html, dest=tmp)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        st.download_button("Download PDF", data=f, file_name="listino_vini.pdf", mime="application/pdf")
