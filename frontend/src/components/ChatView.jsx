import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';

export default function ChatView({ userId, dashboardData, onRefreshDashboard, onShowToast }) {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: "👋 **Hello! I am your AI Carbon Intelligence Advisor.**\n\nTell me about your daily activities (e.g. *\"Drove 40 km in my car\"*, *\"Ate a 200g burger\"*, *\"Ran my 2 kW AC for 5 hours\"*) or use the 🎙️ **Voice** button to dictate hands-free. I will compute exact emissions and suggest high-impact eco-swaps!"
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const feedEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  // Voice Speech-to-Text setup (Web Speech API)
  const toggleVoiceRecording = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onShowToast('⚠️ Speech recognition not supported in this browser.');
      return;
    }

    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      return;
    }

    try {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-US';

      rec.onstart = () => {
        setIsRecording(true);
        onShowToast('🎙️ Listening... speak naturally');
      };

      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputText((prev) => (prev ? `${prev} ${transcript}` : transcript));
        onShowToast(`🗣️ Heard: "${transcript}"`);
      };

      rec.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        onShowToast(`⚠️ Voice error: ${event.error}`);
      };

      rec.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = rec;
      rec.start();
    } catch (err) {
      console.error(err);
      setIsRecording(false);
    }
  };

  const sendMessage = async (customPrompt) => {
    const textToSend = customPrompt || inputText.trim();
    if (!textToSend || isSending) return;

    const newMsgs = [...messages, { sender: 'user', text: textToSend }];
    setMessages(newMsgs);
    if (!customPrompt) setInputText('');
    setIsSending(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: textToSend, user_id: userId })
      });
      const data = await res.json();
      if (data.reply) {
        setMessages((prev) => [...prev, { sender: 'bot', text: data.reply, card: data.co2e_kg > 0 ? data : null }]);
        if (data.logged_record) {
          onRefreshDashboard();
        }
      } else {
        setMessages((prev) => [...prev, { sender: 'bot', text: '⚠️ Unable to compute carbon data. Please try again.' }]);
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { sender: 'bot', text: '⚠️ Network connection error. Is the server running?' }]);
    } finally {
      setIsSending(false);
    }
  };

  const quickPrompts = [
    'Drove 45 km in a gasoline car',
    'Ate 250g of beef steak for lunch',
    'Flew from LHR to CDG economy class',
    'Ran a 3.5 kW AC unit for 6 hours'
  ];

  // Budget alert logic
  const todayEmissions = dashboardData?.summary?.today_emissions_kg || 0;
  const dailyBudget = dashboardData?.daily_budget_kg || 15;
  const budgetRatio = dailyBudget > 0 ? (todayEmissions / dailyBudget) * 100 : 0;

  return (
    <div className="chat-layout">
      {/* Proactive Budget Alert */}
      {budgetRatio >= 80 && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '12px',
            background: budgetRatio >= 100 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            border: `1px solid ${budgetRatio >= 100 ? '#ef4444' : '#f59e0b'}`,
            color: budgetRatio >= 100 ? '#fca5a5' : '#fde047',
            fontSize: '15px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <span>{budgetRatio >= 100 ? '🚨' : '⚠️'}</span>
          <span>
            {budgetRatio >= 100
              ? `Daily Budget Exceeded! Used ${todayEmissions.toFixed(1)} / ${dailyBudget} kg CO2e (${budgetRatio.toFixed(0)}%). Consider high-impact eco-swaps.`
              : `Carbon Alert: You have reached ${budgetRatio.toFixed(0)}% of your daily budget (${todayEmissions.toFixed(1)} / ${dailyBudget} kg CO2e).`}
          </span>
        </div>
      )}

      {/* Quick Prompt Pills */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            className="status-badge"
            style={{ cursor: 'pointer', whiteSpace: 'nowrap', fontSize: '14px' }}
            onClick={() => sendMessage(p)}
          >
            💡 {p}
          </button>
        ))}
      </div>

      {/* Messages Feed */}
      <div className="chat-message-feed">
        {messages.map((m, idx) => {
          const isBot = m.sender === 'bot';
          return (
            <div key={idx} className={`chat-row ${isBot ? 'bot-row' : 'user-row'}`}>
              <div className={`chat-avatar ${isBot ? 'avatar-bot' : 'avatar-user'}`}>
                {isBot ? '🌱' : userId ? userId.slice(0, 2).toUpperCase() : 'ME'}
              </div>
              <div className={`chat-bubble ${isBot ? 'bubble-bot' : 'bubble-user'}`}>
                <div
                  dangerouslySetInnerHTML={{
                    __html: marked.parse(m.text, { breaks: true })
                  }}
                />
              </div>
            </div>
          );
        })}
        {isSending && (
          <div className="chat-row bot-row">
            <div className="chat-avatar avatar-bot">🌱</div>
            <div className="chat-bubble bubble-bot" style={{ fontStyle: 'italic', color: 'var(--text-secondary)' }}>
              Analyzing footprint with Google ADK multi-agent pipeline...
            </div>
          </div>
        )}
        <div ref={feedEndRef} />
      </div>

      {/* Input Bar */}
      <div className="chat-input-bar">
        <button
          className={`mic-btn ${isRecording ? 'recording' : ''}`}
          onClick={toggleVoiceRecording}
          title={isRecording ? 'Stop Recording' : 'Voice Speech-to-Text'}
          type="button"
        >
          🎙️
        </button>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type or speak an activity (e.g. 'Drove 40 km in hybrid car')..."
        />
        <button className="btn btn-primary" onClick={() => sendMessage()} disabled={isSending}>
          Send ➔
        </button>
      </div>
    </div>
  );
}
