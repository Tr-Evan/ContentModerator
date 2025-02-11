import boto3
import cv2
import os
import tempfile
import time
import json
import urllib.request
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from dotenv import load_dotenv
from collections import Counter
from botocore.exceptions import ClientError

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les clés AWS depuis les variables d'environnement
S3_BUCKET = os.getenv('S3_BUCKET')
REGION_NAME = 'us-east-1'

#Initialisation de la session AWS avec les clés
aws_session = boto3.Session(
    aws_access_key_id=os.getenv("ACCESS_KEY"),
    aws_secret_access_key=os.getenv("SECRET_KEY"),
)
s3 = aws_session.client('s3')

#Initalisation du bucket et configuration
s3.create_bucket(Bucket=S3_BUCKET)

#Initalisation des services AWS
rekognition = aws_session.client('rekognition',region_name=REGION_NAME)
transcribe = aws_session.client('transcribe',region_name=REGION_NAME)
comprehend = aws_session.client('comprehend',region_name=REGION_NAME)


def check_filetype(filename):
 # Extrait le nom de base du fichier à partir du chemin de fichier fourni.
    file_basename = os.path.basename(filename)

    # Sépare le nom de base sur le point et prend la dernière partie comme extension.
    extension = file_basename.split(".")[-1]

    # Détermine le type de fichier en fonction de l'extension.
    if extension in ["jpg", "png", "tiff", "svg"]:
        filetype = "image"
    elif extension in ["mp4", "avi", "mkv"]:
        filetype = "vidéo"
    else:
        filetype = None

    # Enregistre le type de fichier détecté.
    print(f"[INFO] : Le fichier {file_basename} est de type : {filetype}")
    
    return filetype

def extract_frame_video(video_path, frame_id):
    # Ouvre la vidéo à partir du chemin fourni.
    video = cv2.VideoCapture(video_path)

    # Positionne le lecteur vidéo sur l'image spécifiée par frame_id.
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

    # Lit l'image actuelle.
    success, image = video.read()

    # Si la lecture réussit (ret est True), retourne l'image.
    # Sinon, retourne None.
    return image if success else None

def moderate_image(image_path):
    """Utilise AWS Rekognition pour détecter du contenu inapproprié."""
    with open(image_path, 'rb') as image_file:
        response = rekognition.detect_moderation_labels(
            Image={'Bytes': image_file.read()}
        )
    return response.get('ModerationLabels', [])

def detect_objects(image_path):
    with open(image_path, 'rb') as image_file:
        # Charger l'image
        image_bytes = image_file.read()

    # Utiliser AWS Rekognition pour détecter les objets dans l'image
    response = rekognition.detect_labels(
        Image={'Bytes': image_bytes},
        MinConfidence=50  # Filtrer les résultats avec une confiance minimale de 50%
    )

    # Extraire les labels et trier par leur confiance
    labels = response['Labels']

    # Extraire les 10 premiers objets avec la plus grande confiance
    objects = [label['Name'] for label in labels[:10]]  # Limiter à 10 objets

    return objects

def detect_celebrities(image_path):
    with open(image_path, 'rb') as image_file:
        # Lire l'image
        image_bytes = image_file.read()

    response = rekognition.recognize_celebrities(
        Image={'Bytes': image_bytes}
    )

    celebrities = [celebrity['Name'] for celebrity in response['CelebrityFaces']]

    return celebrities[:10]

def detect_emotions(image_path):
    with open(image_path, 'rb') as image_file:
        # Lire l'image
        image_bytes = image_file.read()

    # Utiliser Rekognition pour détecter les visages et leurs attributs
    response = rekognition.detect_faces(
        Image={'Bytes': image_bytes},
        Attributes=['ALL']  # Demander tous les attributs, y compris les émotions
    )

    faces_info = []

    # Parcourir les visages détectés dans la réponse
    for face in response['FaceDetails']:
        face_data = {}

        # Récupérer le genre et la confiance associée
        face_data['Gender'] = {
            'Value': face['Gender']['Value'],
            'Confidence': face['Gender']['Confidence']
        }

        # Récupérer la plage d'âge estimée
        face_data['AgeRange'] = {
            'Low': face['AgeRange']['Low'],
            'High': face['AgeRange']['High']
        }

        # Récupérer les émotions et leur niveau de confiance
        emotions = sorted(face['Emotions'], key=lambda x: x['Confidence'], reverse=True)[:3]  # Top 3 émotions
        face_data['Emotions'] = [{'Type': emotion['Type'], 'Confidence': emotion['Confidence']} for emotion in emotions]

        # Ajouter les informations du visage à la liste
        faces_info.append(face_data)

    return faces_info

