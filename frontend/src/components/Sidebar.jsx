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
          <div className="brand-logo">🌱</div>
          <div>
            <div className="brand-title">
              EcoTracker<span className="brand-badge">React</span>
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
