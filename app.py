import streamlit as st
from moderation import process_media
import os
import time
from dotenv import load_dotenv
import boto3
from moderation import process_media

# Initialisation du dossier d'upload
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Chargement des variables d'environnement
load_dotenv()

def update_env_file(access_key, secret_key, bucket_name):
    env_file = ".env"
    env_data = [
        f"ACCESS_KEY={access_key}\n",
        f"SECRET_KEY={secret_key}\n",
        f"S3_BUCKET={bucket_name}\n"
    ]

    with open(env_file, "w") as f:
        f.writelines(env_data)

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
    st.session_state.aws_access_key = os.getenv("ACCESS_KEY")
    st.session_state.aws_secret_key = os.getenv("SECRET_KEY")
    st.session_state.s3_bucket_name = os.getenv("S3_BUCKET")
    st.sidebar.success("Clés AWS chargées depuis .env")

# Champs pour les credentials AWS (saisie manuelle)
st.session_state.aws_access_key = st.sidebar.text_input("🔑 Access Key", value=st.session_state.aws_access_key, type="password")
st.session_state.aws_secret_key = st.sidebar.text_input("🔒 Secret Key", value=st.session_state.aws_secret_key, type="password")
st.session_state.s3_bucket_name = st.sidebar.text_input("🗂️ Nom du bucket S3", value=st.session_state.s3_bucket_name)
update_env_file(st.session_state.aws_access_key, st.session_state.aws_secret_key, st.session_state.s3_bucket_name)

# Vérification des credentials
if not st.session_state.aws_access_key or not st.session_state.aws_secret_key or not st.session_state.s3_bucket_name:
    st.warning("⚠️ Veuillez configurer vos credentials AWS dans la barre latérale")
else:
    # Initialisation du client AWS Rekognition
    rekognition_client = boto3.client(
        'rekognition',
        aws_access_key_id=st.session_state.aws_access_key,
        aws_secret_access_key=st.session_state.aws_secret_key,
        region_name='us-east-1'  # Remplace par ta région AWS si différente
    )

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
                result = process_media(file_path)  # Le client Rekognition est maintenant géré dans moderation.py

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
                    st.image(file_path, caption='Contenu téléchargé', use_container_width=True)
                elif uploaded_file.type.startswith("video"):
                    st.video(file_path)

                # Exemple de hashtags générés automatiquement
                st.write("#### Hashtags générés automatiquement :")

                hashtag_style = """
                <style>
                .hashtag {
                    display: inline-block;
                    background-color: #e3f2fd;
                    color: #0277bd;
                    padding: 6px 14px;
                    margin: 4px;
                    border-radius: 20px;
                    font-weight: 500;
                    font-size: 14px;
                    transition: background-color 0.3s ease;
                }
                .hashtag:hover {
                    background-color: #bbdefb;
                }
                </style>
                """
                st.markdown(hashtag_style, unsafe_allow_html=True)

                if 'hashtags' in result:
                    hashtags_html = "".join([f'<span class="hashtag">{hashtag}</span>' for hashtag in result['hashtags']])
                    st.markdown(hashtags_html, unsafe_allow_html=True)

               # Option de voir la transcription pour les vidéos
                if uploaded_file.type.startswith("video"):
                    with st.expander("Voir la transcription"):
                        st.write(result['subtitles'])