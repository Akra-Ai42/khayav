import os
import json
import requests
import uvicorn
from typing import TypedDict, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_API_BASE = os.getenv("TOGETHER_API_BASE", "[https://api.together.xyz/v1](https://api.together.xyz/v1)")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3-70b-chat-hf")
N8N_RESA_URL = os.getenv("N8N_WORKFLOW_2_RESA_URL")

app = FastAPI()

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
    Ton ton : Chaleureux, drôle, utilise des expressions marseillaises (peuchère, fada, dégun).
    BUT : Aider le client et extraire les infos de réservation : NOM, DATE, HEURE, COUVERTS.
    ÉTAT ACTUEL : {state}
    MESSAGE CLIENT : "{state['message_client']}"
    
    FORMAT DE SORTIE OBLIGATOIRE (JSON uniquement) :
    {{
      "nom": "nom ou null",
      "date": "date ou null",
      "heure": "HH:MM ou null",
      "couverts": int ou null,
      "reponse": "Ton texte marseillais ici",
      "status": "READY" (si on a les 4 infos) ou "ASKING"
    }}
    """
    try:
        ai_msg = llm.invoke(prompt)
        raw_content = ai_msg.content.strip()
        
        # Nettoyage si l'IA entoure le JSON de ```json ... ```
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
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
    except Exception as e:
        print(f"Erreur d'extraction : {e}")
        return {**state, "reponse_ia": "Oh fada, mon cerveau a chauffé au soleil ! Tu peux répéter ?", "status": "ASKING"}

def trigger_booking(state: AgentState):
    if state["status"] == "READY" and N8N_RESA_URL:
        payload = {"nom": state["nom"], "date": state["date"], "heure": state["heure"], "couverts": state["couverts"]}
        try:
            requests.post(N8N_RESA_URL, json=payload, timeout=5)
            return {**state, "status": "DONE", "reponse_ia": state["reponse_ia"] + " ✅ C'est validé dans l'agenda, l'ami !"}
        except Exception:
            return {**state, "reponse_ia": state["reponse_ia"] + " (Petit souci technique pour enregistrer, mais je retiens ta table !)"}
    return state

# Construction du Graphe
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
    initial_state = {
        "message_client": data.get("message"),
        "nom": data.get("nom"),
        "date": data.get("date"),
        "heure": data.get("heure"),
        "couverts": data.get("couverts"),
        "status": "ASKING",
        "reponse_ia": ""
    }
    
    # ON APPELLE ENFIN LE VRAI AGENT !
    final_result = agent_khayav.invoke(initial_state)
    
    return {
        "reponse": final_result["reponse_ia"],
        "nom": final_result["nom"],
        "date": final_result["date"],
        "heure": final_result["heure"],
        "couverts": final_result["couverts"]
    }

# --- MONTAGE STATIQUE ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)