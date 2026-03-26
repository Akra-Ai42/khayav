const { useState, useEffect, useRef } = React;

const App = () => {
    const [messages, setMessages] = useState([{ 
        id: 1, 
        text: "Salut l'ami ! Bienvenue à La Cantine d'Akram. 🌊\n\nJe suis Khayav, ton assistant marseillais. Tu veux réserver ?", 
        sender: 'bot', 
        time: 'En ligne' 
    }]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [sessionData, setSessionData] = useState({ nom: null, date: null, heure: null, couverts: null });
    const messagesEndRef = useRef(null);

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
            // Utilisation d'un chemin relatif pour que ça marche partout
            const res = await fetch('/api/khayav/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText, ...sessionData })
            });
            const data = await res.json();
            
            setSessionData({ nom: data.nom, date: data.date, heure: data.heure, couverts: data.couverts });
            setMessages(prev => [...prev, { id: Date.now(), text: data.reponse, sender: 'bot', time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }]);
        } catch (err) {
            setMessages(prev => [...prev, { id: Date.now(), text: "⚠️ Peuchère, le serveur fait la sieste.", sender: 'bot', time: 'Erreur' }]);
        } finally { 
            setIsTyping(false); 
        }
    };

    return (
        /* ... Ton code JSX reste identique ici ... */
        <div className="flex items-center justify-center min-h-screen p-0 sm:p-4">
             {/* Contenu de ton interface */}
             <p className="p-4">Agent Khayav opérationnel ! (Insère ton JSX complet ici)</p>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);