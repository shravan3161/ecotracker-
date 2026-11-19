import React from 'react';

export default function Header({
  activeTab,
  onOpenMobileMenu,
  weather,
  gridStatus,
  onRefreshGrid,
  theme,
  onToggleTheme
}) {
  const tabTitles = {
    chat: { title: '💬 AI Carbon Chat', subtitle: 'Interactive sustainability intelligence advisor with voice' },
    scanner: { title: '📸 Vision Document Scanner', subtitle: 'Multimodal OCR line-item receipt & bill footprinting' },
    analytics: { title: '📊 Analytics & Carbon Goals', subtitle: '30-day emissions time-series & budget tracking' },
    leaderboard: { title: '🏆 Sustainability Leaderboard', subtitle: 'Team & community carbon-avoided rankings' },
    habits: { title: '⚡ Eco Habits Studio', subtitle: '1-click quick-log presets with celebratory confetti' },
    simulator: { title: '🔮 What-If Climate & ROI Simulator', subtitle: 'Interactive transition modeling across 1, 5, and 10 year horizons' },
    esg: { title: '💼 Enterprise ESG Scope 1, 2, 3', subtitle: 'GHG Protocol corporate disclosure & printable audit report' },
    history: { title: '📋 Activity History & Audit', subtitle: 'Searchable ledger with CSV export and row deletion' },
    offsets: { title: '🌍 Verified Carbon Offset Projects', subtitle: 'Gold Standard & Verra verified carbon credit catalog' }
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
        {weather && (
          <div
            className="status-badge"
            style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}
            title="Outdoor Ambient Weather (Open-Meteo API)"
          >
            ☀️ {weather.temp}°C ({weather.condition})
          </div>
        )}
        <div
          className="status-badge"
          style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', cursor: 'pointer' }}
          onClick={onRefreshGrid}
          title="Click to Refresh Regional Grid Carbon Intensity"
        >
          ⚡ Grid: {gridStatus ? `${gridStatus.intensity_g_per_kwh} g/kWh (${gridStatus.clean_status})` : 'Loading...'}
        </div>
        <button className="theme-toggle-btn" onClick={onToggleTheme} title="Toggle Dark/Light Theme">
          {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
        </button>
      </div>
    </header>
  );
}
