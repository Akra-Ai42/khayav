# Utilisation d'une image Python légère
FROM python:3.11-slim

# Définition du dossier de travail
WORKDIR /app

# Installation des dépendances système nécessaires (si besoin de compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie du fichier des dépendances
COPY requirements.txt .

# Installation des bibliothèques Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie de tout le code source dans le conteneur
COPY . .

# Exposition du port utilisé par FastAPI
EXPOSE 8000

# Commande de lancement du serveur Uvicorn
# Note : "agent_khayav_v1" doit correspondre au nom de ton fichier .py
# et "app" au nom de l'instance FastAPI dans ton code.
CMD ["uvicorn", "agent_khayav_v1:app", "--host", "0.0.0.0", "--port", "8000"]