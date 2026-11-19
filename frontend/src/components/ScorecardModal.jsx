import React from 'react';

export default function ScorecardModal({ isOpen, onClose, dashboardData, userId, onShowToast }) {
  if (!isOpen) return null;

  const summary = dashboardData?.summary || {};
  const totalSaved = summary.total_saved_co2e_kg ? summary.total_saved_co2e_kg.toFixed(1) : '0.0';
  const totalGross = summary.total_co2e_kg ? summary.total_co2e_kg.toFixed(1) : '0.0';
  const badgeCount = dashboardData?.badges?.length || 0;

  const copyScorecard = () => {
    const text = `🌱 My EcoTracker Sustainability Scorecard 🌱\n👤 User: ${userId}\n💚 Carbon Avoided: +${totalSaved} kg CO2e\n📊 Lifetime Footprint: ${totalGross} kg CO2e\n🏅 Badges Unlocked: ${badgeCount}\nTrack yours at: http://localhost:8085`;
    navigator.clipboard.writeText(text);
    onShowToast('📋 Scorecard copied to clipboard!');
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '8px' }}>🌱</div>
          <h2 style={{ fontSize: '24px', fontWeight: 800 }}>Eco Impact Scorecard</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Verified lifestyle sustainability credentials</p>
        </div>

        <div
          style={{
            background: 'var(--bg-surface-elevated)',
            borderRadius: '16px',
            padding: '24px',
            border: '1px solid var(--border-subtle)',
            marginBottom: '24px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Champion:</span>
            <span style={{ fontWeight: 700 }}>{userId}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Carbon Avoided:</span>
            <span style={{ fontWeight: 800, color: '#34d399', fontSize: '18px' }}>+{totalSaved} kg CO2e</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Gross Footprint:</span>
            <span style={{ fontWeight: 700, color: '#f87171' }}>{totalGross} kg CO2e</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Badges Unlocked:</span>
            <span style={{ fontWeight: 700, color: '#c084fc' }}>{badgeCount} 🏅</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
            Close
          </button>
          <button className="btn btn-primary" style={{ flex: 2 }} onClick={copyScorecard}>
            📋 Copy & Share Scorecard
          </button>
        </div>
      </div>
    </div>
  );
}
