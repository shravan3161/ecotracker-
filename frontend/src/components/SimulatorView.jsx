import React, { useState, useEffect } from 'react';

export default function SimulatorView() {
  const [transitDays, setTransitDays] = useState(3);
  const [dietLevel, setDietLevel] = useState(2);
  const [solarPct, setSolarPct] = useState(50);
  const [flightReplaced, setFlightReplaced] = useState(1);
  const [results, setResults] = useState(null);

  useEffect(() => {
    // Calculate scenario
    const annualCommuteSaved = transitDays * 50 * 50 * (0.192 - 0.035); // kg CO2e
    const annualDietSaved = dietLevel * 365 * 1.5; // ~1.5 kg saved/day per tier
    const annualEnergySaved = (solarPct / 100) * 3600 * 0.38; // ~3600 kWh annual baseline
    const annualFlightSaved = flightReplaced * 450; // average short haul flight kg CO2e

    const totalAnnualSavedKg = annualCommuteSaved + annualDietSaved + annualEnergySaved + annualFlightSaved;
    const totalAnnualSavedTonnes = totalAnnualSavedKg / 1000;

    // Financial calculations ($)
    const annualFuelSavedUsd = transitDays * 50 * (20 / 100) * 1.35 * 48; // gas + wear
    const annualGroceriesSavedUsd = dietLevel * 220;
    const annualElectricitySavedUsd = (solarPct / 100) * 420;
    const annualFlightSavedUsd = flightReplaced * 180;
    const totalAnnualUsd = annualFuelSavedUsd + annualGroceriesSavedUsd + annualElectricitySavedUsd + annualFlightSavedUsd;

    setResults({
      year1Tonnes: totalAnnualSavedTonnes.toFixed(2),
      year5Tonnes: (totalAnnualSavedTonnes * 5).toFixed(1),
      year10Tonnes: (totalAnnualSavedTonnes * 10).toFixed(1),
      year1Usd: Math.round(totalAnnualUsd),
      year5Usd: Math.round(totalAnnualUsd * 5),
      year10Usd: Math.round(totalAnnualUsd * 10)
    });
  }, [transitDays, dietLevel, solarPct, flightReplaced]);

  return (
    <div>
      <div className="modern-card">
        <div className="card-title-row">
          <div className="card-title">🔮 "What-If" Climate & ROI Scenario Simulator</div>
          <span className="brand-badge">Transition Engine</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Simulate multi-year decarbonization pathways. Adjust your lifestyle transition levers below to see projected
          cumulative CO2e abatement and household financial savings ($ USD).
        </p>

        {/* Levers Grid */}
        <div className="grid-2" style={{ marginBottom: '30px' }}>
          <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 700 }}>🚆 Commute Transit Days: {transitDays} days/week</span>
              <span style={{ color: 'var(--primary-light)' }}>Shift solo car to electric train/bus</span>
            </div>
            <input
              type="range"
              min="0"
              max="5"
              step="1"
              value={transitDays}
              onChange={(e) => setTransitDays(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--primary)', height: '8px' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
              <span>0 days (Always drive)</span>
              <span>5 days (Full transit)</span>
            </div>
          </div>

          <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 700 }}>
                🥗 Plant-Rich Dietary Shift:{' '}
                {dietLevel === 0 ? 'Omnivore' : dietLevel === 1 ? 'Flexitarian' : dietLevel === 2 ? 'Vegetarian' : '100% Vegan'}
              </span>
              <span style={{ color: 'var(--accent-cyan)' }}>Poore & Nemecek Model</span>
            </div>
            <input
              type="range"
              min="0"
              max="3"
              step="1"
              value={dietLevel}
              onChange={(e) => setDietLevel(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-cyan)', height: '8px' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
              <span>Omnivore</span>
              <span>Flexitarian</span>
              <span>Vegetarian</span>
              <span>Vegan</span>
            </div>
          </div>

          <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 700 }}>⚡ Clean Renewable Power: {solarPct}%</span>
              <span style={{ color: 'var(--accent-amber)' }}>Rooftop Solar / Green Tariff</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="10"
              value={solarPct}
              onChange={(e) => setSolarPct(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-amber)', height: '8px' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
              <span>0% (Fossil Grid)</span>
              <span>100% (Pure Clean Solar/Wind)</span>
            </div>
          </div>

          <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 700 }}>✈️ Flights Replaced by Rail: {flightReplaced} trips/yr</span>
              <span style={{ color: 'var(--accent-purple)' }}>High-Speed Eurostar/Amtrak</span>
            </div>
            <input
              type="range"
              min="0"
              max="6"
              step="1"
              value={flightReplaced}
              onChange={(e) => setFlightReplaced(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-purple)', height: '8px' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
              <span>0 flights</span>
              <span>6 round-trips</span>
            </div>
          </div>
        </div>

        {/* Results Horizons */}
        {results && (
          <div>
            <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px' }}>
              Decarbonization & Household Financial Projections
            </h3>
            <div className="grid-3">
              <div className="metric-kpi" style={{ borderTop: '4px solid #38bdf8' }}>
                <div className="metric-label">1-Year Horizon</div>
                <div className="metric-value" style={{ color: '#38bdf8' }}>
                  {results.year1Tonnes} <span style={{ fontSize: '18px' }}>tonnes CO2e</span>
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#34d399', marginTop: '6px' }}>
                  +${results.year1Usd} USD saved
                </div>
              </div>

              <div className="metric-kpi" style={{ borderTop: '4px solid #10b981' }}>
                <div className="metric-label">5-Year Cumulative</div>
                <div className="metric-value" style={{ color: '#10b981' }}>
                  {results.year5Tonnes} <span style={{ fontSize: '18px' }}>tonnes CO2e</span>
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#34d399', marginTop: '6px' }}>
                  +${results.year5Usd} USD saved
                </div>
              </div>

              <div className="metric-kpi" style={{ borderTop: '4px solid #c084fc' }}>
                <div className="metric-label">10-Year Cumulative (Net Zero)</div>
                <div className="metric-value" style={{ color: '#c084fc' }}>
                  {results.year10Tonnes} <span style={{ fontSize: '18px' }}>tonnes CO2e</span>
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#34d399', marginTop: '6px' }}>
                  +${results.year10Usd} USD saved
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
