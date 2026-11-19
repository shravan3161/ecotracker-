import React from 'react';
import confetti from 'canvas-confetti';

export default function HabitsView({ userId, onRefreshDashboard, onShowToast }) {
  const habits = [
    {
      id: 'oat_latte',
      icon: '☕',
      title: 'Plant-Milk Oat Latte',
      category: 'diet',
      desc: 'Substituted dairy cow milk with oat milk in morning coffee',
      savedKg: 0.28,
      co2eKg: 0.12
    },
    {
      id: 'train_commute',
      icon: '🚆',
      title: 'Electric Train Commute (25 km)',
      category: 'transit',
      desc: 'Took the high-efficiency electric commuter rail instead of solo car',
      savedKg: 4.80,
      co2eKg: 0.88
    },
    {
      id: 'vegan_lunch',
      icon: '🥗',
      title: 'Mediterranean Vegan Lunch',
      category: 'diet',
      desc: 'Chose a chickpea, quinoa, and avocado bowl over beef brisket',
      savedKg: 2.45,
      co2eKg: 0.55
    },
    {
      id: 'bicycle_trip',
      icon: '🚲',
      title: '8 km Bicycle Trip',
      category: 'transit',
      desc: 'Replaced a short city errand drive with pedal power (0 g emissions)',
      savedKg: 1.54,
      co2eKg: 0.00
    },
    {
      id: 'ac_eco_mode',
      icon: '❄️',
      title: 'AC Eco Temperature Set (24°C)',
      category: 'appliances',
      desc: 'Smart thermostat modulation saving 1.2 kWh of grid electricity',
      savedKg: 0.52,
      co2eKg: 0.38
    },
    {
      id: 'cold_wash',
      icon: '🧺',
      title: 'Cold Water Laundry Cycle',
      category: 'appliances',
      desc: 'Washed full load at 30°C instead of 60°C water heating',
      savedKg: 0.65,
      co2eKg: 0.18
    }
  ];

  const logHabit = async (habit) => {
    // Fire festive confetti
    confetti({
      particleCount: 60,
      spread: 70,
      origin: { y: 0.75 }
    });

    try {
      const res = await fetch('/api/log-preset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: habit.category,
          activity_details: habit.title,
          co2e_kg: habit.co2eKg,
          saved_co2e_kg: habit.savedKg,
          user_id: userId
        })
      });
      const data = await res.json();
      onShowToast(`🎉 Logged: ${habit.title} (+${habit.savedKg} kg saved!)`);
      onRefreshDashboard();
    } catch (err) {
      console.error(err);
      onShowToast('⚠️ Error logging habit preset.');
    }
  };

  return (
    <div>
      <div className="modern-card">
        <div className="card-title-row">
          <div className="card-title">⚡ Eco Habits Studio</div>
          <span className="brand-badge">1-Click Quick Log</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Form lasting sustainable habits. Tap any eco-habit below to instantly log verified carbon abatement to your
          personal and team sustainability ledger.
        </p>

        <div className="grid-3">
          {habits.map((h) => (
            <div
              key={h.id}
              className="modern-card"
              style={{
                marginBottom: 0,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-surface-elevated)',
                cursor: 'pointer',
                transition: 'transform 0.15s ease, border-color 0.15s ease'
              }}
              onClick={() => logHabit(h)}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--primary)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <div>
                <div style={{ fontSize: '36px', marginBottom: '12px' }}>{h.icon}</div>
                <div style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>{h.title}</div>
                <p style={{ fontSize: '15px', color: 'var(--text-secondary)', marginBottom: '16px' }}>{h.desc}</p>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '12px'
                }}
              >
                <span style={{ fontSize: '14px', color: '#f87171' }}>Emits: {h.co2eKg} kg</span>
                <span
                  className="status-badge"
                  style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', fontWeight: 700 }}
                >
                  +{h.savedKg} kg Saved
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
