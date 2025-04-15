import pandas as pd
from datetime import datetime, timedelta
import os
from fpdf import FPDF

DATA_FILE = "garde_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Date"])
    else:
        return pd.DataFrame(columns=["ID", "Date", "Heure Début", "Heure Fin", "Pause (min)", "Durée (h)"])

def save_data(data):
    data.to_csv(DATA_FILE, index=False)

def calculate_hours(debut, fin, pause):
    """
    Calcule la durée en heures entre deux objets datetime.time,
    en déduisant la pause en minutes.
    """
    if isinstance(debut, str):
        debut = datetime.strptime(debut, "%H:%M:%S").time()
    if isinstance(fin, str):
        fin = datetime.strptime(fin, "%H:%M:%S").time()

    dt_debut = datetime.combine(datetime.today(), debut)
    dt_fin = datetime.combine(datetime.today(), fin)

    if dt_fin < dt_debut:
        dt_fin += timedelta(days=1)  # gestion des heures de nuit

    duration = dt_fin - dt_debut - timedelta(minutes=pause)
    hours = round(duration.total_seconds() / 3600, 2)
    return max(hours, 0)

def export_pdf(df, mois):
    """
    Exporte un dataframe au format PDF pour un mois donné.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_title(f"Synthèse des heures - {mois}")

    pdf.cell(200, 10, txt=f"Synthèse des heures de garde - {mois}", ln=True, align='C')
    pdf.ln(10)

    headers = ["Date", "Début", "Fin", "Pause", "Durée"]
    col_widths = [30, 25, 25, 25, 25]

    # En-tête
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1)
    pdf.ln()

    # Lignes
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, row["Date"].strftime("%Y-%m-%d"), border=1)
        pdf.cell(col_widths[1], 10, str(row["Heure Début"]), border=1)
        pdf.cell(col_widths[2], 10, str(row["Heure Fin"]), border=1)
        pdf.cell(col_widths[3], 10, str(int(row["Pause (min)"])) + " min", border=1)
        pdf.cell(col_widths[4], 10, f"{row['Durée (h)']} h", border=1)
        pdf.ln()

    total = round(df["Durée (h)"].sum(), 2)
    pdf.ln(5)
    pdf.set_font("Arial", "B", size=12)
    pdf.cell(0, 10, f"Total du mois : {total} heures", ln=True)

    output_path = f"synthese_{mois}.pdf"
    pdf.output(output_path)
    return output_path
