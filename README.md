🥗 Khayav - L'Agent IA pour Restaurants

"L'IA au service du local : de la discussion WhatsApp à la réservation réelle."

Khayav est un agent intelligent conçu pour automatiser la relation client des restaurants de proximité. Contrairement à un simple chatbot, Khayav est un Agent Agentique : il ne se contente pas de parler, il agit.

🚀 Architecture du Projet

Le projet repose sur une architecture hybride Code (Python/LangGraph) et No-Code (n8n) pour maximiser la flexibilité et la rapidité de déploiement.

1. Le Cerveau (Core IA)

Hébergé sur Render via FastAPI et Docker, il utilise :

LangGraph : Pour la gestion de l'état (State) et la logique de décision.

Llama 3 (via Together AI) : Pour l'extraction de données et la génération de réponses avec un ton local.

2. Les Muscles (Automatisation)

Piloté par n8n avec deux workflows distincts :

Workflow Standardiste : Gère le flux WhatsApp (Meta API) et communique avec le cerveau Python.

Workflow Maître d'Hôtel : Reçoit les ordres de réservation via Webhook et met à jour Google Calendar.

🛠️ Stack Technique

Langage : Python 3.11

Framework Web : FastAPI & Uvicorn

Orchestration IA : LangGraph / LangChain

Automatisation : n8n

Infrastructure : Docker / Render

Interfaces : WhatsApp Cloud API / Google Calendar API

📁 Structure du Dépôt

agent_khayav_v1.py : Script principal contenant la logique du graphe et les endpoints API.

Dockerfile : Configuration pour le déploiement conteneurisé sur Render.

requirements.txt : Liste des dépendances Python.

.env : (Non inclus dans Git) Contient les clés d'API secrètes.

💡 Vision : Le Choix de l'Architecte

Ce projet s'inscrit dans la vision du Club Usine IA. Nous croyons que l'IA ne doit pas être une technologie froide servant à spammer le monde, mais un outil puissant pour soutenir nos commerces et écouter nos détresses.

"Au Club Usine IA, nous avons fait notre choix. Nous construisons des agents qui réparent le monde."

📞 Contact

Développé par Akram, Founder de l'Usine IA.
