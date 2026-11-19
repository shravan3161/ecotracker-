import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MobileNav from './components/MobileNav';
import ChatView from './components/ChatView';
import ScannerView from './components/ScannerView';
import AnalyticsView from './components/AnalyticsView';
import LeaderboardView from './components/LeaderboardView';
import HabitsView from './components/HabitsView';
import SimulatorView from './components/SimulatorView';
import EsgView from './components/EsgView';
import HistoryView from './components/HistoryView';
import OffsetsView from './components/OffsetsView';
import FutureScopeView from './components/FutureScopeView';
import ScorecardModal from './components/ScorecardModal';
import ApiKeyModal from './components/ApiKeyModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [userId, setUserId] = useState(localStorage.getItem('ecotracker_uid') || 'default_customer');
  const [theme, setTheme] = useState(localStorage.getItem('ecotracker_theme') || 'dark');
  const [dashboardData, setDashboardData] = useState(null);
  const [weather, setWeather] = useState(null);
  const [gridStatus, setGridStatus] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isScorecardOpen, setIsScorecardOpen] = useState(false);
  const [isApiKeyOpen, setIsApiKeyOpen] = useState(false);

  // Set HTML root attributes
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-font-scale', 'large');
  }, [theme]);

  // Toast helper (single active toast, fast auto-dismiss, click-to-dismiss)
  const showToast = useCallback((msg) => {
    const id = Date.now();
    setToasts([{ id, msg }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 1800);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Fetch Dashboard Data
  const loadDashboardData = useCallback(async () => {
    try {
      const res = await fetch(`/api/dashboard?user_id=${encodeURIComponent(userId)}`);
      const data = await res.json();
      setDashboardData(data);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    }
  }, [userId]);

  // Fetch Live Power Grid Intensity
  const fetchLiveGridStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/grid-intensity?region=UK');
      const data = await res.json();
      setGridStatus(data);
    } catch (err) {
      console.error('Error fetching grid intensity:', err);
    }
  }, []);

  // Fetch Outdoor Ambient Weather (Open-Meteo)
  const fetchAmbientWeather = useCallback(async () => {
    try {
      const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current_weather=true');
      const data = await res.json();
      if (data.current_weather) {
        const temp = data.current_weather.temperature;
        const condition = temp > 24 ? 'High Cooling HVAC' : temp < 16 ? 'Heating HVAC' : 'Mild HVAC';
        setWeather({ temp, condition });
      }
    } catch (err) {
      setWeather({ temp: 21, condition: 'Mild HVAC' });
    }
  }, []);

  // Initialize
  useEffect(() => {
    loadDashboardData();
    fetchLiveGridStatus();
    fetchAmbientWeather();

    // Register PWA service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }, [loadDashboardData, fetchLiveGridStatus, fetchAmbientWeather]);

  const handleUserChange = (newUid) => {
    const cleaned = newUid.trim() || 'default_customer';
    setUserId(cleaned);
    localStorage.setItem('ecotracker_uid', cleaned);
    showToast(`Switched user: ${cleaned}`);
  };

  const handleToggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('ecotracker_theme', next);
  };

  return (
    <div className="app-container">
      {/* Toast Alert (Single, Auto-Dismiss, Click to Close) */}
      <div className="toast-container">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="toast"
            onClick={() => dismissToast(t.id)}
            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' }}
            title="Click to dismiss"
          >
            <span>{t.msg}</span>
            <span style={{ fontSize: '13px', opacity: 0.6, marginLeft: '6px' }}>✕</span>
          </div>
        ))}
      </div>

      {/* Desktop Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        userId={userId}
        onChangeUserId={handleUserChange}
        onOpenApiKeyModal={() => setIsApiKeyOpen(true)}
        onOpenScorecardModal={() => setIsScorecardOpen(true)}
        historyCount={dashboardData?.recent_logs?.length || 0}
      />

      {/* Main Viewport */}
      <main className="main-viewport">
        <Header
          activeTab={activeTab}
          onOpenMobileMenu={() => setIsDrawerOpen(true)}
          theme={theme}
          onToggleTheme={handleToggleTheme}
        />

        <div className="content-scrollable">
          {activeTab === 'chat' && (
            <ChatView
              userId={userId}
              dashboardData={dashboardData}
              onRefreshDashboard={loadDashboardData}
              onShowToast={showToast}
            />
          )}

          {activeTab === 'scanner' && (
            <ScannerView
              userId={userId}
              onRefreshDashboard={loadDashboardData}
              onShowToast={showToast}
            />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsView
              dashboardData={dashboardData}
              userId={userId}
              weather={weather}
              gridStatus={gridStatus}
              onRefreshGrid={fetchLiveGridStatus}
              onRefreshDashboard={loadDashboardData}
              onShowToast={showToast}
            />
          )}

          {activeTab === 'leaderboard' && <LeaderboardView userId={userId} />}

          {activeTab === 'habits' && (
            <HabitsView
              userId={userId}
              onRefreshDashboard={loadDashboardData}
              onShowToast={showToast}
            />
          )}

          {activeTab === 'simulator' && <SimulatorView />}

          {activeTab === 'esg' && <EsgView onShowToast={showToast} />}

          {activeTab === 'history' && (
            <HistoryView
              dashboardData={dashboardData}
              userId={userId}
              onRefreshDashboard={loadDashboardData}
              onShowToast={showToast}
            />
          )}

          {activeTab === 'offsets' && <OffsetsView onShowToast={showToast} />}

          {activeTab === 'future' && <FutureScopeView />}
        </div>
      </main>

      {/* Mobile Navigation & Drawer */}
      <MobileNav
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isDrawerOpen={isDrawerOpen}
        onCloseDrawer={() => setIsDrawerOpen(false)}
        userId={userId}
        onChangeUserId={handleUserChange}
        onOpenApiKeyModal={() => setIsApiKeyOpen(true)}
        onOpenScorecardModal={() => setIsScorecardOpen(true)}
      />

      {/* Modals */}
      <ScorecardModal
        isOpen={isScorecardOpen}
        onClose={() => setIsScorecardOpen(false)}
        dashboardData={dashboardData}
        userId={userId}
        onShowToast={showToast}
      />

      <ApiKeyModal
        isOpen={isApiKeyOpen}
        onClose={() => setIsApiKeyOpen(false)}
        onShowToast={showToast}
      />
    </div>
  );
}
