import React from 'react';

export default function MobileNav({
  activeTab,
  onSelectTab,
  isDrawerOpen,
  onCloseDrawer,
  userId,
  onChangeUserId,
  onOpenApiKeyModal,
  onOpenScorecardModal
}) {
  const bottomTabs = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'analytics', label: 'Analytics', icon: '📊' },
    { id: 'habits', label: 'Habits', icon: '⚡' },
    { id: 'leaderboard', label: 'Leaderboard', icon: '🏆' },
    { id: 'scanner', label: 'Scanner', icon: '📸' }
  ];

  const allTabs = [
    { id: 'chat', label: '💬 AI Carbon Chat' },
    { id: 'scanner', label: '📸 Vision Scanner' },
    { id: 'analytics', label: '📊 Analytics & Goals' },
    { id: 'simulator', label: '🔮 What-If Simulator' },
    { id: 'leaderboard', label: '🏆 Leaderboard' },
    { id: 'habits', label: '⚡ Habits Studio' },
    { id: 'esg', label: '💼 Enterprise ESG' },
    { id: 'history', label: '📋 Activity History' },
    { id: 'offsets', label: '🌍 Carbon Offsets' }
  ];

  return (
    <>
      {/* Mobile Bottom Nav */}
      <nav className="mobile-bottom-nav">
        {bottomTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              className={`bottom-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTab(tab.id)}
            >
              <span className="bottom-nav-icon">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Drawer Overlay */}
      <div className={`mobile-drawer-overlay ${isDrawerOpen ? 'open' : ''}`} onClick={onCloseDrawer}>
        <div className="mobile-drawer-content" onClick={(e) => e.stopPropagation()}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ fontSize: '20px', fontWeight: 800 }}>🌱 EcoTracker</div>
              <button className="btn btn-secondary" style={{ padding: '6px 12px' }} onClick={onCloseDrawer}>
                ✕
              </button>
            </div>
            <ul className="nav-list">
              {allTabs.map((item) => (
                <li key={item.id}>
                  <button
                    className={`nav-button ${activeTab === item.id ? 'active' : ''}`}
                    onClick={() => {
                      onSelectTab(item.id);
                      onCloseDrawer();
                    }}
                  >
                    <span>{item.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
            <div style={{ fontSize: '14px', color: 'var(--text-tertiary)', marginBottom: '8px', fontWeight: 700 }}>
              Session: {userId}
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button
                className="btn btn-secondary"
                style={{ flex: 1, fontSize: '14px' }}
                onClick={() => {
                  onOpenApiKeyModal();
                  onCloseDrawer();
                }}
              >
                ⚙️ API Key
              </button>
              <button
                className="btn btn-cyan"
                style={{ fontSize: '14px' }}
                onClick={() => {
                  onOpenScorecardModal();
                  onCloseDrawer();
                }}
              >
                🏅 Scorecard
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
