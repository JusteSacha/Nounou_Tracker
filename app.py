import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from utils import load_data, save_data, calculate_hours, export_pdf

# Fuseau horaire
tz = pytz.timezone("Europe/Paris")

st.set_page_config(page_title="Suivi Garde Enfant", layout="centered")
st.title("👶 Nounou Tracker - Suivi des Heures de Garde")

# Chargement des données
data = load_data()

# Boutons : Déposer et Récupérer bébé
st.header("💼 Gestion des heures de dépose et de récupération")

col1, col2 = st.columns(2)
with col1:
    id_depose = st.number_input("ID Créneau Dépose", min_value=1, step=1)
    date_depose = st.date_input("📅 Date de dépose", value=datetime.today())
    heure_depose = st.time_input("🕒 Heure de dépose")
    if st.button("Je dépose bébé"):
        ajouter_depose(data, id_depose, date_depose, heure_depose)
        st.success("✅ Heure de dépose ajoutée.")

with col2:
    id_recup = st.number_input("ID Créneau Récupération", min_value=1, step=1)
    date_recup = st.date_input("📅 Date de récupération", value=datetime.today())
    heure_recup = st.time_input("🕔 Heure de récupération")
    if st.button("Je récupère bébé"):
        ajouter_recuperation(data, id_recup, date_recup, heure_recup)
        st.success("✅ Heure de récupération ajoutée.")

# Formulaire classique d'entrée
st.header("📝 Ajouter une journée de garde")
with st.form("entry_form"):
    date = st.date_input("📅 Date", value=datetime.now(tz).date())
    heure_debut = st.time_input("🕒 Heure de début")
    heure_fin = st.time_input("🕔 Heure de fin")
    pause_minutes = st.number_input("⏸️ Pause (minutes)", min_value=0, value=0, step=5)
    submitted = st.form_submit_button("Ajouter")

    if submitted:
        total_heures = calculate_hours(heure_debut, heure_fin, pause_minutes)
        new_id = int(data["ID"].max()) + 1 if not data.empty else 1
        new_row = pd.DataFrame([[new_id, date, heure_debut, heure_fin, pause_minutes, total_heures]],
                               columns=["ID", "Date", "Heure Début", "Heure Fin", "Pause (min)", "Durée (h)"])
        data = pd.concat([data, new_row], ignore_index=True)
        save_data(data)
        st.success("✅ Journée ajoutée !")

# Affichage synthèse
st.header("📊 Synthèse des heures")
if not data.empty:
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values("Date")

    mois_selectionne = st.selectbox("📆 Choisir un mois", sorted(data["Date"].dt.strftime('%Y-%m').unique(), reverse=True))
    df_mois = data[data["Date"].dt.strftime('%Y-%m') == mois_selectionne]
    total_mois = round(df_mois["Durée (h)"].sum(), 2)

    st.subheader(f"🗓️ Mois : {mois_selectionne}")
    st.write(f"**Total d'heures de garde :** ⏱️ {total_mois} heures")
    st.dataframe(df_mois)

    # 🗑️ Suppression
    st.subheader("🗑️ Supprimer un créneau")
    if not df_mois.empty and "ID" in df_mois.columns:
        ligne_a_supprimer = st.selectbox(
            "Sélectionner un créneau à supprimer",
            df_mois.apply(lambda row: f"{int(row['ID'])} | {row['Date'].strftime('%Y-%m-%d')}", axis=1)
        )

        if st.button("Supprimer ce créneau"):
            id_selection = int(ligne_a_supprimer.split(" | ")[0])
            data = data[data["ID"] != id_selection]
            save_data(data)
            st.success("✅ Créneau supprimé avec succès. Recharge l'app pour voir les changements.")
    else:
        st.info("Aucun créneau à supprimer ce mois-ci.")

    # 📤 Export PDF
    if st.button("📤 Exporter la synthèse en PDF"):
        pdf_path = export_pdf(df_mois, mois_selectionne)
        st.success("✅ PDF généré avec succès")
        st.download_button(label="📄 Télécharger le PDF", data=open(pdf_path, "rb").read(),
                           file_name=f"synthese_{mois_selectionne}.pdf", mime="application/pdf")
else:
    st.info("Aucune donnée disponible. Commence par ajouter une journée.")
