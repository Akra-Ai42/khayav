const { useState, useEffect, useRef } = React;

const App = () => {
    const [messages, setMessages] = useState([{ id: 1, text: "Salut l'ami ! Bienvenue à La Cantine d'Akram. 🌊\n\nJe suis Khayav, ton assistant marseillais. Tu veux réserver ?", sender: 'bot', time: 'En ligne' }]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [sessionData, setSessionData] = useState({ nom: null, date: null, heure: null, couverts: null });
    const messagesEndRef = useRef(null);

    // Scroll automatique vers le bas
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        if (window.lucide) window.lucide.createIcons();
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
            
            // Mise à jour des données de contexte
            setSessionData({ nom: data.nom, date: data.date, heure: data.heure, couverts: data.couverts });
            
            setMessages(prev => [...prev, { id: Date.now(), text: data.reponse, sender: 'bot', time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }]);
        } catch (err) {
            setMessages(prev => [...prev, { id: Date.now(), text: "⚠️ Le cerveau est en pause café.", sender: 'bot', time: 'Erreur' }]);
        } finally { 
            setIsTyping(false); 
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen p-0 sm:p-4">
            <div className="relative w-full max-w-md h-[100vh] sm:h-[800px] bg-[#0b141a] sm:rounded-[3rem] shadow-2xl overflow-hidden border-0 sm:border-[8px] border-slate-900 flex flex-col">
                <header className="pt-12 pb-5 px-6 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 shadow-xl z-10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center border border-white/20">
                                <span className="text-2xl">🥗</span>
                            </div>
                            <div>
                                <h1 className="font-bold text-lg leading-none">Agent Khayav ✨</h1>
                                <p className="text-[10px] opacity-80 uppercase tracking-widest mt-1">Marseille • En ligne</p>
                            </div>
                        </div>
                        <button onClick={() => window.location.reload()} className="p-2 bg-white/10 rounded-full hover:rotate-180 transition-all duration-500">
                            <i data-lucide="refresh-ccw" className="w-4 h-4"></i>
                        </button>
                    </div>
                    
                    {/* Badges dynamiques basés sur sessionData */}
                    <div className="mt-4 flex gap-2 overflow-x-auto no-scrollbar pb-1">
                        <span className="bg-white/10 px-3 py-1 rounded-full text-[10px] flex items-center gap-1">
                            <i data-lucide="map-pin" className="w-3 h-3"></i>Vieux-Port
                        </span>
                        {sessionData.date && <span className="bg-green-500/30 px-3 py-1 rounded-full text-[10px] flex items-center gap-1 animate-in"><i data-lucide="calendar" className="w-3 h-3"></i>{sessionData.date}</span>}
                        {sessionData.heure && <span className="bg-blue-500/30 px-3 py-1 rounded-full text-[10px] flex items-center gap-1 animate-in"><i data-lucide="clock" className="w-3 h-3"></i>{sessionData.heure}</span>}
                        {sessionData.couverts && <span className="bg-orange-500/30 px-3 py-1 rounded-full text-[10px] flex items-center gap-1 animate-in"><i data-lucide="users" className="w-3 h-3"></i>{sessionData.couverts} pers</span>}
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto p-4 space-y-4 bg-[url('[https://www.transparenttextures.com/patterns/carbon-fibre.png](https://www.transparenttextures.com/patterns/carbon-fibre.png)')]">
                    {messages.map(msg => (
                        <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} msg-anim`}>
                            <div className={`max-w-[85%] p-3 rounded-2xl shadow-lg ${msg.sender === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-100 rounded-tl-none border border-white/5'}`}>
                                <p className="text-sm leading-relaxed">{msg.text}</p>
                                <div className="flex justify-end gap-1 mt-1 opacity-50 text-[9px] font-bold">
                                    <span>{msg.time}</span>
                                    {msg.sender === 'user' && <i data-lucide="check-check" className="w-3 h-3"></i>}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isTyping && <div className="text-indigo-400 text-[10px] animate-pulse font-bold uppercase ml-2">Khayav réfléchit...</div>}
                    <div ref={messagesEndRef} />
                </main>

                <footer className="p-4 bg-slate-900 border-t border-white/5 pb-10 sm:pb-4">
                    <form onSubmit={sendMessage} className="flex gap-2 bg-[#0b141a] p-1.5 rounded-full border border-white/10 shadow-inner">
                        <input value={inputValue} onChange={e => setInputValue(e.target.value)} type="text" placeholder="Dis-moi tout..." className="flex-1 bg-transparent border-none px-4 py-2 text-sm focus:ring-0 outline-none text-white" />
                        <button type="submit" className="bg-gradient-to-r from-indigo-500 to-purple-600 p-2.5 rounded-full shadow-lg active:scale-95 transition-transform">
                            <i data-lucide="send" className="w-4 h-4 text-white"></i>
                        </button>
                    </form>
                </footer>
            </div>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);