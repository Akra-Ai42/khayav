const { useState, useEffect, useRef } = React;

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

    // Scroll automatique et mise à jour des icônes Lucide
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }, [messages, isTyping]);

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        const userText = inputValue;
        const userMsg = {
            id: Date.now(),
            text: userText,
            sender: 'user',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        try {
            // APPEL API RELATIF (Fonctionne sur Render et en local)
            const response = await fetch('/api/khayav/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: userText, 
                    ...sessionData 
                })
            });

            if (!response.ok) throw new Error("Erreur serveur");

            const data = await response.json();
            
            // Mise à jour des badges
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
                text: "⚠️ Oh peuchère, j'ai perdu le fil... Vérifie que mon cerveau sur Render est bien réveillé !",
                sender: 'bot',
                time: 'Erreur'
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-[#020617] p-0 sm:p-4 font-sans text-slate-100 selection:bg-indigo-500/30">
            
            {/* CONTENEUR MOBILE STYLE IPHONE */}
            <div className="relative w-full max-w-md h-[100vh] sm:h-[850px] bg-[#0b141a] sm:rounded-[3rem] shadow-[0_0_80px_rgba(79,70,229,0.3)] overflow-hidden border-0 sm:border-[10px] border-slate-900 flex flex-col">
                
                {/* EN-TÊTE PREMIUM */}
                <header className="pt-12 pb-5 px-6 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 shadow-2xl z-10 relative">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-white/10 backdrop-blur-xl rounded-2xl flex items-center justify-center border border-white/20 shadow-inner">
                                <span className="text-2xl">🥗</span>
                            </div>
                            <div>
                                <h1 className="font-black text-xl tracking-tight flex items-center gap-2">
                                    Agent Khayav ✨
                                </h1>
                                <div className="flex items-center gap-1.5 opacity-90">
                                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                                    <p className="text-[10px] font-bold text-indigo-100 uppercase tracking-widest">
                                        Marseille • En ligne
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    {/* BADGES DYNAMIQUES */}
                    <div className="mt-5 flex gap-2 overflow-x-auto no-scrollbar pb-1">
                        <span className="bg-white/10 backdrop-blur-md border border-white/20 px-3 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap flex items-center gap-1.5 shadow-sm">
                            <i data-lucide="map-pin" className="w-3 h-3 text-pink-300"></i> Vieux-Port
                        </span>
                        {sessionData.date && (
                            <span className="bg-green-500/30 border border-green-400/50 px-3 py-1.5 rounded-full text-[10px] font-bold flex items-center gap-1.5 animate-in zoom-in">
                                <i data-lucide="calendar" className="w-3 h-3"></i> {sessionData.date}
                            </span>
                        )}
                        {sessionData.heure && (
                            <span className="bg-blue-500/30 border border-blue-400/50 px-3 py-1.5 rounded-full text-[10px] font-bold flex items-center gap-1.5 animate-in zoom-in">
                                <i data-lucide="clock" className="w-3 h-3"></i> {sessionData.heure}
                            </span>
                        )}
                        {sessionData.couverts && (
                            <span className="bg-orange-500/30 border border-orange-400/50 px-3 py-1.5 rounded-full text-[10px] font-bold flex items-center gap-1.5 animate-in zoom-in">
                                <i data-lucide="users" className="w-3 h-3"></i> {sessionData.couverts} pers
                            </span>
                        )}
                    </div>
                </header>

                {/* ZONE DE MESSAGES */}
                <main className="flex-1 overflow-y-auto p-4 space-y-6 bg-[#0b141a]">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} msg-anim`}>
                            <div className={`max-w-[85%] p-4 rounded-[1.8rem] shadow-2xl ${
                                msg.sender === 'user' 
                                    ? 'bg-indigo-600 text-white rounded-tr-none' 
                                    : 'bg-slate-800/80 backdrop-blur-md text-slate-100 border border-white/10 rounded-tl-none'
                            }`}>
                                <p className="text-[14.5px] leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                                <div className="flex items-center justify-end gap-1.5 mt-2 opacity-50">
                                    <span className="text-[9px] font-black uppercase">{msg.time}</span>
                                    {msg.sender === 'user' && <i data-lucide="check-check" className="w-3 h-3"></i>}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isTyping && (
                        <div className="flex justify-start">
                            <div className="bg-slate-800/40 px-6 py-4 rounded-[1.8rem] rounded-tl-none animate-pulse text-indigo-400 text-xs font-bold">
                                KHAYAV RÉFLÉCHIT...
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </main>

                {/* ZONE DE SAISIE */}
                <footer className="p-5 bg-slate-900/80 backdrop-blur-xl border-t border-white/5 pb-8">
                    <form onSubmit={sendMessage} className="flex items-center gap-3 bg-[#0b141a] p-2 rounded-[2.5rem] border border-white/10">
                        <input 
                            type="text" 
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Dis-moi tout..."
                            className="flex-1 bg-transparent border-none focus:ring-0 text-sm px-4 py-2 text-white"
                        />
                        <button type="submit" className="w-12 h-12 rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 flex items-center justify-center shadow-lg active:scale-90 transition-all">
                            <i data-lucide="send" className="w-5 h-5 text-white"></i>
                        </button>
                    </form>
                </footer>
            </div>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);