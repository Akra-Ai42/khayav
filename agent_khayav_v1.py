import os
import json
import requests
from typing import TypedDict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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
    except:
        return {**state, "reponse_ia": "Peuchère, j'ai eu un bug ! Répète ?", "status": "ASKING"}

def trigger_booking(state: AgentState):
    if state["status"] == "READY" and N8N_RESA_URL:
        payload = {"nom": state["nom"], "date": state["date"], "heure": state["heure"], "couverts": state["couverts"]}
        try:
            requests.post(N8N_RESA_URL, json=payload, timeout=5)
            return {**state, "status": "DONE", "reponse_ia": state["reponse_ia"] + " ✅ C'est validé dans l'agenda !"}
        except:
            return {**state, "reponse_ia": "Le serveur de résa fait la sieste..."}
    return state

builder = StateGraph(AgentState)
builder.add_node("brain", analyze_and_extract)
builder.add_node("n8n_action", trigger_booking)
builder.set_entry_point("brain")
builder.add_conditional_edges("brain", lambda x: x["status"], {"READY": "n8n_action", "ASKING": END, "DONE": END})
builder.add_edge("n8n_action", END)
agent_khayav = builder.compile()

# --- ROUTES API & FRONTEND ---

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Cette route sert l'interface React directement avec des URLs propres."""
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agent Khayav POC</title>
        <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
        <script src="[https://unpkg.com/lucide@latest](https://unpkg.com/lucide@latest)"></script>
        <script src="[https://unpkg.com/react@18/umd/react.production.min.js](https://unpkg.com/react@18/umd/react.production.min.js)"></script>
        <script src="[https://unpkg.com/react-dom@18/umd/react-dom.production.min.js](https://unpkg.com/react-dom@18/umd/react-dom.production.min.js)"></script>
        <script src="[https://unpkg.com/@babel/standalone/babel.min.js](https://unpkg.com/@babel/standalone/babel.min.js)"></script>
        <style>
            .no-scrollbar::-webkit-scrollbar { display: none; }
            @keyframes slide-in { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
            .animate-in { animation: slide-in 0.5s ease-out; }
        </style>
    </head>
    <body class="bg-[#020617]">
        <div id="root"></div>
        <script type="text/babel">
            const { useState, useEffect, useRef } = React;
            const { Send, UtensilsCrossed, Sparkles, MapPin, Calendar, Users, Clock, RefreshCcw, Info, CheckCheck, Smile } = lucide;

            const App = () => {
                const [messages, setMessages] = useState([{ id: 1, text: "Salut l'ami ! Bienvenue à La Cantine d'Akram. 🌊\\n\\nJe suis Khayav, ton assistant marseillais. Tu veux réserver ?", sender: 'bot', time: 'Maintenant' }]);
                const [inputValue, setInputValue] = useState('');
                const [isTyping, setIsTyping] = useState(false);
                const [sessionData, setSessionData] = useState({ nom: null, date: null, heure: null, couverts: null });
                const messagesEndRef = useRef(null);

                useEffect(() => {
                    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
                    if (window.lucide) lucide.createIcons();
                }, [messages, isTyping]);

                const sendMessage = async (e) => {
                    e.preventDefault();
                    if (!inputValue.trim()) return;
                    const userText = inputValue;
                    setMessages(prev => [...prev, { id: Date.now(), text: userText, sender: 'user', time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }]);
                    setInputValue('');
                    setIsTyping(true);

                    try {
                        const res = await fetch('/api/khayav/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ message: userText, ...sessionData })
                        });
                        const data = await res.json();
                        setSessionData({ nom: data.nom, date: data.date, heure: data.heure, couverts: data.couverts });
                        setMessages(prev => [...prev, { id: Date.now(), text: data.reponse, sender: 'bot', time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }]);
                    } catch (err) {
                        setMessages(prev => [...prev, { id: Date.now(), text: "⚠️ Le cerveau est en pause café.", sender: 'bot', time: 'Erreur' }]);
                    } finally { setIsTyping(false); }
                };

                return (
                    <div className="flex items-center justify-center min-h-screen p-0 sm:p-4 font-sans text-slate-100">
                        <div className="relative w-full max-w-md h-[100vh] sm:h-[800px] bg-[#0b141a] sm:rounded-[3rem] shadow-2xl overflow-hidden border-0 sm:border-[8px] border-slate-900 flex flex-col">
                            <header className="pt-12 pb-5 px-6 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 shadow-xl z-10">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center border border-white/20"><i data-lucide="utensils-crossed" className="text-white"></i></div>
                                        <div><h1 className="font-bold text-lg leading-none">Agent Khayav <i data-lucide="sparkles" className="inline w-4 text-yellow-300"></i></h1><p className="text-[10px] opacity-80 uppercase tracking-widest mt-1">En ligne • Marseille</p></div>
                                    </div>
                                    <button onClick={() => window.location.reload()} className="p-2 bg-white/10 rounded-full hover:rotate-180 transition-all duration-500"><i data-lucide="refresh-ccw" className="w-4 h-4"></i></button>
                                </div>
                                <div className="mt-4 flex gap-2 overflow-x-auto no-scrollbar">
                                    <span className="bg-white/10 px-3 py-1 rounded-full text-[10px] flex items-center gap-1"><i data-lucide="map-pin" className="w-3"></i>Vieux-Port</span>
                                    {sessionData.date && <span className="bg-green-500/30 px-3 py-1 rounded-full text-[10px] flex items-center gap-1 animate-in"><i data-lucide="calendar" className="w-3"></i>{sessionData.date}</span>}
                                    {sessionData.heure && <span className="bg-blue-500/30 px-3 py-1 rounded-full text-[10px] flex items-center gap-1 animate-in"><i data-lucide="clock" className="w-3"></i>{sessionData.heure}</span>}
                                    {sessionData.couverts && <span className="bg-orange-500/30 px-3 py-1 rounded-full text-[10px] flex items-center gap-1 animate-in"><i data-lucide="users" className="w-3"></i>{sessionData.couverts} pers</span>}
                                </div>
                            </header>
                            <main className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0b141a]">
                                {messages.map(msg => (
                                    <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-in`}>
                                        <div className={`max-w-[85%] p-3 rounded-2xl shadow-lg ${{msg.sender === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-100 rounded-tl-none border border-white/5'}`}>
                                            <p className="text-sm leading-relaxed">{msg.text}</p>
                                            <div className="flex justify-end gap-1 mt-1 opacity-50 text-[9px] font-bold"><span>{msg.time}</span>{msg.sender === 'user' && <i data-lucide="check-check" className="w-3"></i>}</div>
                                        </div>
                                    </div>
                                ))}
                                {isTyping && <div className="text-indigo-400 text-[10px] animate-pulse font-bold uppercase tracking-widest ml-2">Khayav réfléchit...</div>}
                                <div ref={messagesEndRef} />
                            </main>
                            <footer className="p-4 bg-slate-900 border-t border-white/5">
                                <form onSubmit={sendMessage} className="flex gap-2 bg-[#0b141a] p-1.5 rounded-full border border-white/10">
                                    <input value={inputValue} onChange={e => setInputValue(e.target.value)} type="text" placeholder="Dis-moi tout..." className="flex-1 bg-transparent border-none px-4 py-2 text-sm focus:ring-0 outline-none" />
                                    <button type="submit" className="bg-gradient-to-r from-indigo-500 to-purple-600 p-2.5 rounded-full shadow-lg active:scale-95 transition-transform"><i data-lucide="send" className="w-4 h-4"></i></button>
                                </form>
                            </footer>
                        </div>
                    </div>
                );
            };

            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(<App />);
        </script>
    </body>
    </html>
    """

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)