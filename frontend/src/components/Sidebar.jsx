import React from 'react';

export default function Sidebar({
  activeTab,
  onSelectTab,
  userId,
  onChangeUserId,
  onOpenApiKeyModal,
  onOpenScorecardModal,
  historyCount
}) {
  const navItems = [
    { id: 'chat', label: '💬 AI Carbon Chat', pill: 'Bot', pillStyle: { background: 'rgba(16,185,129,0.2)', color: '#34d399' } },
    { id: 'scanner', label: '📸 Vision Scanner', pill: 'AI OCR', pillStyle: { background: 'rgba(56,189,248,0.2)', color: '#38bdf8' } },
    { id: 'analytics', label: '📊 Analytics & Goals' },
    { id: 'simulator', label: '🔮 What-If Simulator' },
    { id: 'leaderboard', label: '🏆 Leaderboard', pill: 'Rank', pillStyle: { background: 'rgba(245,158,11,0.2)', color: '#fbbf24' } },
    { id: 'habits', label: '⚡ Habits Studio' },
    { id: 'esg', label: '💼 Enterprise ESG', pill: 'B2B', pillStyle: { background: 'rgba(168,85,247,0.2)', color: '#c084fc' } },
    { id: 'history', label: '📋 Activity History', pill: historyCount ?? '0', pillStyle: { background: 'rgba(255,255,255,0.08)', color: 'var(--text-secondary)' } },
    { id: 'offsets', label: '🌍 Carbon Offsets' },
    { id: 'future', label: '🚀 Future Scope', pill: 'Roadmap', pillStyle: { background: 'rgba(59,130,246,0.2)', color: '#60a5fa' } }
  ];

  return (
    <aside className="desktop-sidebar">
      <div>
        <div className="brand-header">
          <div className="brand-logo" style={{ background: 'transparent', boxShadow: 'none', padding: 0 }}>
            <svg width="42" height="42" viewBox="0 0 64 64" fill="none">
              <rect width="64" height="64" rx="16" fill="#080d1a" stroke="rgba(16, 185, 129, 0.45)" strokeWidth="2.5" />
              <path d="M32 9 C47 9, 54 22, 52 38 C50 51, 38 55, 32 55 C26 55, 14 51, 12 38 C10 22, 17 9, 32 9 Z" fill="url(#brandGrad)" />
              <path d="M32 17 L32 47" stroke="#ffffff" strokeWidth="3.2" strokeLinecap="round" />
              <path d="M32 25 L43 19" stroke="#ffffff" strokeWidth="2.6" strokeLinecap="round" />
              <circle cx="43" cy="19" r="2.5" fill="#38bdf8" />
              <path d="M32 33 L21 27" stroke="#ffffff" strokeWidth="2.6" strokeLinecap="round" />
              <circle cx="21" cy="27" r="2.5" fill="#38bdf8" />
              <path d="M32 41 L41 36" stroke="#ffffff" strokeWidth="2.6" strokeLinecap="round" />
              <circle cx="41" cy="36" r="2.5" fill="#38bdf8" />
              <circle cx="32" cy="16" r="4" fill="#38bdf8" stroke="#ffffff" strokeWidth="1.8" />
              <defs>
                <linearGradient id="brandGrad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#34d399" />
                  <stop offset="1" stopColor="#059669" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div>
            <div className="brand-title">
              EcoTracker<span className="brand-badge">AI</span>
            </div>
          </div>
        </div>

        <ul className="nav-list">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <li key={item.id}>
                <button
                  className={`nav-button ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectTab(item.id)}
                >
                  <span className="nav-left">{item.label}</span>
                  {item.pill && (
                    <span className="nav-pill" style={item.pillStyle}>
                      {item.pill}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="sidebar-footer">
        <div style={{ fontSize: '14px', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: '8px' }}>
          Customer Session
        </div>
        <div className="customer-pill">
          <span>👤</span>
          <input
            type="text"
            value={userId}
            onChange={(e) => onChangeUserId(e.target.value)}
            placeholder="User ID"
          />
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary" style={{ flex: 1, fontSize: '14px' }} onClick={onOpenApiKeyModal}>
            ⚙️ API Key
          </button>
          <button className="btn btn-cyan" style={{ fontSize: '14px' }} onClick={onOpenScorecardModal}>
            🏅 Scorecard
          </button>
        </div>
      </div>
    </aside>
  );
}
