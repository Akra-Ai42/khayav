import React, { useState, useEffect, useRef } from 'react';
import { Send, Phone, MoreVertical, CheckCheck, Smile, UtensilsCrossed, Sparkles, MapPin, Calendar, Users, Clock, RefreshCcw, Info } from 'lucide-react';

/**
 * POC FRONTEND AGENT KHAYAV - VERSION FINALE (MARSEILLE SUNSET)
 * Design : Glassmorphism & Badges d'extraction dynamiques.
 * Backend : Connecté à l'API Render de Khayav (https://khayav-agent.onrender.com/api/khayav/chat).
 */

const App = () => {
  // --- ÉTAT DE LA CONVERSATION ---
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: "Salut l'ami ! Bienvenue à La Cantine d'Akram. 🌊\n\nJe suis Khayav, ton assistant marseillais qui a du peps. Une petite table au soleil ou tu veux voir la carte ?", 
      sender: 'bot', 
      time: 'Maintenant' 
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // --- DONNÉES EXTRAITES PAR L'IA ---
  const [sessionData, setSessionData] = useState({ 
    nom: null, 
    date: null, 
    heure: null, 
    couverts: null 
  });
  
  const messagesEndRef = useRef(null);

  // Scroll automatique à chaque nouveau message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Réinitialisation de la session pour la démo
  const resetSession = () => {
    if(window.confirm("Voulez-vous recommencer la réservation de zéro ?")) {
        setMessages([{ 
            id: Date.now(), 
            text: "C'est reparti ! On efface tout. Comment puis-je t'aider à nouveau ?", 
            sender: 'bot', 
            time: 'Maintenant' 
        }]);
        setSessionData({ nom: null, date: null, heure: null, couverts: null });
    }
  };

  // Appel au cerveau Python sur Render
  const sendMessageToRender = async (userText) => {
    setIsTyping(true);
    try {
      // IMPORTANT : Remplace par ton URL Render si elle change
      const response = await fetch('https://khayav-agent.onrender.com/api/khayav/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            message: userText, 
            ...sessionData // Envoi du contexte actuel pour maintenir la mémoire
        })
      });

      if (!response.ok) throw new Error("Erreur serveur");

      const data = await response.json();
      
      // Mise à jour des badges visuels en haut de l'écran
      setSessionData({
        nom: data.nom,
        date: data.date,
        heure: data.heure,
        couverts: data.couverts
      });

      setMessages(prev => [...prev, {
        id: Date.now(),
        text: data.reponse || "Désolé, j'ai eu un petit bug marseillais...",
        sender: 'bot',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: "⚠️ Oh peuchère, j'ai perdu le fil... Vérifie que mon cerveau sur Render est bien réveillé et en ligne !",
        sender: 'bot',
        time: 'Erreur'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMsg = {
      id: Date.now(),
      text: inputValue,
      sender: 'user',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    const textToSend = inputValue;
    setInputValue('');
    sendMessageToRender(textToSend);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#020617] p-0 sm:p-4 font-sans text-slate-100 selection:bg-indigo-500/30">
      
      {/* CONTENEUR SIMULATION MOBILE IPHONE STYLE */}
      <div className="relative w-full max-w-md h-[100vh] sm:h-[850px] bg-[#0b141a] sm:rounded-[3rem] shadow-[0_0_80px_rgba(79,70,229,0.3)] overflow-hidden border-0 sm:border-[10px] border-slate-900 flex flex-col transition-all duration-500">
        
        {/* ENCOCHE IPHONE (Visible uniquement sur desktop) */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-slate-900 rounded-b-2xl z-50 hidden sm:block shadow-md"></div>

        {/* EN-TÊTE PREMIUM DYNAMIQUE */}
        <header className="pt-12 pb-5 px-6 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 shadow-2xl z-10 relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative group">
                <div className="w-14 h-14 bg-white/10 backdrop-blur-xl rounded-2xl flex items-center justify-center border border-white/20 shadow-inner group-hover:scale-105 transition-transform">
                  <UtensilsCrossed size={28} className="text-white drop-shadow-md" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 border-2 border-slate-900 rounded-full animate-pulse shadow-sm"></div>
              </div>
              <div>
                <h1 className="font-black text-xl tracking-tight flex items-center gap-2 drop-shadow-sm">
                  Agent Khayav <Sparkles size={18} className="text-yellow-300 animate-pulse" />
                </h1>
                <div className="flex items-center gap-1.5 opacity-90">
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    <p className="text-[10px] font-bold text-indigo-100 uppercase tracking-widest">
                        Serveur Live • Marseille
                    </p>
                </div>
              </div>
            </div>
            <button 
                onClick={resetSession}
                className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-all active:scale-90"
                title="Réinitialiser la discussion"
            >
                <RefreshCcw size={18} className="text-white/80" />
            </button>
          </div>
          
          {/* BADGES D'EXTRACTION (Données en temps réel) */}
          <div className="mt-5 flex gap-2 overflow-x-auto no-scrollbar pb-1">
             <span className="bg-white/10 backdrop-blur-md border border-white/20 px-3 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap flex items-center gap-1.5 shadow-sm">
               <MapPin size={12} className="text-pink-300" /> Vieux-Port
             </span>
             
             {sessionData.date && (
               <div className="animate-in zoom-in duration-300">
                <span className="bg-green-500/30 backdrop-blur-md border border-green-400/50 px-3 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap flex items-center gap-1.5 text-green-100 shadow-lg shadow-green-500/20">
                    <Calendar size={12} /> {sessionData.date}
                </span>
               </div>
             )}
             
             {sessionData.heure && (
               <div className="animate-in zoom-in duration-300 delay-75">
                <span className="bg-blue-500/30 backdrop-blur-md border border-blue-400/50 px-3 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap flex items-center gap-1.5 text-blue-100 shadow-lg shadow-blue-500/20">
                    <Clock size={12} /> {sessionData.heure}
                </span>
               </div>
             )}
             
             {sessionData.couverts && (
               <div className="animate-in zoom-in duration-300 delay-150">
                <span className="bg-orange-500/30 backdrop-blur-md border border-orange-400/50 px-3 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap flex items-center gap-1.5 text-orange-100 shadow-lg shadow-orange-500/20">
                    <Users size={12} /> {sessionData.couverts} pers
                </span>
               </div>
             )}
          </div>
        </header>

        {/* ZONE DE MESSAGERIE STYLE WHATSAPP DARK */}
        <main className="flex-1 overflow-y-auto p-4 space-y-6 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] bg-[#0b141a]">
          
          <div className="text-center opacity-30 py-4 border-b border-white/5 mb-4">
            <p className="text-[9px] font-mono tracking-tighter uppercase flex items-center justify-center gap-2">
                <Info size={10} /> Canal chiffré par l'Usine IA Club
            </p>
          </div>

          {messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-3 duration-500`}
            >
              <div 
                className={`max-w-[85%] p-4 rounded-[1.8rem] relative shadow-2xl transition-all ${
                  msg.sender === 'user' 
                    ? 'bg-gradient-to-br from-indigo-500 to-indigo-700 text-white rounded-tr-none' 
                    : 'bg-[#1e293b]/80 backdrop-blur-md text-slate-100 border border-white/10 rounded-tl-none shadow-indigo-500/5'
                }`}
              >
                <p className="text-[14.5px] leading-relaxed whitespace-pre-wrap font-medium">{msg.text}</p>
                <div className={`flex items-center justify-end gap-1.5 mt-2.5 ${msg.sender === 'user' ? 'text-indigo-200' : 'text-slate-500'}`}>
                  <span className="text-[9px] font-black uppercase tracking-widest">{msg.time}</span>
                  {msg.sender === 'user' && <CheckCheck size={14} className="text-indigo-300" />}
                </div>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex justify-start animate-pulse">
              <div className="bg-[#1e293b]/60 px-6 py-5 rounded-[1.8rem] rounded-tl-none border border-white/5 shadow-inner">
                <div className="flex gap-2">
                  <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                  <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </main>

        {/* ZONE DE SAISIE MODERNE */}
        <footer className="p-5 bg-slate-900/80 backdrop-blur-xl border-t border-white/5 pb-8 sm:pb-12">
          <div className="flex items-center gap-3 bg-[#0b141a]/80 p-2 rounded-[2.5rem] shadow-inner border border-white/10 focus-within:ring-2 focus-within:ring-indigo-500/50 transition-all duration-300 group">
            <button className="p-3 text-slate-500 hover:text-indigo-400 transition-colors group-focus-within:text-indigo-400">
              <Smile size={26} />
            </button>
            
            <form onSubmit={handleSend} className="flex-1 text-white">
              <input 
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Dis-moi tout..."
                className="w-full bg-transparent border-none focus:ring-0 text-[15.5px] placeholder-slate-600 py-2.5"
              />
            </form>

            <button 
              onClick={handleSend}
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 shadow-2xl shadow-indigo-500/20 ${
                inputValue.trim() 
                ? 'bg-gradient-to-r from-indigo-500 to-pink-500 scale-100 rotate-0' 
                : 'bg-slate-800 scale-90 opacity-40 rotate-12'
              }`}
            >
              <Send size={20} className={`text-white transition-all ${inputValue.trim() ? 'translate-x-0.5' : ''}`} />
            </button>
          </div>
          
          {/* BARRE INDICATEUR IPHONE (Style) */}
          <div className="w-36 h-1.5 bg-slate-800/50 mx-auto mt-8 rounded-full hidden sm:block"></div>
        </footer>

      </div>
    </div>
  );
};

export default App;