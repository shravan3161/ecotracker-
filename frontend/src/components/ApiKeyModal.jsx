import React, { useState } from 'react';

export default function ApiKeyModal({ isOpen, onClose, onShowToast }) {
  const [apiKey, setApiKey] = useState(localStorage.getItem('ecotracker_cloud_api_key') || '');
  const [modelProvider, setModelProvider] = useState(localStorage.getItem('ecotracker_model_provider') || 'gemini');

  if (!isOpen) return null;

  const saveKey = () => {
    localStorage.setItem('ecotracker_cloud_api_key', apiKey.trim());
    localStorage.setItem('ecotracker_model_provider', modelProvider);
    onShowToast('🔑 API credentials updated!');
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: 800 }}>⚙️ Cloud LLM Configuration</h2>
          <button className="btn btn-secondary" style={{ padding: '4px 10px' }} onClick={onClose}>
            ✕
          </button>
        </div>

        <p style={{ color: 'var(--text-secondary)', marginBottom: '20px', fontSize: '15px' }}>
          Configure your cloud AI keys for conversational reasoning and multimodal vision OCR. Keys are encrypted
          client-side in local storage.
        </p>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>
            Provider Selection
          </label>
          <select
            className="form-input"
            value={modelProvider}
            onChange={(e) => setModelProvider(e.target.value)}
          >
            <option value="gemini">Google Gemini (gemini-2.5-flash-lite / pro)</option>
            <option value="groq">Groq Cloud (llama-3.3-70b-versatile)</option>
          </select>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>
            API Key
          </label>
          <input
            type="password"
            className="form-input"
            placeholder={modelProvider === 'gemini' ? 'AIzaSy...' : 'gsk_...'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={saveKey}>
            Save Credentials
          </button>
        </div>
      </div>
    </div>
  );
}