def summarize_emotions(faces_info):
    total_faces = len(faces_info)
    age_range = {'min': float('inf'), 'max': float('-inf'), 'total': 0}
    emotions_counter = Counter()
    emotion_confidences = {}
    gender_distribution = {'Male': 0, 'Female': 0}

    # Variables pour stocker les émotions dominantes
    dominant_emotion = None
    max_emotion_confidence = 0
    
    # Parcourir les visages détectés
    for face in faces_info:
        # Analyser le genre
        gender = face['Gender']['Value']
        gender_distribution[gender] += 1
        
        # Analyser l'âge (calcul de la moyenne du range)
        age_min = face['AgeRange']['Low']
        age_max = face['AgeRange']['High']
        age_range['total'] += (age_min + age_max) / 2
        age_range['min'] = min(age_range['min'], age_min)
        age_range['max'] = max(age_range['max'], age_max)
        
        # Analyser les émotions (avec confiance > 50%)
        for emotion in face['Emotions']:
            if emotion['Confidence'] > 50:
                emotion_type = emotion['Type']
                emotion_confidences[emotion_type] = emotion_confidences.get(emotion_type, 0) + emotion['Confidence']
                emotions_counter[emotion_type] += 1

                # Déterminer l'émotion dominante (celle avec la plus haute confiance)
                if emotion['Confidence'] > max_emotion_confidence:
                    max_emotion_confidence = emotion['Confidence']
                    dominant_emotion = emotion_type

    # Calcul de la confiance moyenne des émotions
    for emotion in emotions_counter:
        emotion_confidences[emotion] /= emotions_counter[emotion]
    
    # Calcul de la moyenne d'âge
    if total_faces > 0:
        average_age = age_range['total'] / total_faces
    else:
        average_age = None

    # Résumé des statistiques
    summary = {
        'total_faces': total_faces,
        'dominant_emotion': dominant_emotion,
        'emotion_statistics': {emotion: {
            'count': emotions_counter[emotion],
            'average_confidence': emotion_confidences[emotion]
        } for emotion in emotions_counter},
        'age_statistics': {
            'min_age': age_range['min'],
            'max_age': age_range['max'],
            'average_age': average_age
        },
        'gender_distribution': gender_distribution
    }

    return summary

def get_text_from_speech(filename, job_name):
    filename = filename.split('/')[-1]

    file_uri = f"s3://{S3_BUCKET}/{filename}"

    
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat=filename.split('.')[-1], 
        LanguageCode="fr-FR",  
        OutputBucketName=S3_BUCKET
    )

    # Attendre que la transcription soit terminée
    while True:
        response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        status = response["TranscriptionJob"]["TranscriptionJobStatus"]
        if status in ["COMPLETED", "FAILED"]:
            break
        time.sleep(5)  # Attente de 5 secondes avant de vérifier à nouveau

    if status == "FAILED":
        raise Exception("La transcription a échoué.")

    # Récupérer l'URL du fichier JSON contenant la transcription
    transcript_url = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    with urllib.request.urlopen(transcript_url) as url:
        data = json.loads(url.read().decode())
    return data["results"]["transcripts"][0]["transcript"]

def clean_text(raw_text):
    # Initialiser le tokenizer pour diviser le texte en mots
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(raw_text.lower())  # Convertir en minuscules et tokeniser

    # Charger les stop words en français
    stop_words = set(stopwords.words('french'))

    # Filtrer les tokens en enlevant les mots vides
    filtered_tokens = [word for word in tokens if word not in stop_words]

    # Retourner le texte nettoyé sous forme de chaîne
    return ' '.join(filtered_tokens)

def extract_keyphrases(text):
    response = comprehend.detect_key_phrases(
        Text=text,
        LanguageCode='fr'
    )

    key_phrases = sorted(response['KeyPhrases'], key=lambda x: x['Score'], reverse=True)
    
    top_key_phrases = key_phrases[:10]
    
    hashtags = ['#' + phrase['Text'].replace(" ", "").lower() for phrase in top_key_phrases]
    
    return hashtags

def process_media(media_file):
    media_type = check_filetype(media_file)
    # Si c'est une image
    if media_type == 'image':
        # Modération de l'image
        moderation_result = moderate_image(media_file)
        if moderation_result:
            return {'sensitize': moderation_result}

        # Utilisation d'un set pour éviter les doublons
        hashtags = set()

        # Détecter les objets dans l'image et les ajouter en hashtags
        objects = detect_objects(media_file)
        hashtags.update(f"#{obj.lower()}" for obj in objects)

        # Détecter les émotions des visages dans l'image
        emotions = detect_emotions(media_file)
        summary = summarize_emotions(emotions)

        # Ajouter l'émotion dominante sous forme de hashtag
        if summary["dominant_emotion"]:
            hashtags.add(f"#{summary['dominant_emotion'].lower()}")

        # Détecter les célébrités dans l'image
        celebrities = detect_celebrities(media_file)
        hashtags.update(f"#{celeb.replace(' ', '').lower()}" for celeb in celebrities)

        print(list(hashtags))
        return {'hashtags': list(hashtags)}
    # Si c'est une vidéo
    elif media_type == 'vidéo':
        first_frame = extract_frame_video(media_file, 0)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img_file:
            temp_img_path = temp_img_file.name
            cv2.imwrite(temp_img_path, first_frame)


        moderation_result = moderate_image(temp_img_path)
        
        if moderation_result:
            os.remove(temp_img_path)
            return {'sensitize': moderation_result}
            
        hashtags = set()

        video_filename = os.path.basename(media_file)
        video_name, video_ext = os.path.splitext(video_filename)
        
        timestamp = int(time.time())
        transcription = 'transcriptionText'
        job_name = f"{transcription}_{video_name}_{timestamp}"

        # Ajouter le timestamp avant l'extension
        video_filename = f"{video_name}_{timestamp}{video_ext}" 
        print(video_filename)

        s3.upload_file(media_file, S3_BUCKET, video_filename)

        transcript_text = get_text_from_speech(video_filename, job_name)
        print(transcript_text)
        
        cleaned_text = clean_text(transcript_text)
        print(cleaned_text)
        
        key_phrases = extract_keyphrases(cleaned_text)
        
        return {'subtitles': transcript_text , 'hashtags': list(set(key_phrases))}
