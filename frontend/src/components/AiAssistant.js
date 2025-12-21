// src/components/AiAssistant.js
import React, { useState, useEffect, useRef } from 'react';

const AiAssistant = ({ lat, lon, city }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  // Initial messages
  const [messages, setMessages] = useState([
    { text: "Hello! I am your Weather Assistant. How can I help you today?", sender: 'bot' }
  ]);
  
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  
  const messagesEndRef = useRef(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(scrollToBottom, [messages, isOpen]);

  // Update greeting when city changes
  useEffect(() => {
    setMessages([{ 
        text: `Hi there! I see the weather in ${city || 'this area'} is changing. Do you need advice on your schedule or outfit?`, 
        sender: 'bot' 
    }]);
  }, [lat, lon, city]);

  // --- LOGIC GỐC GIỮ NGUYÊN ---
  const handleSend = async () => {
    if (!input.trim()) return;

    // 1. Show user message
    const userMsg = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setInput(""); 
    setLoading(true);

    try {
      // 2. Call API
      const response = await fetch('http://127.0.0.1:8000/api/chatbot/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            lat: lat, 
            lon: lon, 
            city: city, 
            question: userMsg.text 
        })
      });

      const data = await response.json();
      
      // 3. Handle response
      if (Array.isArray(data.reply)) {
        data.reply.forEach((text) => {
             setMessages(prev => [...prev, { text: text, sender: 'bot' }]);
        });
      } else {
        setMessages(prev => [...prev, { text: data.reply || "Sorry, I'm having a little trouble connecting.", sender: 'bot' }]);
      }

    } catch (err) {
      setMessages(prev => [...prev, { text: "Server is busy, please wait a moment...", sender: 'bot' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <div style={{ position: 'fixed', bottom: '30px', right: '30px', zIndex: 9999, display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
      
      {/* --- CHAT WINDOW (Xanh Dương - Medium Blue) --- */}
      {isOpen && (
        <div style={styles.chatWindow}>
          
          {/* Header Xanh Dương */}
          <div style={styles.header}>
            <div style={{display:'flex', alignItems:'center', gap: 10}}>
                <div style={styles.avatar}>🤖</div>
                <div>
                    <div style={{fontWeight:'600', fontSize: 16}}>AI Assistant</div>
                    <div style={{fontSize: 12, opacity: 0.9, fontWeight: 300}}>Always here to help</div>
                </div>
            </div>
            <button onClick={() => setIsOpen(false)} style={styles.closeBtn}>×</button>
          </div>

          {/* Body */}
          <div style={styles.body}>
            {messages.map((msg, index) => (
                <div key={index} style={{
                    alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                    // User: Màu Xanh Dương Vừa (#4a90e2)
                    // Bot: Màu xám nhạt (#f1f2f6)
                    backgroundColor: msg.sender === 'user' ? '#4a90e2' : '#f1f2f6',
                    color: msg.sender === 'user' ? 'white' : '#333',
                    padding: '10px 15px',
                    borderRadius: '18px',
                    borderBottomRightRadius: msg.sender === 'user' ? '4px' : '18px',
                    borderBottomLeftRadius: msg.sender === 'bot' ? '4px' : '18px',
                    maxWidth: '85%',
                    marginBottom: '10px',
                    fontSize: '14px',
                    lineHeight: '1.5',
                    boxShadow: '0 2px 5px rgba(0,0,0,0.05)',
                    wordWrap: 'break-word'
                }}>
                    {msg.text}
                </div>
            ))}
            
            {loading && (
                <div style={{alignSelf:'flex-start', color:'#888', fontSize:12, marginLeft:10, fontStyle:'italic', marginBottom: 10}}>
                    Bot is typing...
                </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Footer */}
          <div style={styles.footer}>
            <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                style={styles.input}
                disabled={loading}
            />
            <button onClick={handleSend} style={styles.sendBtn} disabled={loading}>
                ➤
            </button>
          </div>
        </div>
      )}

      {/* --- FLOATING BUTTON (Xanh Dương) --- */}
      <button onClick={() => setIsOpen(!isOpen)} style={styles.floatingBtn}>
        {isOpen ? '▼' : '💬'}
      </button>

    </div>
  );
};

// --- CSS STYLES (Tone Xanh Dương - Medium Blue) ---
const styles = {
  floatingBtn: {
    width: '60px', height: '60px', borderRadius: '50%',
    // Gradient Xanh Dương (Soft Blue to Darker Blue)
    background: 'linear-gradient(135deg, #6aafe6 0%, #357abd 100%)', 
    color: 'white', border: 'none',
    fontSize: '24px', cursor: 'pointer', 
    boxShadow: '0 4px 20px rgba(74, 144, 226, 0.4)', 
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'transform 0.2s',
    zIndex: 10000
  },
  chatWindow: {
    width: '350px', height: '500px', backgroundColor: '#fff',
    borderRadius: '24px', 
    boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
    marginBottom: '20px', overflow: 'hidden', display: 'flex', flexDirection: 'column',
    animation: 'fadeInUp 0.3s ease-out',
    border: '1px solid rgba(0,0,0,0.05)'
  },
  header: {
    // Header màu Xanh Dương (#4a90e2)
    backgroundColor: '#4a90e2', 
    padding: '15px 20px', color: 'white',
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
  },
  avatar: {
    width: 38, height: 38, background:'white', borderRadius:'50%', 
    display:'flex', alignItems:'center', justifyContent:'center', fontSize: 20,
    boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
  },
  closeBtn: { background: 'transparent', border: 'none', color: 'white', fontSize: '24px', cursor: 'pointer', opacity: 0.8 },
  body: {
    flex: 1, padding: '20px', backgroundColor: '#fff', overflowY: 'auto',
    display: 'flex', flexDirection: 'column'
  },
  footer: {
    padding: '15px', borderTop: '1px solid #f0f0f0', display: 'flex', gap: '10px', backgroundColor: '#fff'
  },
  input: {
    flex: 1, padding: '12px 15px', borderRadius: '25px', border: '1px solid #eee', outline: 'none', fontSize: '14px',
    backgroundColor: '#f9f9f9', color: '#333'
  },
  sendBtn: {
    background: '#4a90e2', 
    color: 'white', border: 'none', width: '42px', height: '42px',
    borderRadius: '50%', cursor: 'pointer', display: 'flex', alignItems:'center', justifyContent:'center', fontSize: '16px',
    boxShadow: '0 2px 8px rgba(74, 144, 226, 0.3)'
  }
};

// Animation Style
const styleSheet = document.createElement("style");
styleSheet.innerText = `
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
`;
document.head.appendChild(styleSheet);

export default AiAssistant;