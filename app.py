import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils import load_data, save_data, calculate_hours, export_pdf

st.set_page_config(page_title="Suivi Garde Enfant", layout="centered")
st.title("👶 Nounou Tracker - Suivi des Heures de Garde")

# Chargement des données
data = load_data()

# Boutons rapides
st.header("🚼 Dépôt / Récupération express")

if st.button("🟢 Je dépose bébé"):
    now = datetime.now()
    new_id = int(data["ID"].max()) + 1 if not data.empty else 1
    new_row = pd.DataFrame([[new_id, now.date(), now.time(), pd.NaT, 0, 0]],
                           columns=["ID", "Date", "Heure Début", "Heure Fin", "Pause (min)", "Durée (h)"])
    data = pd.concat([data, new_row], ignore_index=True)
    save_data(data)
    st.success(f"✅ Déposé à {now.strftime('%H:%M')} le {now.strftime('%d/%m/%Y')}")

if st.button("🔴 Je récupère bébé"):
    ongoing = data[data["Heure Fin"].isna()]
    if not ongoing.empty:
        idx = ongoing.index[-1]  # dernière ligne sans "Heure Fin"
        now = datetime.now()
        data.at[idx, "Heure Fin"] = now.time()
        # Recalcul de la durée
        heure_debut = pd.to_datetime(str(data.at[idx, "Date"]) + ' ' + str(data.at[idx, "Heure Début"]))
        heure_fin = pd.to_datetime(str(data.at[idx, "Date"]) + ' ' + str(now.time()))
        duree = (heure_fin - heure_debut).total_seconds() / 3600
        data.at[idx, "Durée (h)"] = round(duree, 2)
        save_data(data)
        st.success(f"✅ Bébé récupéré à {now.strftime('%H:%M')}. Durée : {round(duree,2)} h")
    else:
        st.warning("⚠️ Aucun dépôt en attente de récupération.")


# Formulaire d'entrée
st.header("📝 Ajouter une journée de garde")
with st.form("entry_form"):
    date = st.date_input("📅 Date", value=datetime.today())
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

# Affichage des données
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
            df_mois.apply(lambda row: f"{int(row['ID'])} | {row['Date']}", axis=1)
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
