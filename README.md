# 📦 ContentModerator

Bienvenue dans **ContentModerator**, une application puissante qui utilise **AWS Rekognition** et **Streamlit** pour analyser des images, des vidéos et du texte afin de détecter du contenu inapproprié. 🚀

## 🌟 Fonctionnalités

- 📷 **Analyse d'images** : Détection de contenu sensible via AWS Rekognition.
- 🎥 **Analyse de vidéos** : Extraction d'images clés pour une modération efficace.
- 📊 **Interface intuitive** : Interface interactive créée avec Streamlit pour une expérience utilisateur optimale.

## 🔧 Installation

1. **Clone le repo :**

   ```bash
   git clone https://github.com/Tr-Evan/ContentModerator.git
   cd ContentModerator
   ```

2. **Installe les dépendances :**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure les variables d'environnement :** Crée un fichier `.env` :

   ```bash
   ACCESS_KEY=ton_access_key
   SECRET_KEY=ta_secret_key
   S3_BUCKET=nom_de_ton_s3
   ```

4. **Lance l'application :**

   ```bash
   streamlit run app.py
   ```

## 🚀 Utilisation

- Accède à l'application via l'interface Streamlit qui s'ouvrira dans ton navigateur.
- Upload des fichiers (image, vidéo, texte).
- Consulte les résultats d'analyse instantanément.

## 📦 Structure du projet

```
ContentModerator/
├── app.py              # Application Streamlit
├── moderation.py       # Logique de modération avec AWS Rekognition
├── uploads/            # Images / vidéos uploadé
├── .env                # Variables d'environnement
└── requirements.txt    # Dépendances Python
```

## 🔐 Prérequis AWS

- Un compte AWS actif
- Service AWS Rekognition activé
- Clés d'API configurées dans le fichier `.env`
- Configurer le S3 Bucket (region : us-est-1)
   Dans l'onglet "Autorisations"
   - Débloquer les accées public
   - Ajouter le code dans "Stratégie de compartiment"
```
      {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::contentmoderator-sdv-2025/*"
        }
    ]
}
```

## 🤝 Contribuer

1. Fork le projet
2. Crée une branche `feature/amélioration`
3. Commit tes changements
4. Push la branche
5. Ouvre une Pull Request

## 📄 Licence

Ce projet est sous licence "pas touche la mouche".
