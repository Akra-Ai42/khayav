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

# Chargement des variables d'environnement
load_dotenv()

# --- CONFIGURATION ---
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_API_BASE = os.getenv("TOGETHER_API_BASE", "https://api.together.xyz/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3-70b-chat-hf")
N8N_RESA_URL = os.getenv("N8N_WORKFLOW_2_RESA_URL")

app = FastAPI()

# Configuration CORS pour autoriser le Frontend à parler au Backend
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
    status: str 

llm = ChatOpenAI(
    base_url=TOGETHER_API_BASE,
    api_key=TOGETHER_API_KEY,
    model=MODEL_NAME,
    temperature=0.7
)

def analyze_and_extract(state: AgentState):
    prompt = f"""
    Tu es Khayav, l'assistant marseillais du restaurant "La Cantine d'Akram".
    Ton ton : Chaleureux, drôle, utilise des expressions marseillaises.
    BUT : Réserver une table. Tu as besoin de : NOM, DATE, HEURE, COUVERTS.
    ÉTAT ACTUEL : {state}
    MESSAGE CLIENT : "{state['message_client']}"
    FORMAT DE SORTIE OBLIGATOIRE (JSON uniquement) :
    {{
      "nom": "nom ou null",
      "date": "date ou null",
      "heure": "HH:MM ou null",
      "couverts": int ou null,
      "reponse": "Ton texte marseillais",
      "status": "READY" (si tout est complet) ou "ASKING"
    }}
    """
    ai_msg = llm.invoke(prompt)
    try:
        raw_content = ai_msg.content.strip()
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0]
        data = json.loads(raw_content)
        return {
            **state,
            "nom": data.get("nom") or state.get("nom"),
            "date": data.get("date") or state.get("date"),
            "heure": data.get("heure") or state.get("heure"),
            "couverts": data.get("couverts") or state.get("couverts"),
            "reponse_ia": data.get("reponse"),
            "status": data.get("status")
        }
    except Exception:
        return {**state, "reponse_ia": "Peuchère, j'ai eu un bug ! Répète ?", "status": "ASKING"}

def trigger_booking(state: AgentState):
    if state["status"] == "READY" and N8N_RESA_URL:
        payload = {"nom": state["nom"], "date": state["date"], "heure": state["heure"], "couverts": state["couverts"]}
        try:
            requests.post(N8N_RESA_URL, json=payload, timeout=5)
            return {**state, "status": "DONE", "reponse_ia": state["reponse_ia"] + " ✅ C'est validé dans l'agenda !"}
        except Exception:
            return {**state, "reponse_ia": "Le serveur de résa fait la sieste..."}
    return state

builder = StateGraph(AgentState)
builder.add_node("brain", analyze_and_extract)
builder.add_node("n8n_action", trigger_booking)
builder.set_entry_point("brain")
builder.add_conditional_edges("brain", lambda x: x["status"], {"READY": "n8n_action", "ASKING": END, "DONE": END})
builder.add_edge("n8n_action", END)
agent_khayav = builder.compile()

# --- ROUTES API ---

@app.post("/api/khayav/chat")
async def chat(request: Request):
    data = await request.json()
    user_msg = data.get("message")
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

# --- MONTAGE DU DOSSIER STATIQUE ---
# Important : les fichiers index.html et app.js doivent être dans un dossier 'static'
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)