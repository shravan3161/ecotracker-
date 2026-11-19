import React, { useState, useEffect } from 'react';

export default function EsgView() {
  const [esgData, setEsgData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('/api/esg-report?org_id=default_org')
      .then((res) => res.json())
      .then((data) => setEsgData(data))
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div>
      <div className="modern-card">
        <div className="card-title-row">
          <div className="card-title">💼 Enterprise ESG Disclosure & Audit</div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span className="brand-badge" style={{ background: 'rgba(168,85,247,0.2)', color: '#c084fc' }}>
              GHG Protocol Corporate Standard
            </span>
            <a
              href="/api/esg-report.html?org_id=default_org"
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
              style={{ fontSize: '13.5px', padding: '6px 14px' }}
            >
              📄 Printable Report
            </a>
          </div>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Certified greenhouse gas inventory formatted for sustainability disclosure filings (CSRD, SEC Climate, TCFD).
          Includes cryptographic audit verification hashes.
        </p>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
            Loading ESG disclosure metrics...
          </div>
        ) : esgData ? (
          <div>
            <div className="grid-3" style={{ marginBottom: '24px' }}>
              <div className="metric-kpi" style={{ borderLeft: '4px solid #ef4444' }}>
                <div className="metric-label">Scope 1 (Direct Emissions)</div>
                <div className="metric-value" style={{ color: '#f87171' }}>
                  {esgData.scope_1_direct_co2e_kg.toFixed(1)} <span style={{ fontSize: '18px' }}>kg</span>
                </div>
                <div className="metric-sub">Company fleet vehicles & on-site natural gas</div>
              </div>

              <div className="metric-kpi" style={{ borderLeft: '4px solid #38bdf8' }}>
                <div className="metric-label">Scope 2 (Market Electricity)</div>
                <div className="metric-value" style={{ color: '#38bdf8' }}>
                  {esgData.scope_2_market_co2e_kg.toFixed(1)} <span style={{ fontSize: '18px' }}>kg</span>
                </div>
                <div className="metric-sub">Purchased facility power & HVAC cooling</div>
              </div>

              <div className="metric-kpi" style={{ borderLeft: '4px solid #a855f7' }}>
                <div className="metric-label">Scope 3 (Value Chain)</div>
                <div className="metric-value" style={{ color: '#c084fc' }}>
                  {esgData.scope_3_value_chain_co2e_kg.toFixed(1)} <span style={{ fontSize: '18px' }}>kg</span>
                </div>
                <div className="metric-sub">Business travel, commuter transit & logistics</div>
              </div>
            </div>

            <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontWeight: 700 }}>Total Gross Carbon Inventory</span>
                <span style={{ fontSize: '24px', fontWeight: 800, color: '#f87171' }}>
                  {esgData.total_gross_emissions_metric_tons.toFixed(3)} Metric Tonnes CO2e
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <span style={{ fontWeight: 700 }}>Total Verified Offsets / Avoidance</span>
                <span style={{ fontSize: '20px', fontWeight: 700, color: '#34d399' }}>
                  +{esgData.total_carbon_avoided_metric_tons.toFixed(3)} Metric Tonnes
                </span>
              </div>

              <div
                style={{
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '13.5px',
                  color: 'var(--text-tertiary)'
                }}
              >
                <span>🔒 Cryptographic Audit Hash:</span>
                <code
                  style={{
                    background: 'rgba(255,255,255,0.06)',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    color: '#94a3b8'
                  }}
                >
                  {esgData.audit_hash}
                </code>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
