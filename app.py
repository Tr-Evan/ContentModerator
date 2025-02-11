import streamlit as st
from moderation import process_media
import os
from dotenv import load_dotenv

# Initialisation du dossier d'upload
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Chargement des variables d'environnement
load_dotenv()

# Barre latérale pour la configuration AWS
st.sidebar.header("⚙️ Configuration")

# Option pour charger les credentials depuis un fichier .env
if st.sidebar.button("📥 Charger credentials depuis .env"):
    aws_access_key = os.getenv("ACCESS_KEY")
    aws_secret_key = os.getenv("SECRET_KEY")
    s3_bucket_name = os.getenv("S3_BUCKET", "")
    st.sidebar.success("Clés AWS chargées depuis .env")
else:
    # Champs pour les credentials AWS (saisie manuelle)
    aws_access_key = st.sidebar.text_input("🔑 Access Key", type="password")
    aws_secret_key = st.sidebar.text_input("🔒 Secret Key", type="password")
    s3_bucket_name = st.sidebar.text_input("🗂️ Nom du bucket S3", "")

# Vérification des credentials
if not aws_access_key or not aws_secret_key or not s3_bucket_name:
    st.warning("⚠️ Veuillez configurer vos credentials AWS dans la barre latérale")
else:
    # Titre de l'application
    st.title("📸 Content Moderator Pro")
    st.subheader("Analysez et modérez votre contenu en un clic!")

    # Téléchargement de fichier
    uploaded_file = st.file_uploader("📤 Choisissez un fichier (image ou vidéo)", type=["jpg", "jpeg", "png", "mp4", "avi"])

    # Traitement du fichier si téléchargé
    if uploaded_file is not None:
        # Chemin complet pour enregistrer le fichier
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        # Sauvegarder le fichier dans le dossier "uploads"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info(f"Fichier reçu : {uploaded_file.name}")

        # Bouton pour lancer la modération
        if st.button("🚀 Lancer la modération"):
            with st.spinner("Analyse en cours..."):
                result = process_media(file_path)

            # Affichage des résultats
            if 'ModerationLabels' in result and result['ModerationLabels']:
                st.error("⚠️ Contenu inapproprié détecté :")
                for label in result['ModerationLabels']:
                    st.write(f"- {label['Name']} ({label['Confidence']:.2f}% de confiance)")

                st.write("### Thèmes sensibles détectés :")
                for label in result['ModerationLabels']:
                    st.write(f"- {label['Name']}")
            else:
                st.success("✅ Aucun contenu inapproprié détecté.")

                # Affichage du contenu approprié
                st.write("### Contenu approprié :")
                if uploaded_file.type.startswith("image"):
                    st.image(file_path, caption='Contenu téléchargé', use_column_width=True)
                elif uploaded_file.type.startswith("video"):
                    st.video(file_path)

                # Exemple de hashtags générés automatiquement
                st.write("#### Hashtags générés automatiquement :")
                st.write("#Happy #People #Friends #Fun")

                # Option de voir la transcription pour les vidéos
                if uploaded_file.type.startswith("video"):
                    st.write("#### Transcription de la vidéo :")
                    st.text_area("Transcription", "Transcription de la vidéo...", height=200)
