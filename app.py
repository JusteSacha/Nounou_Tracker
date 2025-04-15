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
st.header("🚼 Enregistrement rapide")

col1, col2 = st.columns(2)

with col1:
    if st.button("🟢 Je dépose bébé"):
        now = datetime.now(tz)
        new_id = int(data["ID"].max()) + 1 if not data.empty else 1
        new_row = pd.DataFrame([[new_id, now.date(), now.time(), None, 0, None]],
                               columns=["ID", "Date", "Heure Début", "Heure Fin", "Pause (min)", "Durée (h)"])
        data = pd.concat([data, new_row], ignore_index=True)
        save_data(data)
        st.success(f"Bébé déposé à {now.strftime('%H:%M')}")

with col2:
    if st.button("🔴 Je récupère bébé"):
        now = datetime.now(tz)
        last_entry = data[data["Heure Fin"].isnull()].sort_values("Date").tail(1)
        if not last_entry.empty:
            idx = last_entry.index[0]
            heure_debut = pd.to_datetime(str(data.loc[idx, "Heure Début"]))
            heure_fin = now.time()
            duree = calculate_hours(heure_debut.time(), heure_fin, int(data.loc[idx, "Pause (min)"]))
            data.at[idx, "Heure Fin"] = heure_fin
            data.at[idx, "Durée (h)"] = duree
            save_data(data)
            st.success(f"Bébé récupéré à {now.strftime('%H:%M')} – {duree} h enregistrées.")
        else:
            st.warning("Aucune entrée sans heure de fin trouvée.")


# Formulaire classique d'entrée
st.header("📝 Ajouter une journée de garde")
with st.form("entry_form"):
    date = st.date_input("📅 Date", value=datetime.now(tz).date())
    
    # Heure de début
    heure_debut = st.time_input("🕒 Heure de début", value=datetime.strptime("09:00", "%H:%M").time())
    if heure_debut < datetime.strptime("07:00", "%H:%M").time():
        heure_debut = datetime.strptime("07:00", "%H:%M").time()
    elif heure_debut > datetime.strptime("18:00", "%H:%M").time():
        heure_debut = datetime.strptime("18:00", "%H:%M").time()

    # Heure de fin
    heure_fin = st.time_input("🕔 Heure de fin", value=datetime.strptime("16:00", "%H:%M").time())
    if heure_fin < datetime.strptime("07:00", "%H:%M").time():
        heure_fin = datetime.strptime("07:00", "%H:%M").time()
    elif heure_fin > datetime.strptime("18:00", "%H:%M").time():
        heure_fin = datetime.strptime("18:00", "%H:%M").time()

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
    df_mois = data[data["Date"].dt.strftime('%Y-%m') == mois_selectionne].copy()
    total_mois = round(df_mois["Durée (h)"].sum(), 2)

    # Formater les heures (Heure Début, Heure Fin) pour ne pas afficher les secondes
    df_mois["Heure Début"] = df_mois["Heure Début"].apply(lambda x: x.strftime("%H:%M") if pd.notnull(x) else "")
    df_mois["Heure Fin"] = df_mois["Heure Fin"].apply(lambda x: x.strftime("%H:%M") if pd.notnull(x) else "")

    # ✅ Formater la date pour l'affichage
    df_mois["Date_str"] = df_mois["Date"].dt.strftime("%Y-%m-%d")

    st.subheader(f"🗓️ Mois : {mois_selectionne}")
    st.write(f"**Total d'heures de garde :** ⏱️ {total_mois} heures")
    st.dataframe(df_mois.drop(columns=["Date_str"]))

    # 🗑️ Suppression
    st.subheader("🗑️ Supprimer un créneau")
    if not df_mois.empty and "ID" in df_mois.columns:
        options_suppr = df_mois.apply(lambda row: f"{int(row['ID'])} | {row['Date'].strftime('%Y-%m-%d')}", axis=1)
        ligne_a_supprimer = st.selectbox("Sélectionner un créneau à supprimer", options_suppr)

        if st.button("Supprimer ce créneau"):
            id_selection = int(ligne_a_supprimer.split(" | ")[0])
            data = data[data["ID"] != id_selection]
            save_data(data)
            st.success("✅ Créneau supprimé avec succès. Recharge l'app pour voir les changements.")
    else:
        st.info("Aucun créneau à supprimer ce mois-ci.")

    # 📤 Export PDF
    if st.button("📤 Exporter la synthèse en PDF"):
        pdf_path = export_pdf(df_mois.drop(columns=["Date_str"]), mois_selectionne)
        st.success("✅ PDF généré avec succès")
        st.download_button(label="📄 Télécharger le PDF", data=open(pdf_path, "rb").read(),
                           file_name=f"synthese_{mois_selectionne}.pdf", mime="application/pdf")
else:
    st.info("Aucune donnée disponible. Commence par ajouter une journée.")
