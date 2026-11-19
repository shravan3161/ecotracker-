import React from 'react';

export default function Header({
  activeTab,
  onOpenMobileMenu,
  theme,
  onToggleTheme
}) {
  const tabTitles = {
    chat: { title: '💬 AI Carbon Chat', subtitle: 'Interactive sustainability intelligence advisor with voice' },
    scanner: { title: '📸 Vision Document Scanner', subtitle: 'Multimodal OCR line-item receipt & bill footprinting' },
    analytics: { title: '📊 Analytics & Carbon Goals', subtitle: '30-day emissions time-series & budget tracking' },
    leaderboard: { title: '🏆 Sustainability Leaderboard', subtitle: 'Team & community carbon-avoided rankings' },
    habits: { title: '⚡ Eco Habits Studio', subtitle: 'Customizable habit builder with celebratory confetti' },
    simulator: { title: '🔮 What-If Climate & ROI Simulator', subtitle: 'Interactive transition modeling across 1, 5, and 10 year horizons' },
    esg: { title: '💼 Enterprise ESG Scope 1, 2, 3', subtitle: 'GHG Protocol corporate disclosure & printable audit report' },
    history: { title: '📋 Activity History & Audit', subtitle: 'Searchable ledger with CSV export and row deletion' },
    offsets: { title: '🌍 Verified Carbon Offset Projects', subtitle: 'Gold Standard & Verra verified carbon credit catalog' },
    future: { title: '🚀 Future Scope & Strategic Roadmap', subtitle: 'IoT telemetry, open banking, autonomous A2A auctions, and decentralized audits' }
  };

  const current = tabTitles[activeTab] || tabTitles.chat;

  return (
    <header className="top-header">
      <div className="header-left">
        <button className="mobile-menu-trigger" onClick={onOpenMobileMenu} aria-label="Open Navigation Menu">
          ☰
        </button>
        <div className="header-title-box">
          <h2>{current.title}</h2>
          <p>{current.subtitle}</p>
        </div>
      </div>

      <div className="header-actions">
        <button className="theme-toggle-btn" onClick={onToggleTheme} title="Toggle Dark/Light Theme">
          {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
        </button>
      </div>
    </header>
  );
}
