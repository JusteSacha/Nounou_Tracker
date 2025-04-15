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
# Affichage synthèse
st.header("📊 Synthèse des heures")

if not data.empty:
    # S'assurer que Date est bien au format datetime.date (pas datetime complet)
    data["Date"] = pd.to_datetime(data["Date"], errors='coerce').dt.date

    # Trier les données par date
    data = data.sort_values("Date")

    # Extraire tous les mois uniques sous forme "YYYY-MM"
    mois_uniques = sorted({d.strftime('%Y-%m') for d in data["Date"]}, reverse=True)
    mois_selectionne = st.selectbox("📆 Choisir un mois", mois_uniques)

    # Filtrer le DataFrame pour le mois sélectionné
    df_mois = data[[d.strftime('%Y-%m') == mois_selectionne for d in data["Date"]]].copy()

    # Formater les heures pour afficher HH:MM sans les secondes
    df_mois["Heure Début"] = pd.to_datetime(df_mois["Heure Début"].astype(str), format="%H:%M:%S", errors="coerce").dt.strftime("%H:%M")
    df_mois["Heure Fin"] = pd.to_datetime(df_mois["Heure Fin"].astype(str), format="%H:%M:%S", errors="coerce").dt.strftime("%H:%M")

    # Formater la date en JJ/MM/AAAA pour affichage
    df_mois["Date"] = df_mois["Date"].apply(lambda d: d.strftime("%d/%m/%Y") if pd.notnull(d) else "")

    # Calcul total
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
