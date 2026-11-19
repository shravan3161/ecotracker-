import React, { useState } from 'react';

export default function HistoryView({ dashboardData, userId, onRefreshDashboard, onShowToast }) {
  const [searchTerm, setSearchTerm] = useState('');

  const logs = dashboardData?.recent_logs || [];
  const filtered = logs.filter(
    (r) =>
      r.activity_details.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const deleteRow = async (logId) => {
    try {
      await fetch('/api/delete-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log_id: logId, user_id: userId })
      });
      onShowToast(`Deleted record #${logId}`);
      onRefreshDashboard();
    } catch (err) {
      console.error(err);
      onShowToast('⚠️ Error deleting log entry.');
    }
  };

  const clearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all your logged activities?')) return;
    try {
      await fetch('/api/clear-logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      onShowToast('All activity records wiped.');
      onRefreshDashboard();
    } catch (err) {
      console.error(err);
      onShowToast('⚠️ Error clearing logs.');
    }
  };

  return (
    <div className="modern-card">
      <div className="card-title-row">
        <div className="card-title">📋 Activity History & Audit Ledger</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <a
            href={`/api/export-csv?user_id=${encodeURIComponent(userId)}`}
            download="ecotracker_activities.csv"
            className="btn btn-secondary"
            style={{ fontSize: '14px' }}
          >
            📥 Export CSV
          </a>
          <button className="btn btn-danger" style={{ fontSize: '14px' }} onClick={clearAll}>
            🗑️ Clear All
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          className="form-input"
          placeholder="Search activity description or category..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="modern-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Scope</th>
              <th>Category</th>
              <th>Activity Description</th>
              <th>Emissions</th>
              <th>Savings</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? (
              filtered.map((r) => (
                <tr key={r.id}>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {r.timestamp ? r.timestamp.slice(0, 10) : 'Recent'}
                  </td>
                  <td>
                    <span
                      className="status-badge"
                      style={{ background: 'rgba(255,255,255,0.06)', fontSize: '13.5px' }}
                    >
                      {r.scope || 'Scope 3'}
                    </span>
                  </td>
                  <td style={{ textTransform: 'capitalize', fontWeight: 600 }}>{r.category}</td>
                  <td>{r.activity_details}</td>
                  <td style={{ fontWeight: 700, color: '#f87171' }}>{r.co2e_kg} kg</td>
                  <td style={{ fontWeight: 700, color: '#34d399' }}>+{r.saved_co2e_kg} kg</td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '14px' }}
                      onClick={() => deleteRow(r.id)}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '30px' }}>
                  No activities recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
