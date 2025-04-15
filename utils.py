import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF

DATA_FILE = "garde_data.csv"

def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Heure Début", "Heure Fin", "Pause (min)", "Durée (h)"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def calculate_hours(start, end, pause_min):
    fmt = "%H:%M:%S"
    debut = datetime.strptime(str(start), fmt)
    fin = datetime.strptime(str(end), fmt)
    duree = (fin - debut - timedelta(minutes=pause_min)).total_seconds() / 3600
    return round(duree, 2)

def export_pdf(df, mois):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Synthèse des heures de garde - {mois}", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)

    for index, row in df.iterrows():
        ligne = f"{row['Date']} : {row['Heure Début']} - {row['Heure Fin']} (Pause: {row['Pause (min)']} min) → {row['Durée (h)']} h"
        pdf.cell(200, 10, ligne, ln=True)

    total = round(df["Durée (h)"].sum(), 2)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, f"Total mensuel : {total} heures", ln=True)

    path = f"synthese_{mois}.pdf"
    pdf.output(path)
    return path