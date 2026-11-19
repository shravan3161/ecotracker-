import React, { useState, useEffect } from 'react';

export default function LeaderboardView({ userId }) {
  const [leaderboard, setLeaderboard] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('/api/leaderboard')
      .then((res) => res.json())
      .then((data) => {
        if (data.leaderboard) {
          setLeaderboard(data.leaderboard);
        }
      })
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="modern-card">
      <div className="card-title-row">
        <div className="card-title">🏆 Community & Team Sustainability Leaderboard</div>
        <span className="brand-badge">Live Rankings</span>
      </div>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
        Celebrating top sustainability champions based on cumulative carbon avoided through conscious green swaps and
        consistent low-carbon habits.
      </p>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
          Loading community rankings...
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="modern-table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>Rank</th>
                <th>Eco Champion</th>
                <th>Activities</th>
                <th>Carbon Avoided</th>
                <th>Gross Footprint</th>
                <th style={{ textAlign: 'right' }}>Badges</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((item, idx) => {
                const rankClass = idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : idx === 2 ? 'rank-3' : 'rank-other';
                const isCurrent = item.user_id === userId;

                return (
                  <tr
                    key={item.user_id}
                    style={{
                      background: isCurrent ? 'rgba(16, 185, 129, 0.12)' : 'transparent',
                      fontWeight: isCurrent ? 700 : 500
                    }}
                  >
                    <td>
                      <span className={`rank-badge ${rankClass}`}>{idx + 1}</span>
                    </td>
                    <td>
                      <span style={{ fontSize: '16px' }}>{item.user_id}</span>{' '}
                      {isCurrent && (
                        <span
                          className="status-badge"
                          style={{
                            background: 'rgba(16, 185, 129, 0.2)',
                            color: '#34d399',
                            fontSize: '12px',
                            marginLeft: '6px'
                          }}
                        >
                          You
                        </span>
                      )}
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{item.total_activities} logged</td>
                    <td style={{ color: '#34d399', fontWeight: 700 }}>+{item.total_saved_kg} kg</td>
                    <td style={{ color: '#f87171' }}>{item.total_emissions_kg} kg</td>
                    <td style={{ textAlign: 'right', color: '#c084fc', fontWeight: 700 }}>
                      {item.badge_count} 🏅
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
