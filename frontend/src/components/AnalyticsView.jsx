import React, { useState, useEffect, useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function AnalyticsView({ dashboardData, userId, onRefreshDashboard, onShowToast }) {
  const [budgetSlider, setBudgetSlider] = useState(dashboardData?.daily_budget_kg || 15);
  const [dailyTrends, setDailyTrends] = useState([]);
  const trendChartRef = useRef(null);
  const doughnutChartRef = useRef(null);
  const trendCanvasRef = useRef(null);
  const doughnutCanvasRef = useRef(null);

  useEffect(() => {
    if (dashboardData?.daily_budget_kg) {
      setBudgetSlider(dashboardData.daily_budget_kg);
    }
  }, [dashboardData?.daily_budget_kg]);

  // Fetch 30-day trends
  useEffect(() => {
    fetch(`/api/daily-trends?user_id=${encodeURIComponent(userId)}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.trends) {
          setDailyTrends(data.trends);
        }
      })
      .catch((err) => console.error(err));
  }, [userId]);

  // Render Charts
  useEffect(() => {
    // 1. Trend Line Chart
    if (trendCanvasRef.current && dailyTrends.length > 0) {
      if (trendChartRef.current) {
        trendChartRef.current.destroy();
      }

      const labels = dailyTrends.map((d) => d.day.slice(5));
      const emissionsData = dailyTrends.map((d) => d.emissions_kg);
      const savingsData = dailyTrends.map((d) => d.saved_kg);

      trendChartRef.current = new ChartJS(trendCanvasRef.current, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Gross Emissions (kg)',
              data: emissionsData,
              borderColor: '#f87171',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              fill: true,
              tension: 0.35,
              pointRadius: 3
            },
            {
              label: 'Carbon Avoided (kg)',
              data: savingsData,
              borderColor: '#34d399',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              fill: true,
              tension: 0.35,
              pointRadius: 3
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: { color: '#94a3b8', font: { size: 14 } }
            }
          },
          scales: {
            x: {
              ticks: { color: '#64748b' },
              grid: { color: 'rgba(255, 255, 255, 0.05)' }
            },
            y: {
              ticks: { color: '#64748b' },
              grid: { color: 'rgba(255, 255, 255, 0.05)' }
            }
          }
        }
      });
    }

    // 2. Category Doughnut Chart
    if (doughnutCanvasRef.current && dashboardData?.category_breakdown) {
      if (doughnutChartRef.current) {
        doughnutChartRef.current.destroy();
      }

      const cats = dashboardData.category_breakdown;
      const catLabels = Object.keys(cats).map((k) => k.charAt(0).toUpperCase() + k.slice(1));
      const catValues = Object.values(cats);

      doughnutChartRef.current = new ChartJS(doughnutCanvasRef.current, {
        type: 'doughnut',
        data: {
          labels: catLabels.length > 0 ? catLabels : ['No Data'],
          datasets: [
            {
              data: catValues.length > 0 ? catValues : [1],
              backgroundColor: ['#10b981', '#06b6d4', '#a855f7', '#f59e0b', '#ef4444', '#64748b'],
              borderWidth: 2,
              borderColor: '#0f172a'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { color: '#94a3b8', font: { size: 14 }, padding: 16 }
            }
          }
        }
      });
    }

    return () => {
      trendChartRef.current?.destroy();
      doughnutChartRef.current?.destroy();
    };
  }, [dailyTrends, dashboardData?.category_breakdown]);

  const handleBudgetChange = (newVal) => {
    setBudgetSlider(newVal);
  };

  const commitBudgetChange = async (newVal) => {
    try {
      await fetch('/api/budget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, daily_budget_kg: parseFloat(newVal) })
      });
      onShowToast(`🎯 Daily budget updated: ${newVal} kg/day`);
      onRefreshDashboard();
    } catch (err) {
      console.error(err);
    }
  };

  const summary = dashboardData?.summary || {};
  const todayEmissions = summary.today_emissions_kg || 0;
  const budgetRatio = budgetSlider > 0 ? ((todayEmissions / budgetSlider) * 100).toFixed(0) : 0;

  return (
    <div>
      {/* 4 KPI Metric Cards */}
      <div className="grid-4" style={{ marginBottom: '24px' }}>
        <div className="metric-kpi">
          <div className="metric-label">Lifetime Gross Emissions</div>
          <div className="metric-value" style={{ color: '#f87171' }}>
            {summary.total_co2e_kg ? summary.total_co2e_kg.toFixed(1) : '0.0'}{' '}
            <span style={{ fontSize: '18px' }}>kg</span>
          </div>
          <div className="metric-sub">{summary.total_activities || 0} total logged activities</div>
        </div>

        <div className="metric-kpi">
          <div className="metric-label">Total Carbon Avoided</div>
          <div className="metric-value" style={{ color: '#34d399' }}>
            +{summary.total_saved_co2e_kg ? summary.total_saved_co2e_kg.toFixed(1) : '0.0'}{' '}
            <span style={{ fontSize: '18px' }}>kg</span>
          </div>
          <div className="metric-sub">From conscious eco-swaps</div>
        </div>

        <div className="metric-kpi">
          <div className="metric-label">Today's Budget Usage</div>
          <div className="metric-value" style={{ color: budgetRatio >= 100 ? '#ef4444' : '#38bdf8' }}>
            {todayEmissions.toFixed(1)}{' '}
            <span style={{ fontSize: '18px' }}>/ {budgetSlider} kg</span>
          </div>
          <div className="metric-sub">{budgetRatio}% of daily target</div>
        </div>

        <div className="metric-kpi">
          <div className="metric-label">Achievements Unlocked</div>
          <div className="metric-value" style={{ color: '#c084fc' }}>
            {dashboardData?.badges?.length || 0} <span style={{ fontSize: '18px' }}>🏅</span>
          </div>
          <div className="metric-sub">
            {dashboardData?.badges?.map((b) => b.name).join(', ') || 'Keep logging to unlock'}
          </div>
        </div>
      </div>

      {/* Dual Charts Grid */}
      <div className="grid-2">
        <div className="modern-card">
          <div className="card-title-row">
            <div className="card-title">📈 30-Day Daily Carbon Trends</div>
            <span className="brand-badge">Time-Series</span>
          </div>
          <div style={{ height: '300px', position: 'relative' }}>
            <canvas ref={trendCanvasRef} />
          </div>
        </div>

        <div className="modern-card">
          <div className="card-title-row">
            <div className="card-title">🥧 Emissions by Category</div>
            <span className="brand-badge">EPA & DEFRA</span>
          </div>
          <div style={{ height: '300px', position: 'relative' }}>
            <canvas ref={doughnutCanvasRef} />
          </div>
        </div>
      </div>

      {/* Daily Budget Target Card */}
      <div className="modern-card">
        <div className="card-title-row">
          <div className="card-title">🎯 Daily Carbon Budget Target</div>
          <span style={{ fontSize: '20px', fontWeight: 800, color: 'var(--primary-light)' }}>
            {budgetSlider} kg CO2e / day
          </span>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Align your lifestyle emissions with the Paris Agreement target (~5 to 15 kg CO2e/day per capita).
          Real-time alerts appear when approaching 80% or 100% capacity.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>5 kg</span>
          <input
            type="range"
            min="2"
            max="40"
            step="1"
            value={budgetSlider}
            onChange={(e) => handleBudgetChange(e.target.value)}
            onPointerUp={(e) => commitBudgetChange(e.target.value)}
            onKeyUp={(e) => commitBudgetChange(e.target.value)}
            style={{ flex: 1, accentColor: 'var(--primary)', height: '8px', cursor: 'pointer' }}
          />
          <span style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>40 kg</span>
        </div>
      </div>
    </div>
  );
}
