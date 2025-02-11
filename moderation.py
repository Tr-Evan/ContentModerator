import boto3
import cv2
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer les clés AWS depuis les variables d'environnement
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

# Initialisation du client AWS Rekognition
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-1'  
)

def check_filetype(file_path):
    """Détecte le type de fichier."""
    if file_path.endswith(('.png', '.jpg', '.jpeg')):
        return 'image'
    elif file_path.endswith(('.mp4', '.avi')):
        return 'video'
    elif file_path.endswith('.txt'):
        return 'text'
    else:
        return 'unknown'

def extract_frame_video(video_path):
    """Extrait une image d'une vidéo."""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if ret:
        image_path = video_path + '_frame.jpg'
        cv2.imwrite(image_path, frame)
        return image_path
    return None

def moderate_image(image_path):
    """Utilise AWS Rekognition pour détecter du contenu inapproprié."""
    with open(image_path, 'rb') as image_file:
        response = rekognition.detect_moderation_labels(
            Image={'Bytes': image_file.read()}
        )
    return response.get('ModerationLabels', [])

def process_media(file_path):
    """Traite le contenu : texte, vidéo ou image."""
    file_type = check_filetype(file_path)

    if file_type == 'image':
        return {'ModerationLabels': moderate_image(file_path)}
    elif file_type == 'video':
        frame_path = extract_frame_video(file_path)
        if frame_path:
            return {'ModerationLabels': moderate_image(frame_path)}
    elif file_type == 'text':
        with open(file_path, 'r') as file:
            content = file.read()
            return {'TextContent': content}
    else:
        return {'Error': 'Type de fichier non supporté'}
