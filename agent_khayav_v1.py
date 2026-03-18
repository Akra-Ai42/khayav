# agent_khayav_v1.py
# ==============================================================================
# USINE IA - AGENT RESTAURANT "KHAYAV" v1.0
# Développé pour Akram (Founder)
# ==============================================================================

import os
import json
import requests
from typing import TypedDict, Optional, List
from fastapi import FastAPI, Request
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- CONFIGURATION (À adapter avec tes futures URLs n8n) ---
N8N_WORKFLOW_2_RESA_URL = "https://n8n.ton-domaine.com/webhook/booking-khayav"
N8N_WORKFLOW_ESCALADE_URL = "https://n8n.ton-domaine.com/webhook/escalade-patron"

# --- BASE DE CONNAISSANCES (JSON Statique) ---
RESTO_INFO = {
    "nom": "La Cantine d'Akram",
    "specialites": ["Pizza Truffe (la légende)", "Pâtes Carbonara (les vraies)", "Tiramisu Maison"],
    "options": ["Vegan (Salade Italienne)", "Sans Gluten (Risotto)"],
    "horaires": "Tous les jours de 19h00 à 23h30",
    "lieu": "Marseille, Vieux-Port",
    "humour": "Toujours une blague sur la faim en début de conversation."
}

# --- DÉFINITION DE L'ÉTAT (Le State) ---
class AgentState(TypedDict):
    messages: List[dict]
    nom: Optional[str]
    date: Optional[str]
    heure: Optional[str]
    couverts: Optional[int]
    intent: str # "INFO" | "BOOKING" | "CANCEL" | "DELAY" | "COMPLEX"
    reponse_ia: str

# --- INITIALISATION DU LLM (Together AI ou OpenAI) ---
# Note : Together AI est compatible avec l'objet ChatOpenAI
llm = ChatOpenAI(
    model="meta-llama/Llama-3-70b-chat-hf", 
    openai_api_base="https://api.together.xyz/v1",
    openai_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0.7
)

# --- NŒUD 1 : ANALYSE & EXTRACTION ---
def analyzer_node(state: AgentState):
    last_user_message = state["messages"][-1]["content"]
    
    # Prompt de classification et d'extraction
    system_instruction = f"""
    Tu es le cerveau d'extraction de Khayav.
    Voici les infos du resto : {json.dumps(RESTO_INFO)}
    
    Ton job :
    1. Identifie l'intention : "BOOKING" (réserver), "CANCEL" (annuler/modifier), "DELAY" (retard), "INFO" (question simple), "COMPLEX" (demande hors norme).
    2. Extrais les entités : nom, date, heure, couverts.
    3. Garde les valeurs déjà connues dans le State : Nom={state['nom']}, Date={state['date']}, Heure={state['heure']}, Couverts={state['couverts']}.
    
    Réponds UNIQUEMENT au format JSON strict :
    {{
        "intent": "...",
        "nom": "...",
        "date": "...",
        "heure": "...",
        "couverts": int ou null
    }}
    """
    
    response = llm.invoke([
        SystemMessage(content=system_instruction),
        HumanMessage(content=last_user_message)
    ])
    
    try:
        data = json.loads(response.content)
        state.update(data)
    except:
        state["intent"] = "INFO" # Fallback
        
    return state

# --- NŒUD 2 : GÉNÉRATION DE LA RÉPONSE ---
def responder_node(state: AgentState):
    intent = state["intent"]
    
    # Construction du message de l'IA selon l'intention
    prompt = f"""
    Tu es Khayav, l'agent IA du restaurant. Ton ton est amical, un peu chambreur (humour marseillais léger), et efficace.
    
    CONTEXTE :
    - Menu/Infos : {json.dumps(RESTO_INFO)}
    - Intention détectée : {intent}
    - Données collectées : Nom={state['nom']}, Date={state['date']}, Heure={state['heure']}, Pers={state['couverts']}
    
    CONSIGNES :
    - Si intention "BOOKING" et manque des infos : demande-les avec humour.
    - Si intention "BOOKING" et TOUT est là : confirme que tu lances la résa.
    - Si intention "CANCEL" : dis que tu t'en occupes (ceci sera géré par n8n).
    - Si intention "DELAY" : rassure le client.
    - Si intention "COMPLEX" : dis que tu passes le relais au patron (le VIP service).
    
    Règle : Maximum 3 phrases.
    """
    
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=state["messages"][-1]["content"])
    ])
    
    state["reponse_ia"] = response.content
    return state

# --- NŒUD 3 : DÉCLENCHEUR N8N (Workflow 2) ---
def trigger_action_node(state: AgentState):
    # C'est ici qu'on fait le lien avec tes "muscles" n8n
    
    intent = state["intent"]
    
    # CAS A : Réservation complète
    if intent == "BOOKING" and state["nom"] and state["date"] and state["heure"] and state["couverts"]:
        payload = {
            "action": "CREATE_BOOKING",
            "nom": state["nom"],
            "date": state["date"],
            "heure": state["heure"],
            "couverts": state["couverts"]
        }
        requests.post(N8N_WORKFLOW_2_RESA_URL, json=payload)
        print("🚀 Signal de réservation envoyé à n8n")

    # CAS B : Escalade (Demande complexe)
    elif intent == "COMPLEX":
        payload = {
            "action": "HUMAN_ESCALATION",
            "message": state["messages"][-1]["content"]
        }
        requests.post(N8N_WORKFLOW_ESCALADE_URL, json=payload)
        print("⚠️ Signal d'escalade envoyé au patron via n8n")
        
    return state

# --- CONSTRUCTION DU GRAPHE LANGGRAPH ---
builder = StateGraph(AgentState)

builder.add_node("analyzer", analyzer_node)
builder.add_node("responder", responder_node)
builder.add_node("trigger", trigger_action_node)

builder.set_entry_point("analyzer")
builder.add_edge("analyzer", "responder")
builder.add_edge("responder", "trigger")
builder.add_edge("trigger", END)

brain_khayav = builder.compile()

# --- ROUTES FASTAPI (La Porte pour n8n Workflow 1) ---

@app.post("/api/khayav/chat")
async def chat(request: Request):
    data = await request.json()
    
    # On récupère les infos envoyées par n8n (persistance de l'état)
    # n8n doit renvoyer les données extraites à chaque tour dans le body
    input_state = {
        "messages": [{"role": "user", "content": data.get("message")}],
        "nom": data.get("nom"),
        "date": data.get("date"),
        "heure": data.get("heure"),
        "couverts": data.get("couverts"),
        "intent": "INFO",
        "reponse_ia": ""
    }
    
    # Exécution du cerveau
    output_state = brain_khayav.invoke(input_state)
    
    # On renvoie la réponse et les variables à n8n pour qu'il les garde en mémoire
    return {
        "reponse": output_state["reponse_ia"],
        "nom": output_state["nom"],
        "date": output_state["date"],
        "heure": output_state["heure"],
        "couverts": output_state["couverts"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)