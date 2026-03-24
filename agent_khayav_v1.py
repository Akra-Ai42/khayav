import os
import json
import requests
from typing import TypedDict, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import uvicorn

# Chargement des variables d'environnement (.env en local, Env Vars sur Render)
load_dotenv()

# --- CONFIGURATION ---
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_API_BASE = os.getenv("TOGETHER_API_BASE", "https://api.together.xyz/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3-70b-chat-hf")
N8N_RESA_URL = os.getenv("N8N_WORKFLOW_2_RESA_URL")

app = FastAPI()

# Configuration CORS pour autoriser les requêtes venant de ton interface web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOGIQUE IA (LANGGRAPH) ---

class AgentState(TypedDict):
    """L'état du cerveau de Khayav : ce qu'il sait et ce qu'il doit encore demander."""
    message_client: str
    nom: Optional[str]
    date: Optional[str]
    heure: Optional[str]
    couverts: Optional[int]
    reponse_ia: str
    status: str # "ASKING" (en cours), "READY" (complet), "DONE" (transmis à n8n)

# Initialisation du moteur LLM (Llama 3 via Together AI)
llm = ChatOpenAI(
    base_url=TOGETHER_API_BASE,
    api_key=TOGETHER_API_KEY,
    model=MODEL_NAME,
    temperature=0.7
)

def analyze_and_extract(state: AgentState):
    """Analyse le texte du client et extrait les données de réservation."""
    
    prompt = f"""
    Tu es Khayav, l'assistant marseillais du restaurant "La Cantine d'Akram".
    Ton ton : Chaleureux, drôle, utilise des expressions marseillaises (peuchère, dégun, fatche de...).
    
    BUT : Réserver une table. Tu as besoin de : NOM, DATE, HEURE, COUVERTS.
    
    ÉTAT ACTUEL DE LA RÉSERVATION :
    - Nom: {state.get('nom')}
    - Date: {state.get('date')}
    - Heure: {state.get('heure')}
    - Couverts: {state.get('couverts')}
    
    MESSAGE DU CLIENT : "{state['message_client']}"
    
    INSTRUCTIONS :
    1. Extrais les nouvelles informations présentes dans le message.
    2. Si toutes les informations sont présentes, confirme avec enthousiasme.
    3. S'il manque des informations, demande-les poliment mais avec humour.
    
    FORMAT DE SORTIE (JSON UNIQUEMENT) :
    {{
      "nom": "nom ou null",
      "date": "date ISO ou null",
      "heure": "HH:MM ou null",
      "couverts": int ou null,
      "reponse": "Ton texte marseillais ici",
      "status": "READY" (si complet) ou "ASKING"
    }}
    """
    
    ai_msg = llm.invoke(prompt)
    try:
        # Nettoyage pour s'assurer de ne parser que le JSON
        content = ai_msg.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        
        data = json.loads(content)
        
        # Mise à jour de l'état (on conserve l'ancienne valeur si la nouvelle est nulle)
        return {
            **state,
            "nom": data.get("nom") or state.get("nom"),
            "date": data.get("date") or state.get("date"),
            "heure": data.get("heure") or state.get("heure"),
            "couverts": data.get("couverts") or state.get("couverts"),
            "reponse_ia": data.get("reponse"),
            "status": data.get("status")
        }
    except Exception as e:
        return {**state, "reponse_ia": "Oh peuchère, j'ai eu un petit trou de mémoire. Tu peux répéter ?", "status": "ASKING"}

def trigger_booking(state: AgentState):
    """Envoie l'ordre de réservation final au workflow n8n (Le Maître d'Hôtel)."""
    if state["status"] == "READY" and N8N_RESA_URL:
        payload = {
            "nom": state["nom"],
            "date": state["date"],
            "heure": state["heure"],
            "couverts": state["couverts"]
        }
        try:
            # Appel asynchrone vers n8n
            requests.post(N8N_RESA_URL, json=payload, timeout=5)
            return {**state, "status": "DONE", "reponse_ia": state["reponse_ia"] + " ✅ C'est dans la boîte, ton agenda est mis à jour !"}
        except Exception:
            return {**state, "reponse_ia": "Le serveur de réservation fait la sieste... On réessaye dans une minute ?"}
    return state

# --- CONSTRUCTION DU GRAPHE DE DÉCISION (LANGGRAPH) ---
builder = StateGraph(AgentState)
builder.add_node("brain", analyze_and_extract)
builder.add_node("n8n_action", trigger_booking)
builder.set_entry_point("brain")

# On définit le chemin : Si c'est prêt, on va vers n8n, sinon on s'arrête là
builder.add_conditional_edges(
    "brain",
    lambda x: x["status"],
    {"READY": "n8n_action", "ASKING": END, "DONE": END}
)
builder.add_edge("n8n_action", END)
agent_khayav = builder.compile()

# --- ROUTES API ---

@app.get("/health")
def health():
    """Route de vérification pour Render."""
    return {"status": "Khayav is alive and kicking 🚀", "pôle": "Usine IA"}

@app.post("/api/khayav/chat")
async def chat(request: Request):
    """Endpoint principal utilisé par le Frontend."""
    data = await request.json()
    user_msg = data.get("message")
    
    # Préparation de l'état initial avec le contexte envoyé par le front
    initial_state = {
        "message_client": user_msg,
        "nom": data.get("nom"),
        "date": data.get("date"),
        "heure": data.get("heure"),
        "couverts": data.get("couverts"),
        "status": "ASKING",
        "reponse_ia": ""
    }
    
    # Exécution du cerveau
    final_result = agent_khayav.invoke(initial_state)
    
    return {
        "reponse": final_result["reponse_ia"],
        "nom": final_result["nom"],
        "date": final_result["date"],
        "heure": final_result["heure"],
        "couverts": final_result["couverts"]
    }

# --- SERVICE DES FICHIERS STATIQUES ---
# FastAPI va servir l'interface (index.html, app.js) située dans le dossier /static
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except Exception:
    print("⚠️ Attention : Le dossier 'static' est introuvable. L'API fonctionnera, mais pas l'interface web.")

if __name__ == "__main__":
    # Lancement du serveur (Port 8000 par défaut)
    uvicorn.run(app, host="0.0.0.0", port=8000)