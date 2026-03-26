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

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOGIQUE IA (Gardée à l'identique) ---
# ... (Tes classes AgentState, llm, analyze_and_extract, trigger_booking ici) ...

# --- ROUTES API (Placées AVANT le statique) ---

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
    # Simulation ou appel langgraph
    # final_result = agent_khayav.invoke(initial_state) 
    # Pour le debug, on renvoie une structure propre :
    return {
        "reponse": "Ah l'ami ! Je t'écoute.", # Remplace par ton invoke
        "nom": data.get("nom"),
        "date": data.get("date"),
        "heure": data.get("heure"),
        "couverts": data.get("couverts")
    }

# --- MONTAGE DU DOSSIER STATIQUE (DERNIÈRE POSITION) ---
# L'option html=True fait que "/" servira automatiquement "index.html"
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    # Render utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)