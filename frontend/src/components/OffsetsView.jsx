import React, { useState } from 'react';

export default function OffsetsView({ onShowToast }) {
  const [retireTons, setRetireTons] = useState(2);

  const projects = [
    {
      id: 'mangroves',
      title: '🌊 Coastal Mangrove Blue Carbon',
      location: 'Madagascar & Southeast Asia',
      standard: 'Verra VCS (VM0033)',
      pricePerTon: 18,
      desc: 'Restoring tidal mangrove estuaries that sequester carbon 4x faster than terrestrial tropical forests.'
    },
    {
      id: 'wind',
      title: '💨 North Sea Offshore Wind Expansion',
      location: 'Scotland & Netherlands',
      standard: 'Gold Standard GS4GG',
      pricePerTon: 12,
      desc: 'Displacing coal-fired power from the European regional grid with clean offshore wind energy.'
    },
    {
      id: 'biochar',
      title: '🔥 Biochar Carbon Removal (Pyrolysis)',
      location: 'Kenya & East Africa',
      standard: 'Puro.earth Standard',
      pricePerTon: 35,
      desc: 'Permanent 500+ year geological carbon sequestration improving soil fertility and agricultural yields.'
    },
    {
      id: 'cookstoves',
      title: '🍳 Clean Household Efficient Cookstoves',
      location: 'Uganda & Rwanda',
      standard: 'Gold Standard CER',
      pricePerTon: 14,
      desc: 'Halving fuelwood usage in rural kitchens, saving old-growth forests and reducing household smoke.'
    }
  ];

  return (
    <div>
      <div className="modern-card">
        <div className="card-title-row">
          <div className="card-title">🌍 Verified Carbon Offset Projects</div>
          <span className="brand-badge">Gold Standard & Verra</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Neutralize unavoidable emissions by investing in accredited, high-durability climate projects with third-party
          registry verification.
        </p>

        <div className="grid-2" style={{ marginBottom: '30px' }}>
          {projects.map((p) => (
            <div
              key={p.id}
              className="modern-card"
              style={{
                marginBottom: 0,
                background: 'var(--bg-surface-elevated)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '18px', fontWeight: 700 }}>{p.title}</span>
                  <span className="status-badge" style={{ background: 'rgba(56,189,248,0.15)', color: '#38bdf8' }}>
                    {p.standard}
                  </span>
                </div>
                <div style={{ fontSize: '14px', color: 'var(--text-tertiary)', marginBottom: '10px' }}>📍 {p.location}</div>
                <p style={{ fontSize: '15px', color: 'var(--text-secondary)', marginBottom: '16px' }}>{p.desc}</p>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '14px'
                }}
              >
                <span style={{ fontSize: '18px', fontWeight: 800, color: 'var(--primary-light)' }}>
                  ${p.pricePerTon} <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>/ tonne</span>
                </span>
                <button
                  className="btn btn-primary"
                  style={{ fontSize: '14px', padding: '6px 14px' }}
                  onClick={() => onShowToast(`🌱 Retired 1 Tonne under: ${p.title}`)}
                >
                  Retire Offset
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Portfolio Simulator */}
        <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
          <div className="card-title-row">
            <div className="card-title">⚖️ Offset Portfolio Simulator</div>
            <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent-cyan)' }}>
              {retireTons} Tonnes = ${(retireTons * 18).toFixed(0)} USD
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Balance your net household footprint to zero by simulating an annualized portfolio allocation.
          </p>
          <input
            type="range"
            min="1"
            max="25"
            step="1"
            value={retireTons}
            onChange={(e) => setRetireTons(parseInt(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent-cyan)', height: '8px' }}
          />
        </div>
      </div>
    </div>
  );
}
