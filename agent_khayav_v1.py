import os
import json
import requests
from typing import TypedDict, Optional, List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# --- CONFIGURATION ---
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_API_BASE = os.getenv("TOGETHER_API_BASE", "https://api.together.xyz/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3-70b-chat-hf")
N8N_RESA_URL = os.getenv("N8N_WORKFLOW_2_RESA_URL")

app = FastAPI()

# Configuration CORS pour que ton Front-end puisse appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOGIQUE IA (LANGGRAPH) ---

class AgentState(TypedDict):
    message_client: str
    nom: Optional[str]
    date: Optional[str]
    heure: Optional[str]
    couverts: Optional[int]
    reponse_ia: str
    status: str # "ASKING" | "READY" | "DONE"

# Initialisation du LLM via Together AI (compatible OpenAI SDK)
llm = ChatOpenAI(
    base_url=TOGETHER_API_BASE,
    api_key=TOGETHER_API_KEY,
    model=MODEL_NAME,
    temperature=0.7
)

def analyze_and_extract(state: AgentState):
    """Analyse le message et extrait les entités au format JSON."""
    
    prompt = f"""
    Tu es Khayav, l'assistant marseillais du restaurant "La Cantine d'Akram".
    Ton ton : Chaleureux, drôle, utilise des expressions marseillaises (peuchère, dégun, etc.).
    
    BUT : Réserver une table. Tu as besoin de : NOM, DATE, HEURE, COUVERTS.
    
    ÉTAT ACTUEL :
    - Nom: {state.get('nom')}
    - Date: {state.get('date')}
    - Heure: {state.get('heure')}
    - Couverts: {state.get('couverts')}
    
    MESSAGE CLIENT : "{state['message_client']}"
    
    RÉPONS :
    1. Extrais les nouvelles infos si présentes.
    2. Si tout est complet, confirme avec joie.
    3. S'il manque des infos, demande-les avec humour.
    
    FORMAT DE SORTIE OBLIGATOIRE (JSON uniquement) :
    {{
      "nom": "nom ou null",
      "date": "date ISO ou null",
      "heure": "HH:MM ou null",
      "couverts": int ou null,
      "reponse": "Ton texte marseillais",
      "status": "READY" (si tout est là) ou "ASKING"
    }}
    """
    
    ai_msg = llm.invoke(prompt)
    try:
        # Nettoyage de la réponse pour ne garder que le JSON
        raw_content = ai_msg.content.strip()
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0]
        
        data = json.loads(raw_content)
        
        # Mise à jour de l'état (on garde l'ancienne info si la nouvelle est nulle)
        return {
            **state,
            "nom": data.get("nom") or state.get("nom"),
            "date": data.get("date") or state.get("date"),
            "heure": data.get("heure") or state.get("heure"),
            "couverts": data.get("couverts") or state.get("couverts"),
            "reponse_ia": data.get("reponse"),
            "status": data.get("status")
        }
    except:
        return {**state, "reponse_ia": "Oh peuchère, mon cerveau a chauffé au soleil ! Tu peux répéter ?", "status": "ASKING"}

def trigger_booking(state: AgentState):
    """Envoie la réservation à n8n si le status est READY."""
    if state["status"] == "READY" and N8N_RESA_URL:
        payload = {
            "nom": state["nom"],
            "date": state["date"],
            "heure": state["heure"],
            "couverts": state["couverts"]
        }
        try:
            requests.post(N8N_RESA_URL, json=payload, timeout=5)
            return {**state, "status": "DONE", "reponse_ia": state["reponse_ia"] + " ✅ C'est validé dans l'agenda, à très vite !"}
        except:
            return {**state, "reponse_ia": "Le serveur de réservation fait la sieste... réessaye dans 2 minutes !"}
    return state

# Construction du Graphe
builder = StateGraph(AgentState)
builder.add_node("brain", analyze_and_extract)
builder.add_node("n8n_action", trigger_booking)
builder.set_entry_point("brain")

builder.add_conditional_edges(
    "brain",
    lambda x: x["status"],
    {"READY": "n8n_action", "ASKING": END}
)
builder.add_edge("n8n_action", END)
agent_khayav = builder.compile()

# --- ROUTES API ---

@app.get("/")
def health():
    return {"status": "Khayav is alive and kicking 🚀", "pôle": "Usine IA"}

@app.post("/api/khayav/chat")
async def chat(request: Request):
    data = await request.json()
    user_msg = data.get("message")
    
    # Récupération du contexte précédent (optionnel via n8n ou local)
    initial_state = {
        "message_client": user_msg,
        "nom": data.get("nom"),
        "date": data.get("date"),
        "heure": data.get("heure"),
        "couverts": data.get("couverts"),
        "status": "ASKING",
        "reponse_ia": ""
    }
    
    final_result = agent_khayav.invoke(initial_state)
    
    return {
        "reponse": final_result["reponse_ia"],
        "nom": final_result["nom"],
        "date": final_result["date"],
        "heure": final_result["heure"],
        "couverts": final_result["couverts"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)