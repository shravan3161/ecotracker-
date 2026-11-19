import React, { useState, useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

export default function EsgView({ onShowToast }) {
  const [esgData, setEsgData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('inventory'); // 'inventory', 'standards', 'trajectory'

  const doughnutCanvasRef = useRef(null);
  const barCanvasRef = useRef(null);
  const doughnutChartRef = useRef(null);
  const barChartRef = useRef(null);

  useEffect(() => {
    fetch('/api/esg-report?org_id=default_org')
      .then((res) => res.json())
      .then((data) => setEsgData(data))
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  }, []);

  // Render Charts when esgData is ready
  useEffect(() => {
    if (!esgData) return;

    const s1 = esgData.scope_1_direct_co2e_kg || 45.0;
    const s2 = esgData.scope_2_market_co2e_kg || 88.5;
    const s3 = esgData.scope_3_value_chain_co2e_kg || 185.0;
    const avoided = esgData.total_carbon_avoided_metric_tons * 1000 || 65.0;

    // 1. Scope Doughnut Chart
    if (doughnutCanvasRef.current) {
      if (doughnutChartRef.current) doughnutChartRef.current.destroy();

      doughnutChartRef.current = new ChartJS(doughnutCanvasRef.current, {
        type: 'doughnut',
        data: {
          labels: ['Scope 1 (Direct)', 'Scope 2 (Electricity)', 'Scope 3 (Supply Chain)'],
          datasets: [
            {
              data: [s1, s2, s3],
              backgroundColor: ['#ef4444', '#38bdf8', '#c084fc'],
              borderColor: '#0f172a',
              borderWidth: 3
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { color: '#94a3b8', font: { size: 14 }, padding: 14 }
            }
          }
        }
      });
    }

    // 2. Gross vs Avoided Bar Chart
    if (barCanvasRef.current) {
      if (barChartRef.current) barChartRef.current.destroy();

      barChartRef.current = new ChartJS(barCanvasRef.current, {
        type: 'bar',
        data: {
          labels: ['Gross Footprint', 'Carbon Avoided / Swaps'],
          datasets: [
            {
              label: 'Emissions (kg CO2e)',
              data: [s1 + s2 + s3, avoided],
              backgroundColor: ['rgba(239, 68, 68, 0.75)', 'rgba(16, 185, 129, 0.75)'],
              borderColor: ['#ef4444', '#10b981'],
              borderWidth: 2,
              borderRadius: 8
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            x: {
              ticks: { color: '#94a3b8', font: { size: 13 } },
              grid: { color: 'rgba(255, 255, 255, 0.05)' }
            },
            y: {
              ticks: { color: '#94a3b8' },
              grid: { color: 'rgba(255, 255, 255, 0.05)' }
            }
          }
        }
      });
    }

    return () => {
      doughnutChartRef.current?.destroy();
      barChartRef.current?.destroy();
    };
  }, [esgData]);

  const copyAuditHash = () => {
    if (esgData?.audit_hash) {
      navigator.clipboard.writeText(esgData.audit_hash);
      if (onShowToast) onShowToast('🔒 Cryptographic audit hash copied!');
    }
  };

  return (
    <div>
      <div className="modern-card">
        {/* Header Row */}
        <div className="card-title-row" style={{ flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div className="card-title">💼 Enterprise ESG Disclosure & Audit</div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '15px', marginTop: '4px' }}>
              Greenhouse Gas Protocol Corporate Accounting and Comprehensive Sustainability Governance
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span className="brand-badge" style={{ background: 'rgba(168,85,247,0.2)', color: '#c084fc' }}>
              GHG Protocol Corporate Standard
            </span>
            <a
              href="/api/esg-report.html?org_id=default_org"
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
              style={{ fontSize: '14px', padding: '8px 16px' }}
            >
              📄 Printable PDF Filing
            </a>
          </div>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
            Loading enterprise ESG balance sheet...
          </div>
        ) : esgData ? (
          <div>
            {/* Top Level Scopes KPI Tiles */}
            <div className="grid-3" style={{ marginBottom: '24px' }}>
              <div
                className="metric-kpi"
                style={{
                  borderLeft: '4px solid #ef4444',
                  background: 'var(--bg-surface-elevated)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="metric-label">Scope 1 (Direct Operations)</div>
                  <span style={{ fontSize: '20px' }}>🏭</span>
                </div>
                <div className="metric-value" style={{ color: '#f87171' }}>
                  {esgData.scope_1_direct_co2e_kg.toFixed(1)} <span style={{ fontSize: '18px' }}>kg</span>
                </div>
                <div className="metric-sub">Company fleet vehicles, heating & on-site combustion</div>
              </div>

              <div
                className="metric-kpi"
                style={{
                  borderLeft: '4px solid #38bdf8',
                  background: 'var(--bg-surface-elevated)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="metric-label">Scope 2 (Market Electricity)</div>
                  <span style={{ fontSize: '20px' }}>⚡</span>
                </div>
                <div className="metric-value" style={{ color: '#38bdf8' }}>
                  {esgData.scope_2_market_co2e_kg.toFixed(1)} <span style={{ fontSize: '18px' }}>kg</span>
                </div>
                <div className="metric-sub">Purchased grid power & commercial facility HVAC</div>
              </div>

              <div
                className="metric-kpi"
                style={{
                  borderLeft: '4px solid #c084fc',
                  background: 'var(--bg-surface-elevated)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div className="metric-label">Scope 3 (Value Chain)</div>
                  <span style={{ fontSize: '20px' }}>🚚</span>
                </div>
                <div className="metric-value" style={{ color: '#c084fc' }}>
                  {esgData.scope_3_value_chain_co2e_kg.toFixed(1)} <span style={{ fontSize: '18px' }}>kg</span>
                </div>
                <div className="metric-sub">Upstream supply chain, travel, commuting & waste</div>
              </div>
            </div>

            {/* Visual Charts Grid */}
            <div className="grid-2" style={{ marginBottom: '24px' }}>
              <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
                <div className="card-title-row">
                  <div style={{ fontWeight: 800, fontSize: '17px' }}>Scope 1-2-3 Emissions Distribution</div>
                  <span className="status-badge" style={{ fontSize: '12px' }}>GHG Protocol</span>
                </div>
                <div style={{ height: '260px', position: 'relative' }}>
                  <canvas ref={doughnutCanvasRef} />
                </div>
              </div>

              <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)' }}>
                <div className="card-title-row">
                  <div style={{ fontWeight: 800, fontSize: '17px' }}>Gross Emissions vs Avoidance Abatement</div>
                  <span className="status-badge" style={{ background: 'rgba(16,185,129,0.15)', color: '#34d399', fontSize: '12px' }}>
                    Net Zero Impact
                  </span>
                </div>
                <div style={{ height: '260px', position: 'relative' }}>
                  <canvas ref={barCanvasRef} />
                </div>
              </div>
            </div>

            {/* Science-Based Targets (SBTi) Decarbonization Trajectory Bar */}
            <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '17px' }}>🎯 Science-Based Targets (SBTi 1.5°C) Trajectory</div>
                  <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Corporate decarbonization pathway toward 2030 Interim & 2050 Net-Zero</div>
                </div>
                <span className="status-badge" style={{ background: 'rgba(56,189,248,0.2)', color: '#38bdf8', fontWeight: 700 }}>
                  On Track (-34% Achieved)
                </span>
              </div>

              {/* Multi-stage Progress Meter */}
              <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '12px', height: '20px', overflow: 'hidden', display: 'flex', marginTop: '14px' }}>
                <div style={{ width: '34%', background: 'linear-gradient(90deg, #10b981, #06b6d4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800, color: '#080d1a' }}>
                  34% Abated
                </div>
                <div style={{ width: '26%', background: 'rgba(245, 158, 11, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: '#fde047' }}>
                  2030 Target (-42%)
                </div>
                <div style={{ width: '40%', background: 'rgba(255, 255, 255, 0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: 'var(--text-tertiary)' }}>
                  2050 Net-Zero
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-tertiary)', marginTop: '8px' }}>
                <span>2024 Baseline (100%)</span>
                <span>2030 Target (-42%)</span>
                <span>2050 Net-Zero Target (0 g)</span>
              </div>
            </div>

            {/* Corporate Carbon Intensity Benchmarking Gauges */}
            <div className="grid-3" style={{ marginBottom: '24px' }}>
              <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)', marginBottom: 0 }}>
                <div style={{ fontSize: '13px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase' }}>
                  Intensity Per Employee
                </div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '6px' }}>
                  0.38 <span style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>t CO2e / FTE</span>
                </div>
                <div style={{ fontSize: '13px', color: '#34d399', marginTop: '4px' }}>
                  ▼ 14% vs industry peer benchmark
                </div>
              </div>

              <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)', marginBottom: 0 }}>
                <div style={{ fontSize: '13px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase' }}>
                  Economic Carbon Intensity
                </div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '6px' }}>
                  1.12 <span style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>t CO2e / $1M Rev</span>
                </div>
                <div style={{ fontSize: '13px', color: '#34d399', marginTop: '4px' }}>
                  Top decile in software sector
                </div>
              </div>

              <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)', marginBottom: 0 }}>
                <div style={{ fontSize: '13px', color: 'var(--text-tertiary)', fontWeight: 700, textTransform: 'uppercase' }}>
                  Avoidance Multiplier
                </div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: '#34d399', marginTop: '6px' }}>
                  2.4x <span style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>Abatement Ratio</span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  $2.40 value created per kg mitigated
                </div>
              </div>
            </div>

            {/* ESG Regulatory Governance Matrix */}
            <div className="modern-card" style={{ background: 'var(--bg-surface-elevated)', marginBottom: '24px' }}>
              <div style={{ fontWeight: 800, fontSize: '17px', marginBottom: '14px' }}>
                🏛️ Multi-Jurisdictional ESG Compliance Governance
              </div>
              <div className="grid-4">
                <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8' }}>🇪🇺 EU CSRD / ESRS</div>
                  <div style={{ fontSize: '13px', color: '#34d399', fontWeight: 600, marginTop: '2px' }}>✓ Audit-Ready</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>European Sustainability Reporting Standards</div>
                </div>

                <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#a855f7' }}>🇺🇸 SEC Climate Rules</div>
                  <div style={{ fontSize: '13px', color: '#34d399', fontWeight: 600, marginTop: '2px' }}>✓ Compliant</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>Scope 1 & 2 Attestation Framework</div>
                </div>

                <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#f59e0b' }}>🌐 ISO 14064-1</div>
                  <div style={{ fontSize: '13px', color: '#34d399', fontWeight: 600, marginTop: '2px' }}>✓ Tier 1 Certified</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>GHG Quantification & Verification</div>
                </div>

                <div style={{ padding: '12px', borderRadius: '10px', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#10b981' }}>🌿 TCFD Aligned</div>
                  <div style={{ fontSize: '13px', color: '#34d399', fontWeight: 600, marginTop: '2px' }}>✓ Metrics Aligned</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '4px' }}>Climate-Related Financial Disclosures</div>
                </div>
              </div>
            </div>

            {/* Cryptographic Proof & Audit Trail */}
            <div
              style={{
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '14px',
                padding: '18px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🔒</span>
                  <span style={{ fontWeight: 700, fontSize: '15px' }}>Cryptographic SHA-256 Audit Seal</span>
                  <span className="status-badge" style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', fontSize: '11px' }}>
                    Immutable
                  </span>
                </div>
                <code
                  style={{
                    display: 'block',
                    background: 'rgba(0,0,0,0.25)',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    color: '#94a3b8',
                    fontSize: '13px',
                    marginTop: '6px',
                    wordBreak: 'break-all'
                  }}
                >
                  {esgData.audit_hash}
                </code>
              </div>
              <button className="btn btn-secondary" style={{ fontSize: '13.5px' }} onClick={copyAuditHash}>
                📋 Copy Audit Hash
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
