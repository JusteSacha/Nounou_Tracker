import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF

DATA_FILE = "garde_data.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        if "ID" not in df.columns:
            df["ID"] = range(1, len(df)+1)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["ID", "Date", "Heure Début", "Heure Fin", "Pause (min)", "Durée (h)", "Dépose", "Récupération"])

def save_data(df):
    df = df.copy()
    if "ID" not in df.columns or df["ID"].isnull().any():
        df["ID"] = range(1, len(df) + 1)
    else:
        df["ID"] = df["ID"].astype(int)
    df.reset_index(drop=True, inplace=True)
    df.to_csv(DATA_FILE, index=False)

from datetime import datetime, timedelta

from datetime import datetime, timedelta

def calculate_hours(start, end, pause_min):
    """
    Calcule la durée en heures entre deux objets datetime.time,
    en déduisant la pause en minutes, sans tenir compte des secondes.
    """
    # Si start ou end sont des chaînes de caractères, on les transforme en objets datetime.time
    if isinstance(start, str):
        start = datetime.strptime(start, "%H:%M").time()
    if isinstance(end, str):
        end = datetime.strptime(end, "%H:%M").time()

    # Vérification et conversion si nécessaire, pour que start et end soient des objets datetime.time
    if isinstance(start, datetime):
        start = start.time()
    if isinstance(end, datetime):
        end = end.time()

    # Combinaison des heures avec la date pour créer des objets datetime
    dt_start = datetime.combine(datetime.today(), start)
    dt_end = datetime.combine(datetime.today(), end)

    # Si l'heure de fin est avant l'heure de début (exemple : garde de nuit), on ajoute un jour à l'heure de fin
    if dt_end < dt_start:
        dt_end += timedelta(days=1)

    # Calcul de la durée en prenant en compte la pause
    duration = dt_end - dt_start - timedelta(minutes=pause_min)

    # Conversion de la durée en heures (avec un format arrondi à 2 décimales)
    hours = round(duration.total_seconds() / 3600, 2)

    # Retourne 0 si la durée est négative (pour éviter des résultats incorrects)
    return max(hours, 0)

def export_pdf(df, mois):
    """
    Exporte une synthèse des heures de garde sous forme de fichier PDF.
    """
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

def ajouter_depose(data, id, date, heure_debut):
    """
    Ajoute l'heure de dépose à la donnée.
    """
    data.loc[data['ID'] == id, 'Dépose'] = f"{date} {heure_debut}"
    save_data(data)

def ajouter_recuperation(data, id, date, heure_fin):
    """
    Ajoute l'heure de récupération à la donnée.
    """
    data.loc[data['ID'] == id, 'Récupération'] = f"{date} {heure_fin}"
    save_data(data)
