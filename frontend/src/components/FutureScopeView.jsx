import React from 'react';

export default function FutureScopeView() {
  const roadmapItems = [
    {
      quarter: 'Q1 - Q2 2027',
      status: 'In Architecture Review',
      statusColor: '#60a5fa',
      statusBg: 'rgba(59, 130, 246, 0.15)',
      icon: '🔌',
      title: 'IoT & Smart Home Telemetry Ingestion',
      subtitle: 'Matter, MQTT & Zigbee Smart Plug Protocols',
      description:
        'Direct automated telemetry integration with smart plugs (Shelly, TP-Link Kasa) and smart thermostats (Google Nest, Ecobee). Eliminates manual activity entry by continuously streaming true kilowatt-hour consumption directly into the FastMCP appliance toolset.',
      benefits: ['Zero manual input required', 'Real-time HVAC wattage monitoring', 'Sub-second anomaly load detection']
    },
    {
      quarter: 'Q2 - Q3 2027',
      status: 'Prototype Stage',
      statusColor: '#34d399',
      statusBg: 'rgba(16, 185, 129, 0.15)',
      icon: '💳',
      title: 'Open Banking & Green Fintech Footprinting',
      subtitle: 'Plaid, Yapily & Stripe Financial Connections',
      description:
        'Secure read-only open banking aggregation connecting to user credit and debit cards. Uses Merchant Category Codes (MCCs) paired with EPA economic input-output (USEEIO) tables to calculate real-time emissions from grocery purchases, fuel fill-ups, and flight bookings.',
      benefits: ['Instant transactional carbon auditing', 'Automated recurring bill accounting', 'Bank-grade OAuth 2.0 encryption']
    },
    {
      quarter: 'Q3 2027',
      status: 'Research & Design',
      statusColor: '#fbbf24',
      statusBg: 'rgba(245, 158, 11, 0.15)',
      icon: '🤖',
      title: 'Autonomous Agent-to-Agent (A2A) Microgrid Auctions',
      subtitle: 'Decentralized Smart EV Load Negotiation',
      description:
        'Expanding Google ADK 2.0 into autonomous Agent-to-Agent (A2A) negotiation. Home energy agents communicate with local solar microgrids and grid operators to dynamically schedule EV charging and battery discharge during surplus renewable generation windows.',
      benefits: ['Financial arbitrage on dynamic energy tariffs', 'Zero-curtailment clean energy utilization', 'Grid-stabilizing demand response']
    },
    {
      quarter: 'Q4 2027',
      status: 'Concept Phase',
      statusColor: '#c084fc',
      statusBg: 'rgba(168, 85, 247, 0.15)',
      icon: '⛓️',
      title: 'Decentralized Carbon Credit Verification & On-Chain Audit',
      subtitle: 'Hedera Guardian, Toucan & Verra Smart Registries',
      description:
        'Cryptographically auditable on-chain carbon retirement records. Every offset purchased or habit logged mints an immutable, double-counting-proof certificate on eco-friendly distributed ledgers, ensuring complete corporate ESG audit transparency.',
      benefits: ['100% immune to greenwashing & double counting', 'Cryptographically verifiable certificates', 'Full CSRD & SEC Climate compliance']
    },
    {
      quarter: 'H1 2028',
      status: 'Planned',
      statusColor: '#f87171',
      statusBg: 'rgba(239, 68, 68, 0.15)',
      icon: '📱',
      title: 'Native Mobile Apps with Passive GPS Transit Detection',
      subtitle: 'React Native & Expo Geofencing Engine',
      description:
        'Transitioning the Progressive Web App (PWA) into native iOS and Android binaries featuring battery-optimized background geofencing and accelerometer sensor fusion to automatically detect when a user rides a bicycle, boards a train, or drives a car.',
      benefits: ['Fully automated transit classification', 'No manual journey logging', 'Push notifications for low-carbon travel alerts']
    },
    {
      quarter: 'H2 2028',
      status: 'Planned',
      statusColor: '#38bdf8',
      statusBg: 'rgba(56, 189, 248, 0.15)',
      icon: '🏢',
      title: 'Enterprise Scope 3 Supply Chain Ingestion Portal',
      subtitle: 'Multi-Tenant B2B Supplier Integration',
      description:
        'Enterprise multi-tenant portal allowing corporations to invite upstream suppliers to complete automated carbon audits. Ingests supplier EDI invoices, computes supply-chain embodied carbon, and generates consolidated GHG Protocol compliance filings.',
      benefits: ['End-to-end supply chain visibility', 'Automated Scope 3 supplier data ingestion', '1-click export for CSRD & SEC filings']
    }
  ];

  return (
    <div>
      <div className="modern-card">
        <div className="card-title-row">
          <div className="card-title">🚀 Strategic Roadmap & Future Scope</div>
          <span className="brand-badge" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa' }}>
            2027 - 2028 Roadmap
          </span>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '28px', fontSize: '16px', lineHeight: '1.6' }}>
          EcoTracker is architected as an extensible, enterprise-ready carbon intelligence platform. Below is the
          strategic engineering and product roadmap designed to transition EcoTracker from a conversational advisor into
          a ubiquitous, autonomous sustainability operating system.
        </p>

        <div className="grid-2">
          {roadmapItems.map((item, idx) => (
            <div
              key={idx}
              className="modern-card"
              style={{
                marginBottom: 0,
                background: 'var(--bg-surface-elevated)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                border: '1px solid var(--border-subtle)',
                transition: 'transform 0.18s ease, border-color 0.18s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = item.statusColor;
                e.currentTarget.style.transform = 'translateY(-3px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-tertiary)' }}>{item.quarter}</span>
                  <span
                    className="status-badge"
                    style={{ background: item.statusBg, color: item.statusColor, fontSize: '13px' }}
                  >
                    {item.status}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '32px' }}>{item.icon}</span>
                  <div>
                    <h3 style={{ fontSize: '19px', fontWeight: 800 }}>{item.title}</h3>
                    <p style={{ fontSize: '14px', color: item.statusColor, fontWeight: 600 }}>{item.subtitle}</p>
                  </div>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: '15px', lineHeight: '1.6', marginBottom: '16px' }}>
                  {item.description}
                </p>
              </div>

              <div
                style={{
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                  Key Capabilities:
                </div>
                {item.benefits.map((b, bIdx) => (
                  <div key={bIdx} style={{ fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color: item.statusColor }}>✓</span>
                    <span>{b}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
