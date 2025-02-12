import streamlit as st
from moderation import process_media
from moderation import get_aws_session
import os
import time
from dotenv import load_dotenv

# Initialisation du dossier d'upload
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Initialisation des credentials dans la session si non présents
if 'aws_access_key' not in st.session_state:
    st.session_state.aws_access_key = ""
if 'aws_secret_key' not in st.session_state:
    st.session_state.aws_secret_key = ""
if 's3_bucket_name' not in st.session_state:
    st.session_state.s3_bucket_name = ""

# Barre latérale pour la configuration AWS
st.sidebar.header("⚙️ Configuration")

# Option pour charger les credentials depuis un fichier .env
if st.sidebar.button("📥 Charger credentials depuis .env"):
    load_dotenv()
    st.session_state.aws_access_key = os.getenv("ACCESS_KEY")
    st.session_state.aws_secret_key = os.getenv("SECRET_KEY")
    st.session_state.s3_bucket_name = os.getenv("S3_BUCKET")
    st.sidebar.success("Clés AWS chargées depuis .env")

# Champs pour les credentials AWS (saisie manuelle)
new_access_key = st.sidebar.text_input("🔑 Access Key", value=st.session_state.aws_access_key, type="password")
new_secret_key = st.sidebar.text_input("🔒 Secret Key", value=st.session_state.aws_secret_key, type="password")
new_s3_bucket = st.sidebar.text_input("🗂️ Nom du bucket S3", value=st.session_state.s3_bucket_name)
print(new_access_key, st.session_state.aws_access_key)

if st.sidebar.button("Appliquer les changements"):
    if (new_access_key != st.session_state.aws_access_key or
        new_secret_key != st.session_state.aws_secret_key or
        new_s3_bucket != st.session_state.s3_bucket_name):

        # Mettre à jour les variables
        st.session_state.aws_access_key = new_access_key
        st.session_state.aws_secret_key = new_secret_key
        st.session_state.s3_bucket_name = new_s3_bucket
        print(st.session_state.aws_access_key)

        # Mettre à jour le fichier `.env`
        with open(".env", "w") as f:
            f.write(f"ACCESS_KEY={new_access_key}\n")
            f.write(f"SECRET_KEY={new_secret_key}\n")
            f.write(f"S3_BUCKET={new_s3_bucket}\n")

        st.success("🔄 Changement détecté ! Redémarrage en cours...")
        time.sleep(1)

# Vérification des credentials
if not st.session_state.aws_access_key or not st.session_state.aws_secret_key or not st.session_state.s3_bucket_name:
    st.warning("⚠️ Veuillez configurer vos credentials AWS dans la barre latérale")
else:
    # Titre de l'application
    st.title("📸 Content Moderator Pro")
    st.subheader("Analysez et modérez votre contenu en un clic !")

    # Téléchargement de fichier
    uploaded_file = st.file_uploader("📤 Choisissez un fichier (image ou vidéo)", type=["jpg", "jpeg", "png", "mp4", "avi"])

    # Traitement du fichier si téléchargé
    if uploaded_file is not None:
        # Chemin complet pour enregistrer le fichier
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        # Sauvegarder le fichier dans le dossier "uploads"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Bouton pour lancer la modération
        if st.button("🚀 Lancer la modération"):
            with st.spinner("Analyse en cours..."):
                result = process_media(file_path)
            # Affichage des résultats
            if 'sensitize' in result and result['sensitize']:
                st.error("### ⚠️ Contenu inapproprié détecté")
                st.error("Thèmes sensibles détectés :")
                for label in result['sensitize']:
                    st.write(f"⚠️ {label['Name']}")
            else:
                st.success("✅ Aucun contenu inapproprié détecté.")
                # Affichage du contenu approprié
                if uploaded_file.type.startswith("image"):
                    st.image(file_path, use_container_width=True)
                elif uploaded_file.type.startswith("video"):
                    st.video(file_path)

                for hashtag in result['hashtags']:
                    st.write(f"{hashtag}")
                # Exemple de hashtags générés automatiquement

                # Option de voir la transcription pour les vidéos
                if uploaded_file.type.startswith("video"):
                    with st.expander("Voir la transcription"):
                        st.write(result['subtitles'])
