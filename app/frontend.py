# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""EcoTracker Next-Gen Accessible, High-Legibility, Ultra-Responsive Platform.

Features:
- Scaled-Up, High-Legibility Typography (16px base, 15.5px chat, 13.5px+ meta labels)
- Accessibility Font Size Adjuster (Normal / Large / Extra Large)
- Hands-Free Speech-to-Text Voice Dictation (Web Speech API)
- Progressive Web App (PWA) Installable with Offline Caching
- 30-Day Daily Emissions Trend Line Chart (Chart.js)
- Gamified Team & Community Leaderboard
- Proactive 80% and 100% Daily Carbon Budget Threshold Alerts
- Ambient Weather Context (Open-Meteo API) for contextual HVAC load estimation
- Native Mobile Camera Snap for Receipt & Utility Bill OCR
- 1-Click Shareable Eco Scorecard Card Generator
"""

def get_dashboard_html() -> str:
    return r"""<!DOCTYPE html>
<html lang="en" data-theme="dark" data-font-scale="large">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no">
    <title>EcoTracker — AI Sustainability Intelligence Platform</title>
    <meta name="description" content="Autonomous enterprise-grade AI carbon intelligence platform. Calculate footprints, scan receipts, simulate climate ROI, and generate ESG disclosures.">
    <meta name="theme-color" content="#080d1a">
    <link rel="manifest" href="/manifest.json">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked@9.1.2/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.0/dist/confetti.browser.min.js"></script>
    <style>
        :root {
            --primary: #10b981;
            --primary-light: #34d399;
            --primary-dark: #059669;
            --primary-glow: rgba(16, 185, 129, 0.28);
            --accent-cyan: #06b6d4;
            --accent-purple: #a855f7;
            --accent-amber: #f59e0b;
            --danger: #ef4444;
            --danger-bg: rgba(239, 68, 68, 0.15);

            /* High-Legibility Large Typography Base (Default Everywhere) */
            --font-base: 18px;
            --font-sm: 15px;
            --font-md: 17px;
            --font-lg: 20px;
            --font-xl: 25px;
            --font-xxl: 32px;
            --line-height-base: 1.6;

            /* Dark Theme Tokens */
            --bg-base: #080d1a;
            --bg-surface: #0f172a;
            --bg-surface-elevated: #1e293b;
            --bg-card: rgba(15, 23, 42, 0.88);
            --border-subtle: rgba(255, 255, 255, 0.10);
            --border-hover: rgba(255, 255, 255, 0.20);
            --border-active: rgba(16, 185, 129, 0.5);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-tertiary: #64748b;
            --sidebar-width: 280px;
            --bottom-nav-height: 68px;
            --top-bar-height: 64px;
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 18px;
            --radius-full: 9999px;
            --shadow-card: 0 4px 24px -2px rgba(0, 0, 0, 0.35);
        }

        /* Large Font Mode (Permanent Default Everywhere) */
        [data-font-scale="large"],
        :root {
            --font-base: 18px;
            --font-sm: 15px;
            --font-md: 17px;
            --font-lg: 20px;
            --font-xl: 25px;
            --font-xxl: 32px;
        }

        [data-theme="light"] {
            --bg-base: #f8fafc;
            --bg-surface: #ffffff;
            --bg-surface-elevated: #f1f5f9;
            --bg-card: rgba(255, 255, 255, 0.95);
            --border-subtle: rgba(0, 0, 0, 0.09);
            --border-hover: rgba(0, 0, 0, 0.16);
            --border-active: rgba(16, 185, 129, 0.6);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-tertiary: #94a3b8;
            --shadow-card: 0 4px 20px -2px rgba(0, 0, 0, 0.08);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        html, body {
            height: 100%;
            height: 100dvh;
            background: var(--bg-base);
            color: var(--text-primary);
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
            overflow: hidden;
            font-size: var(--font-base);
            line-height: var(--line-height-base);
        }

        /* Ambient Lighting */
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 15% 15%, rgba(16, 185, 129, 0.09) 0%, transparent 45%),
                        radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.08) 0%, transparent 45%);
            pointer-events: none;
            z-index: 0;
        }

        .app-container {
            display: flex;
            width: 100vw;
            height: 100dvh;
            position: relative;
            z-index: 1;
        }

        /* Desktop Sidebar Navigation */
        aside.desktop-sidebar {
            width: var(--sidebar-width);
            background: var(--bg-surface);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 22px 18px;
            flex-shrink: 0;
            overflow-y: auto;
            z-index: 20;
        }

        .brand-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding: 0 6px;
        }
        .brand-logo {
            width: 42px; height: 42px;
            border-radius: var(--radius-md);
            background: linear-gradient(135deg, rgba(16,185,129,0.3), rgba(6,182,212,0.3));
            border: 1px solid rgba(16,185,129,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 16px var(--primary-glow);
        }
        .brand-title {
            font-size: var(--font-lg);
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, var(--text-primary) 40%, var(--primary-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-badge {
            font-size: 13px;
            font-weight: 800;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(16, 185, 129, 0.2);
            color: var(--primary-light);
            margin-left: 6px;
        }

        /* Nav List */
        .nav-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
            list-style: none;
        }
        .nav-button {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 11px 14px;
            border-radius: var(--radius-md);
            border: 1px solid transparent;
            background: transparent;
            color: var(--text-secondary);
            font-size: var(--font-md);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.18s ease;
        }
        .nav-button:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }
        .nav-button.active {
            background: rgba(16, 185, 129, 0.15);
            border-color: rgba(16, 185, 129, 0.38);
            color: var(--primary-light);
        }
        .nav-button .nav-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .nav-pill {
            font-size: 13px;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 700;
        }

        /* Customer Session in Sidebar */
        .sidebar-footer {
            border-top: 1px solid var(--border-subtle);
            padding-top: 16px;
            margin-top: 12px;
        }
        .customer-pill {
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            padding: 10px 14px;
            border-radius: var(--radius-sm);
            margin-bottom: 10px;
        }
        .customer-pill input {
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: var(--font-sm);
            font-weight: 600;
            outline: none;
            width: 100%;
        }

        /* Main Viewport */
        main.main-viewport {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100dvh;
            overflow: hidden;
            position: relative;
        }

        /* Header */
        header.top-header {
            height: var(--top-bar-height);
            border-bottom: 1px solid var(--border-subtle);
            background: var(--bg-surface);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            flex-shrink: 0;
            z-index: 10;
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .mobile-menu-trigger {
            display: none;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 24px;
            cursor: pointer;
            padding: 6px;
        }
        .header-title-box h2 {
            font-size: var(--font-lg);
            font-weight: 800;
            letter-spacing: -0.01em;
            color: var(--text-primary);
        }
        .header-title-box p {
            font-size: var(--font-sm);
            color: var(--text-secondary);
            display: none;
        }
        @media (min-width: 768px) {
            .header-title-box p { display: block; }
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-badge {
            font-size: var(--font-sm);
            font-weight: 700;
            padding: 6px 12px;
            border-radius: var(--radius-full);
            display: inline-flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
            cursor: pointer;
        }
        .theme-toggle-btn {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: var(--font-sm);
            font-weight: 700;
            gap: 6px;
            transition: all 0.2s;
        }
        .theme-toggle-btn:hover {
            border-color: var(--border-hover);
        }

        /* Scrollable Canvas */
        .content-scrollable {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            -webkit-overflow-scrolling: touch;
            padding-bottom: calc(var(--bottom-nav-height) + 24px);
        }
        @media (min-width: 1024px) {
            .content-scrollable {
                padding: 32px 42px;
                padding-bottom: 32px;
            }
        }

        .view-panel {
            display: none;
            max-width: 1200px;
            margin: 0 auto;
            animation: fadeIn 0.18s ease-out;
        }
        .view-panel.active {
            display: block;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Glass Cards */
        .glass-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            padding: 24px;
            box-shadow: var(--shadow-card);
            margin-bottom: 20px;
        }

        /* Button Kit */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 18px;
            border-radius: var(--radius-sm);
            font-size: var(--font-sm);
            font-weight: 700;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.15s ease;
            text-decoration: none;
            white-space: nowrap;
        }
        .btn-primary {
            background: var(--primary);
            color: #042f2e;
            box-shadow: 0 2px 10px var(--primary-glow);
        }
        .btn-primary:hover {
            background: var(--primary-light);
        }
        .btn-secondary {
            background: var(--bg-surface-elevated);
            color: var(--text-primary);
            border-color: var(--border-subtle);
        }
        .btn-secondary:hover {
            border-color: var(--border-hover);
        }
        .btn-danger {
            background: var(--danger-bg);
            color: var(--danger);
            border-color: rgba(239, 68, 68, 0.3);
        }
        .btn-cyan {
            background: rgba(6, 182, 212, 0.15);
            color: #38bdf8;
            border-color: rgba(6, 182, 212, 0.35);
        }

        /* VIEW 1: AI Chat */
        .chat-layout {
            display: flex;
            flex-direction: column;
            height: calc(100dvh - var(--top-bar-height) - 48px);
            max-width: 920px;
            margin: 0 auto;
        }
        @media (max-width: 1023px) {
            .chat-layout {
                height: calc(100dvh - var(--top-bar-height) - var(--bottom-nav-height) - 12px);
            }
        }
        .chat-message-feed {
            flex: 1;
            overflow-y: auto;
            padding-right: 8px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            -webkit-overflow-scrolling: touch;
        }
        .chat-row {
            display: flex;
            gap: 12px;
            max-width: 90%;
            animation: fadeIn 0.2s ease-out;
        }
        .chat-row.user-row {
            align-self: flex-end;
            flex-direction: row-reverse;
        }
        .chat-avatar {
            width: 38px; height: 38px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }
        .avatar-bot {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(6, 182, 212, 0.25));
            border: 1px solid rgba(16, 185, 129, 0.4);
        }
        .avatar-user {
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            color: #0f172a;
            font-weight: 800;
            font-size: 15px;
        }
        .chat-bubble {
            padding: 15px 18px;
            border-radius: 14px;
            font-size: var(--font-md);
            line-height: 1.6;
        }
        .bubble-bot {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            border-top-left-radius: 4px;
        }
        .bubble-user {
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: #ffffff;
            border-top-right-radius: 4px;
        }

        /* Result Cards within Chat */
        .result-card-inner {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 16px;
            margin: 12px 0;
        }
        .result-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .emissions-badge {
            font-size: var(--font-lg);
            font-weight: 800;
            color: #f87171;
        }
        .swap-recommendation {
            background: rgba(16, 185, 129, 0.12);
            border-left: 4px solid var(--primary);
            padding: 10px 14px;
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: var(--font-sm);
            color: var(--text-primary);
            margin: 10px 0;
        }

        /* Prompt Carousel */
        .prompt-carousel {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding: 10px 0;
            margin-bottom: 12px;
            scrollbar-width: none;
            -webkit-overflow-scrolling: touch;
        }
        .prompt-carousel::-webkit-scrollbar { display: none; }
        .prompt-chip {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: var(--font-sm);
            font-weight: 600;
            padding: 8px 14px;
            border-radius: var(--radius-full);
            white-space: nowrap;
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.15s ease;
        }
        .prompt-chip:hover {
            color: var(--text-primary);
            border-color: var(--border-hover);
            background: var(--bg-surface-elevated);
        }

        /* Chat Input Bar */
        .chat-input-wrapper {
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-full);
            padding: 8px 10px 8px 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        }
        .chat-input-field {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: var(--font-md);
            outline: none;
            padding: 6px 0;
        }
        .input-icon-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            width: 38px; height: 38px;
            border-radius: var(--radius-full);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.15s ease;
        }
        .input-icon-btn:hover {
            color: var(--text-primary);
            background: var(--bg-surface-elevated);
        }
        .input-icon-btn.recording {
            color: #ef4444;
            background: rgba(239, 68, 68, 0.2);
            animation: pulseRecord 1s infinite alternate;
        }
        @keyframes pulseRecord {
            from { transform: scale(1); }
            to { transform: scale(1.15); }
        }

        /* KPI Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }
        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 22px;
        }
        .kpi-label {
            font-size: var(--font-sm);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
        }
        .kpi-value {
            font-size: var(--font-xxl);
            font-weight: 800;
            color: var(--text-primary);
            margin: 8px 0 4px;
        }

        /* Modern Tables */
        .table-responsive {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        table.modern-table {
            width: 100%;
            border-collapse: collapse;
            font-size: var(--font-sm);
        }
        table.modern-table th {
            text-align: left;
            padding: 12px 16px;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-subtle);
        }
        table.modern-table td {
            padding: 14px 16px;
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-primary);
        }

        /* Mobile Bottom Nav */
        nav.mobile-bottom-nav {
            display: none;
            position: fixed;
            bottom: 0; left: 0; right: 0;
            height: var(--bottom-nav-height);
            background: var(--bg-surface);
            border-top: 1px solid var(--border-subtle);
            padding: 0 10px;
            padding-bottom: env(safe-area-inset-bottom);
            z-index: 50;
            justify-content: space-around;
            align-items: center;
        }
        @media (max-width: 1023px) {
            aside.desktop-sidebar { display: none; }
            .mobile-menu-trigger { display: block; }
            nav.mobile-bottom-nav { display: flex; }
        }
        .bottom-nav-item {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 4px;
            color: var(--text-secondary);
            text-decoration: none;
            border: none;
            background: transparent;
            font-size: 13.5px;
            font-weight: 600;
            cursor: pointer;
            padding: 8px 0;
            transition: all 0.15s ease;
        }
        .bottom-nav-item.active {
            color: var(--primary-light);
        }
        .bottom-nav-icon {
            font-size: 22px;
        }

        /* Mobile Drawer */
        .mobile-drawer-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(4px);
            z-index: 100;
        }
        .mobile-drawer-overlay.open { display: block; }
        .mobile-drawer-sheet {
            position: absolute;
            bottom: 0; left: 0; right: 0;
            background: var(--bg-surface);
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
            padding: 24px 20px;
            padding-bottom: calc(env(safe-area-inset-bottom) + 20px);
            max-height: 80vh;
            overflow-y: auto;
            transform: translateY(100%);
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .mobile-drawer-overlay.open .mobile-drawer-sheet {
            transform: translateY(0);
        }

        /* Form Inputs */
        .form-input {
            width: 100%;
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            padding: 11px 16px;
            font-size: var(--font-sm);
            outline: none;
        }
        .form-input:focus {
            border-color: var(--primary);
        }

        /* Toasts */
        .toast-container {
            position: fixed;
            top: 18px;
            right: 18px;
            z-index: 200;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        }
        .toast {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            padding: 12px 18px;
            border-radius: var(--radius-sm);
            font-size: var(--font-sm);
            font-weight: 600;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            pointer-events: auto;
            animation: fadeIn 0.2s ease-out;
        }

        /* Modals */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            align-items: center;
            justify-content: center;
            z-index: 150;
            padding: 20px;
        }
        .modal-overlay.open { display: flex; }
        .modal-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 26px;
            width: 100%;
            max-width: 520px;
            box-shadow: var(--shadow-card);
        }

        /* Leaderboard Rank Badges */
        .rank-badge {
            width: 32px; height: 32px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 15px;
        }
        .rank-1 { background: #fbbf24; color: #78350f; }
        .rank-2 { background: #cbd5e1; color: #334155; }
        .rank-3 { background: #d97706; color: #fff; }
        .rank-other { background: var(--bg-surface-elevated); color: var(--text-secondary); }
    </style>
</head>
<body>
    <div class="toast-container" id="toast-container"></div>

    <div class="app-container">
        <!-- Desktop Sidebar -->
        <aside class="desktop-sidebar">
            <div>
                <div class="brand-header">
                    <div class="brand-logo">🌱</div>
                    <div>
                        <div class="brand-title">EcoTracker<span class="brand-badge">SaaS</span></div>
                    </div>
                </div>

                <ul class="nav-list">
                    <li><button class="nav-button active" id="desk-nav-chat" onclick="switchTab('chat')"><span class="nav-left">💬 AI Carbon Chat</span><span class="nav-pill" style="background: rgba(16,185,129,0.2); color: #34d399;">Bot</span></button></li>
                    <li><button class="nav-button" id="desk-nav-scanner" onclick="switchTab('scanner')"><span class="nav-left">📸 Vision Scanner</span><span class="nav-pill" style="background: rgba(56,189,248,0.2); color: #38bdf8;">AI OCR</span></button></li>
                    <li><button class="nav-button" id="desk-nav-analytics" onclick="switchTab('analytics')"><span class="nav-left">📊 Analytics & Goals</span></button></li>
                    <li><button class="nav-button" id="desk-nav-simulator" onclick="switchTab('simulator')"><span class="nav-left">🔮 What-If Simulator</span></button></li>
                    <li><button class="nav-button" id="desk-nav-leaderboard" onclick="switchTab('leaderboard')"><span class="nav-left">🏆 Leaderboard</span><span class="nav-pill" style="background: rgba(245,158,11,0.2); color: #fbbf24;">Rank</span></button></li>
                    <li><button class="nav-button" id="desk-nav-habits" onclick="switchTab('habits')"><span class="nav-left">⚡ Habits Studio</span></button></li>
                    <li><button class="nav-button" id="desk-nav-esg" onclick="switchTab('esg')"><span class="nav-left">💼 Enterprise ESG</span><span class="nav-pill" style="background: rgba(168,85,247,0.2); color: #c084fc;">B2B</span></button></li>
                    <li><button class="nav-button" id="desk-nav-history" onclick="switchTab('history')"><span class="nav-left">📋 Activity History</span><span id="desk-history-count" class="nav-pill" style="background: rgba(255,255,255,0.08); color: var(--text-secondary);">0</span></button></li>
                    <li><button class="nav-button" id="desk-nav-offsets" onclick="switchTab('offsets')"><span class="nav-left">🌍 Carbon Offsets</span></button></li>
                    <li><button class="nav-button" id="desk-nav-future" onclick="switchTab('future')"><span class="nav-left">🚀 Future Scope</span><span class="nav-pill" style="background: rgba(59,130,246,0.2); color: #60a5fa;">Roadmap</span></button></li>
                </ul>
            </div>

            <div class="sidebar-footer">
                <div style="font-size: 14px; text-transform: uppercase; font-weight: 700; color: var(--text-tertiary); margin-bottom: 8px;">Customer Session</div>
                <div class="customer-pill">
                    <span>👤</span>
                    <input type="text" id="desk-user-input" value="default_customer" placeholder="User ID" onchange="switchUser(this.value)">
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary" style="flex: 1; font-size: 14px;" onclick="openApiKeyModal()">⚙️ Cloud API Key</button>
                    <button class="btn btn-cyan" style="font-size: 14px;" onclick="generateScorecardModal()">🏅 Scorecard</button>
                </div>
            </div>
        </aside>

        <!-- Main Viewport -->
        <main class="main-viewport">
            <header class="top-header">
                <div class="header-left">
                    <button class="mobile-menu-trigger" onclick="toggleMobileDrawer()">☰</button>
                    <div class="header-title-box">
                        <h2 id="page-title">AI Carbon Chat</h2>
                        <p id="page-subtitle">Interactive sustainability intelligence advisor</p>
                    </div>
                </div>

                <div class="header-actions">
                    <div class="status-badge" id="weather-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;" title="Outdoor Ambient Weather (Open-Meteo)">
                        ☀️ 22°C (Mild HVAC)
                    </div>
                    <div class="status-badge" id="grid-intensity-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;" onclick="fetchLiveGridStatus()" title="Live Regional Power Grid Carbon Intensity">
                        ⚡ Grid: Loading...
                    </div>
                    <button class="theme-toggle-btn" onclick="toggleTheme()" title="Toggle Dark/Light theme">🌗 Theme</button>
                </div>
            </header>

            <div class="content-scrollable">
                <!-- VIEW 1: AI Chat -->
                <section class="view-panel active" id="view-chat">
                    <div class="chat-layout">
                        <!-- Budget Warning Banner -->
                        <div id="budget-alert-banner" style="display: none; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: var(--radius-sm); padding: 10px 16px; margin-bottom: 12px; font-size: var(--font-sm); color: #fbbf24;"></div>

                        <div class="chat-message-feed" id="chat-feed">
                            <div class="chat-row">
                                <div class="chat-avatar avatar-bot">🌱</div>
                                <div class="chat-bubble bubble-bot">
                                    <strong style="font-size: var(--font-lg);">Welcome to EcoTracker!</strong><br><br>
                                    I am your personal AI sustainability advisor. Tell me about your daily choices—such as your commute, meals, air conditioner use, or flights. I'll calculate your exact carbon footprint and suggest practical, quantified eco-swaps.<br><br>
                                    <em>You can type your message, click the camera 📷 to scan a receipt, or tap the microphone 🎙️ to speak hands-free!</em>
                                </div>
                            </div>
                        </div>

                        <!-- Prompt Pills -->
                        <div class="prompt-carousel">
                            <div class="prompt-chip" onclick="quickPrompt('I drove 45 km in a gasoline car, calculate emissions')">🚗 45km Gas Commute</div>
                            <div class="prompt-chip" onclick="quickPrompt('Had a 250g ribeye steak dinner and 2 beers')">🥩 250g Steak Dinner</div>
                            <div class="prompt-chip" onclick="quickPrompt('Flew 1200 km domestic flight, show eco-swaps')">✈️ 1200km Flight</div>
                            <div class="prompt-chip" onclick="quickPrompt('Ran my AC cooling for 6 hours today')">❄️ 6hr AC Power</div>
                            <div class="prompt-chip" onclick="switchTab('scanner')">📸 Scan Receipt / Bill</div>
                        </div>

                        <!-- Input Bar with Speech Dictation -->
                        <div class="chat-input-wrapper">
                            <input type="text" class="chat-input-field" id="chat-text-input" placeholder="Message EcoTracker (or tap 🎙️ to speak)..." onkeydown="if(event.key==='Enter') sendChatMessage()">
                            <button class="input-icon-btn" id="voice-dictate-btn" onclick="toggleVoiceDictation()" title="Voice Dictation (Speech-to-Text)">🎙️</button>
                            <button class="input-icon-btn" onclick="triggerNativeCamera()" title="Upload or capture photo">📷</button>
                            <input type="file" id="chat-camera-file" accept="image/*" capture="environment" style="display: none;" onchange="handleChatImageUpload(event)">
                            <button class="btn btn-primary" style="padding: 10px 22px; border-radius: var(--radius-full);" onclick="sendChatMessage()">Send ↵</button>
                        </div>
                    </div>
                </section>

                <!-- VIEW 2: Vision Scanner -->
                <section class="view-panel" id="view-scanner">
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 18px;">
                            <div>
                                <h3 style="font-size: var(--font-xl); font-weight: 800;">📸 Multimodal Vision Scanner</h3>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary);">Upload or snap a photo of any grocery receipt or electric utility bill to parse line items.</p>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn btn-secondary" onclick="loadSampleScan('receipt')">🧾 Sample Receipt</button>
                                <button class="btn btn-secondary" onclick="loadSampleScan('utility_bill')">⚡ Sample Bill</button>
                            </div>
                        </div>

                        <!-- Dropzone -->
                        <div style="border: 2px dashed rgba(56, 189, 248, 0.35); border-radius: var(--radius-md); padding: 36px 20px; text-align: center; background: rgba(15, 23, 42, 0.4); cursor: pointer; margin-bottom: 20px;" onclick="document.getElementById('scanner-file-picker').click()">
                            <input type="file" id="scanner-file-picker" accept="image/*" capture="environment" style="display: none;" onchange="handleScannerFile(event)">
                            <div style="font-size: 42px; margin-bottom: 10px;">📷</div>
                            <h4 style="font-size: var(--font-lg); font-weight: 700; margin-bottom: 6px;">Tap to capture with camera or browse files</h4>
                            <p style="font-size: var(--font-sm); color: var(--text-secondary);">Direct support for mobile phone cameras (JPG, PNG, WebP)</p>
                        </div>

                        <!-- Scanned Results Area -->
                        <div id="scanner-output" style="display: none;">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-subtle); padding-bottom: 14px; margin-bottom: 18px;">
                                <div>
                                    <span id="scan-vendor-tag" class="status-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8;">Vendor</span>
                                    <h4 id="scan-title" style="font-size: var(--font-lg); font-weight: 800; margin-top: 6px;">Extracted Document</h4>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: var(--font-sm); color: var(--text-secondary);">Total Carbon Impact</div>
                                    <div id="scan-co2-total" style="font-size: var(--font-xxl); font-weight: 800; color: #f87171;">0.0 kg</div>
                                </div>
                            </div>
                            <p id="scan-summary-msg" style="font-size: var(--font-md); color: var(--text-secondary); line-height: 1.6; margin-bottom: 18px;"></p>

                            <div class="table-responsive">
                                <table class="modern-table">
                                    <thead>
                                        <tr>
                                            <th>Item / Description</th>
                                            <th>Qty</th>
                                            <th>Emissions</th>
                                            <th>Eco-Swap Recommendation</th>
                                            <th style="text-align: right;">Abatement</th>
                                        </tr>
                                    </thead>
                                    <tbody id="scan-items-tbody"></tbody>
                                </table>
                            </div>

                            <div style="display: flex; justify-content: flex-end; margin-top: 18px;">
                                <button class="btn btn-primary" onclick="commitScanLog()">💾 Log Total to Activity History</button>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- VIEW 3: Analytics & Goals -->
                <section class="view-panel" id="view-analytics">
                    <div class="kpi-grid">
                        <div class="kpi-card">
                            <div class="kpi-label">Gross Emissions</div>
                            <div class="kpi-value" id="kpi-gross-val">0.0 <span style="font-size: 15px; color: var(--text-secondary);">kg CO2e</span></div>
                            <div style="font-size: var(--font-sm); color: var(--text-secondary);" id="kpi-count-val">0 activities logged</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Carbon Avoided / Saved</div>
                            <div class="kpi-value" style="color: #34d399;" id="kpi-saved-val">0.0 <span style="font-size: 15px; color: var(--text-secondary);">kg CO2e</span></div>
                            <div style="font-size: var(--font-sm); color: var(--text-secondary);">Through greener eco-swaps</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Daily Budget Target</div>
                            <div class="kpi-value" id="kpi-budget-val">0%</div>
                            <div style="background: rgba(255,255,255,0.08); border-radius: 4px; height: 8px; overflow: hidden; margin-top: 8px;">
                                <div id="kpi-budget-bar" style="background: var(--primary); height: 100%; width: 0%;"></div>
                            </div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Milestones Unlocked</div>
                            <div class="kpi-value" style="color: #c084fc;" id="kpi-badges-val">0</div>
                            <div style="font-size: var(--font-sm); color: var(--text-secondary);" id="kpi-badge-desc">Start logging choices</div>
                        </div>
                    </div>

                    <!-- 30-Day Historical Trend Line Chart -->
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                            <h4 style="font-size: var(--font-lg); font-weight: 700;">📈 30-Day Carbon Trend Timeline</h4>
                            <span style="font-size: var(--font-sm); color: var(--text-secondary);">Daily Gross vs. Avoided</span>
                        </div>
                        <div style="height: 250px; position: relative;">
                            <canvas id="dailyTrendChart"></canvas>
                        </div>
                    </div>

                    <!-- Category Breakdown Chart & Goal Setter -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px;">
                        <div class="glass-card">
                            <h4 style="font-size: var(--font-lg); font-weight: 700; margin-bottom: 14px;">Emissions by Lifestyle Category</h4>
                            <div style="height: 240px; position: relative;">
                                <canvas id="analyticsDoughnut"></canvas>
                            </div>
                        </div>
                        <div class="glass-card">
                            <h4 style="font-size: var(--font-lg); font-weight: 700; margin-bottom: 8px;">Daily Carbon Target Budget</h4>
                            <p style="font-size: var(--font-sm); color: var(--text-secondary); margin-bottom: 18px;">Adjust your personal daily allowance to match your climate targets.</p>
                            <div style="display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 8px;">
                                <span>Daily Allowance:</span>
                                <span id="budget-slider-disp" style="color: var(--primary-light); font-size: var(--font-lg);">10.0 kg/day</span>
                            </div>
                            <input type="range" id="budget-range-input" min="2" max="40" step="0.5" value="10" style="width: 100%; accent-color: var(--primary); margin-bottom: 20px;" oninput="updateBudgetSlider(this.value)">
                            <button class="btn btn-primary" style="width: 100%;" onclick="saveUserBudget()">Save New Budget Target</button>
                        </div>
                    </div>
                </section>

                <!-- VIEW 4: What-If Simulator -->
                <section class="view-panel" id="view-simulator">
                    <div class="glass-card">
                        <h3 style="font-size: var(--font-xl); font-weight: 800; margin-bottom: 6px;">🔮 What-If Climate & ROI Simulator</h3>
                        <p style="font-size: var(--font-sm); color: var(--text-secondary); margin-bottom: 26px;">Adjust lifestyle sliders to see your projected multi-year carbon abatement and cumulative household money saved.</p>

                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin-bottom: 26px;">
                            <div class="glass-card" style="margin-bottom: 0;">
                                <div style="display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 8px;">
                                    <span>Weekly Commute</span>
                                    <span id="sim-km-disp" style="color: #38bdf8;">150 km/wk</span>
                                </div>
                                <input type="range" id="sim-km-slider" min="20" max="600" step="10" value="150" style="width: 100%; accent-color: #38bdf8; margin-bottom: 14px;" oninput="triggerSimulatorCalc()">
                                <div style="font-size: var(--font-sm); color: var(--text-secondary); margin-bottom: 6px;">Shift Commute Vehicle:</div>
                                <select id="sim-mode-select" class="form-input" onchange="triggerSimulatorCalc()">
                                    <option value="train">Electric Train (79% cut)</option>
                                    <option value="ev">Electric Car / EV (76% cut)</option>
                                    <option value="bus">City Bus (54% cut)</option>
                                    <option value="bike">Bicycle / Walking (100% cut)</option>
                                </select>
                            </div>

                            <div class="glass-card" style="margin-bottom: 0;">
                                <div style="display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 8px;">
                                    <span>Plant-Based Days / Week</span>
                                    <span id="sim-diet-disp" style="color: #34d399;">3 days/wk</span>
                                </div>
                                <input type="range" id="sim-diet-slider" min="0" max="7" step="1" value="3" style="width: 100%; accent-color: #34d399; margin-bottom: 14px;" oninput="triggerSimulatorCalc()">
                                <p style="font-size: var(--font-sm); color: var(--text-secondary);">3 plant-based days eliminate ~1,950 kg CO2e annually while reducing household grocery expenses.</p>
                            </div>

                            <div class="glass-card" style="margin-bottom: 0;">
                                <div style="font-weight: 700; margin-bottom: 12px;">Home Clean Tech & Aviation</div>
                                <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; cursor: pointer; font-size: var(--font-sm);">
                                    <input type="checkbox" id="sim-solar-box" checked style="accent-color: #f59e0b;" onchange="triggerSimulatorCalc()">
                                    <span>☀️ 5kW Rooftop Solar Installation</span>
                                </label>
                                <label style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px; cursor: pointer; font-size: var(--font-sm);">
                                    <input type="checkbox" id="sim-heatpump-box" checked style="accent-color: #a855f7;" onchange="triggerSimulatorCalc()">
                                    <span>♨️ Air-Source Heat Pump</span>
                                </label>
                                <div style="display: flex; justify-content: space-between; font-size: var(--font-sm); margin-bottom: 6px;">
                                    <span>Flights Avoided / Swapped to Rail:</span>
                                    <span id="sim-flights-disp" style="font-weight: 700;">2 flights</span>
                                </div>
                                <input type="range" id="sim-flights-slider" min="0" max="6" step="1" value="2" style="width: 100%; accent-color: #a855f7;" oninput="triggerSimulatorCalc()">
                            </div>
                        </div>

                        <!-- Multi-Horizon Cards -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 22px;">
                            <div class="glass-card" style="text-align: center; border-color: rgba(56, 189, 248, 0.3);">
                                <div class="kpi-label">1-Year Horizon</div>
                                <div id="sim-co2-1" style="font-size: var(--font-xxl); font-weight: 800; color: #38bdf8; margin: 8px 0 4px;">7.8 MT</div>
                                <div id="sim-cash-1" style="font-size: var(--font-lg); font-weight: 700; color: #34d399;">+$1,840</div>
                                <div style="font-size: var(--font-sm); color: var(--text-secondary);">Estimated Savings</div>
                            </div>
                            <div class="glass-card" style="text-align: center; border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.05);">
                                <div class="kpi-label" style="color: #34d399;">5-Year Horizon</div>
                                <div id="sim-co2-5" style="font-size: var(--font-xxl); font-weight: 800; color: #34d399; margin: 8px 0 4px;">39.0 MT</div>
                                <div id="sim-cash-5" style="font-size: var(--font-lg); font-weight: 700; color: #34d399;">+$9,200</div>
                                <div style="font-size: var(--font-sm); color: var(--text-secondary);">Estimated Savings</div>
                            </div>
                            <div class="glass-card" style="text-align: center; border-color: rgba(168, 85, 247, 0.3);">
                                <div class="kpi-label">10-Year Horizon</div>
                                <div id="sim-co2-10" style="font-size: var(--font-xxl); font-weight: 800; color: #c084fc; margin: 8px 0 4px;">78.0 MT</div>
                                <div id="sim-cash-10" style="font-size: var(--font-lg); font-weight: 700; color: #34d399;">+$18,400</div>
                                <div style="font-size: var(--font-sm); color: var(--text-secondary);">Estimated Savings</div>
                            </div>
                        </div>

                        <div id="sim-summary-container" style="background: var(--bg-surface-elevated); padding: 16px 20px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); font-size: var(--font-md);"></div>
                    </div>
                </section>

                <!-- VIEW 5: Community Leaderboard -->
                <section class="view-panel" id="view-leaderboard">
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">
                            <div>
                                <h3 style="font-size: var(--font-xl); font-weight: 800;">🏆 Sustainability Champions Leaderboard</h3>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary);">Compare cumulative carbon avoided and green actions across community participants.</p>
                            </div>
                            <button class="btn btn-secondary" onclick="loadLeaderboardData()">🔄 Refresh Standings</button>
                        </div>

                        <div class="table-responsive">
                            <table class="modern-table">
                                <thead>
                                    <tr>
                                        <th style="width: 60px;">Rank</th>
                                        <th>Participant</th>
                                        <th>Activities</th>
                                        <th>Carbon Avoided</th>
                                        <th>Total Logged</th>
                                        <th style="text-align: right;">Badges</th>
                                    </tr>
                                </thead>
                                <tbody id="leaderboard-tbody">
                                    <tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-secondary);">Loading leaderboard rankings...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>

                <!-- VIEW 6: Habits Studio -->
                <section class="view-panel" id="view-habits">
                    <div class="glass-card">
                        <h3 style="font-size: var(--font-xl); font-weight: 800; margin-bottom: 6px;">⚡ Eco Habits Studio</h3>
                        <p style="font-size: var(--font-sm); color: var(--text-secondary); margin-bottom: 20px;">1-tap daily presets that record verified choices directly into your activity history.</p>

                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 28px;">
                            <button class="btn btn-secondary" style="flex-direction: column; padding: 20px; gap: 10px; height: auto;" onclick="logHabitPreset('transit', 'Commuted 25 km via Electric Train', 0.88, 3.92)">
                                <span style="font-size: 28px;">🚆</span>
                                <strong style="font-size: var(--font-md);">Electric Train</strong>
                                <span style="font-size: var(--font-sm); color: #34d399;">Saves 3.92 kg CO2e</span>
                            </button>
                            <button class="btn btn-secondary" style="flex-direction: column; padding: 20px; gap: 10px; height: auto;" onclick="logHabitPreset('diet', 'Plant-based lentil & quinoa lunch', 0.40, 2.50)">
                                <span style="font-size: 28px;">🥗</span>
                                <strong style="font-size: var(--font-md);">Plant-Based Lunch</strong>
                                <span style="font-size: var(--font-sm); color: #34d399;">Saves 2.50 kg CO2e</span>
                            </button>
                            <button class="btn btn-secondary" style="flex-direction: column; padding: 20px; gap: 10px; height: auto;" onclick="logHabitPreset('transit', 'Bicycle ride for local errands (8 km)', 0.0, 1.54)">
                                <span style="font-size: 28px;">🚲</span>
                                <strong style="font-size: var(--font-md);">8 km Bicycle Ride</strong>
                                <span style="font-size: var(--font-sm); color: #34d399;">Zero Emissions</span>
                            </button>
                            <button class="btn btn-secondary" style="flex-direction: column; padding: 20px; gap: 10px; height: auto;" onclick="logHabitPreset('waste', 'Recycled 2 kg aluminum cans & containers', 0.0, 16.0)">
                                <span style="font-size: 28px;">♻️</span>
                                <strong style="font-size: var(--font-md);">Recycled Aluminum</strong>
                                <span style="font-size: var(--font-sm); color: #34d399;">Saves 16.0 kg CO2e</span>
                            </button>
                        </div>

                        <!-- FastMCP Calculator -->
                        <h4 style="font-size: var(--font-lg); font-weight: 700; margin-bottom: 14px;">FastMCP Scientific Domain Calculator</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 18px;">
                            <div>
                                <label style="font-size: var(--font-sm); color: var(--text-secondary); display: block; margin-bottom: 6px;">Category</label>
                                <select id="mcp-calc-category" class="form-input" onchange="populateMcpItems(this.value)">
                                    <option value="transit">Transportation</option>
                                    <option value="diet">Food & Dietary</option>
                                    <option value="appliance">Home Energy / Appliance</option>
                                    <option value="waste">Recycling / Waste Offset</option>
                                </select>
                            </div>
                            <div>
                                <label style="font-size: var(--font-sm); color: var(--text-secondary); display: block; margin-bottom: 6px;" id="mcp-item-label">Item / Mode</label>
                                <select id="mcp-item-select" class="form-input"></select>
                            </div>
                            <div>
                                <label style="font-size: var(--font-sm); color: var(--text-secondary); display: block; margin-bottom: 6px;" id="mcp-qty-label">Quantity</label>
                                <input type="number" id="mcp-qty-input" class="form-input" value="45" min="0.1" step="any">
                            </div>
                        </div>
                        <button class="btn btn-cyan" style="width: 100%;" onclick="runMcpCalculation()">Calculate & Compare Benchmarks</button>
                        <div id="mcp-results-box" style="margin-top: 16px; display: none;"></div>
                    </div>
                </section>

                <!-- VIEW 7: Enterprise ESG -->
                <section class="view-panel" id="view-esg">
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">
                            <div>
                                <h3 style="font-size: var(--font-xl); font-weight: 800;">💼 Enterprise ESG Carbon Accounting</h3>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary);">Greenhouse Gas (GHG) Protocol Scope 1, Scope 2, and Scope 3 balance sheet.</p>
                            </div>
                            <div>
                                <a id="esg-report-link" href="/api/esg-report?format=html" target="_blank" class="btn btn-cyan">🖨️ View Executive PDF Report ↗</a>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 22px;">
                            <div class="glass-card" style="margin-bottom: 0;">
                                <div class="kpi-label" style="color: #f59e0b;">Scope 1 (Direct Fuels)</div>
                                <div id="esg-scope1-num" style="font-size: var(--font-xxl); font-weight: 800; margin: 6px 0 2px;">0.000 <span style="font-size: 14px; color: var(--text-secondary);">MT</span></div>
                                <div style="font-size: var(--font-sm); color: var(--text-secondary);">Boilers, fleet fuel, natural gas.</div>
                            </div>
                            <div class="glass-card" style="margin-bottom: 0;">
                                <div class="kpi-label" style="color: #38bdf8;">Scope 2 (Market Power)</div>
                                <div id="esg-scope2-num" style="font-size: var(--font-xxl); font-weight: 800; margin: 6px 0 2px;">0.000 <span style="font-size: 14px; color: var(--text-secondary);">MT</span></div>
                                <div style="font-size: var(--font-sm); color: var(--text-secondary);">Purchased grid electricity & steam.</div>
                            </div>
                            <div class="glass-card" style="margin-bottom: 0;">
                                <div class="kpi-label" style="color: #34d399;">Scope 3 (Value Chain)</div>
                                <div id="esg-scope3-num" style="font-size: var(--font-xxl); font-weight: 800; margin: 6px 0 2px;">0.000 <span style="font-size: 14px; color: var(--text-secondary);">MT</span></div>
                                <div style="font-size: var(--font-sm); color: var(--text-secondary);">Business travel, commuting, catering, waste.</div>
                            </div>
                        </div>

                        <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <strong style="font-size: var(--font-md);">Cryptographic Audit Fingerprint</strong>
                                <span id="esg-audit-badge" class="status-badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-family: monospace;">ESG-VERIFIED-SYNC</span>
                            </div>
                            <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.6;">
                                Conforms to the GHG Protocol Corporate Accounting Standard. Verified with SHA-256 integrity checksums for third-party CSRD and SEC compliance audits.
                            </p>
                        </div>
                    </div>
                </section>

                <!-- VIEW 8: Activity History -->
                <section class="view-panel" id="view-history">
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 18px;">
                            <div>
                                <h3 style="font-size: var(--font-xl); font-weight: 800;">📋 Activity Audit History</h3>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary);">View, filter, delete, or download verified activity entries.</p>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn btn-secondary" onclick="exportDataCSV()">📥 Export CSV</button>
                                <button class="btn btn-danger" onclick="openResetModal()">🗑️ Wipe History</button>
                            </div>
                        </div>

                        <div class="table-responsive">
                            <table class="modern-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Scope</th>
                                        <th>Category</th>
                                        <th>Activity Details</th>
                                        <th>Gross (kg)</th>
                                        <th>Saved (kg)</th>
                                        <th style="text-align: right;">Action</th>
                                    </tr>
                                </thead>
                                <tbody id="history-rows-tbody">
                                    <tr><td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 26px;">Loading activity history...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>

                <!-- VIEW 9: Carbon Offsets -->
                <section class="view-panel" id="view-offsets">
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 22px;">
                            <div>
                                <h3 style="font-size: var(--font-xl); font-weight: 800;">🌍 Verified Carbon Offsets</h3>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary);">Neutralize residual emissions through certified Gold Standard & Verra VCS projects.</p>
                            </div>
                            <div style="display: flex; align-items: center; gap: 12px; background: var(--bg-surface-elevated); padding: 10px 16px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
                                <span style="font-size: var(--font-sm); color: var(--text-secondary);">Offset:</span>
                                <input type="range" min="10" max="500" step="10" value="100" style="accent-color: #38bdf8;" oninput="updateOffsetDisp(this.value)">
                                <span id="offset-calc-disp" style="font-size: var(--font-md); font-weight: 700; color: #38bdf8;">100 kg (~5 trees, $3.00)</span>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px;">
                            <div class="glass-card" style="margin-bottom: 0;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span class="status-badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399;">Gold Standard #GS1284</span>
                                    <span style="font-weight: 700;">$15 / ton</span>
                                </div>
                                <h4 style="font-size: var(--font-lg); font-weight: 700; margin-bottom: 8px;">🌳 Rimba Raya Peatland Forest</h4>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 14px;">Protects 65,000 hectares of tropical peat swamp forest in Borneo, preserving endangered orangutan habitats.</p>
                                <a href="https://www.goldstandard.org/" target="_blank" class="btn btn-secondary" style="width: 100%;">View Registry ↗</a>
                            </div>

                            <div class="glass-card" style="margin-bottom: 0;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span class="status-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8;">Verra VCS #1822</span>
                                    <span style="font-weight: 700;">$12 / ton</span>
                                </div>
                                <h4 style="font-size: var(--font-lg); font-weight: 700; margin-bottom: 8px;">💨 Renewable Wind Portfolio</h4>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 14px;">Displaces fossil thermal electricity across regional power grids with 250 MW of clean wind generation.</p>
                                <a href="https://registry.verra.org/" target="_blank" class="btn btn-secondary" style="width: 100%;">View Registry ↗</a>
                            </div>

                            <div class="glass-card" style="margin-bottom: 0;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span class="status-badge" style="background: rgba(168, 85, 247, 0.2); color: #c084fc;">Blue Carbon</span>
                                    <span style="font-weight: 700;">$18 / ton</span>
                                </div>
                                <h4 style="font-size: var(--font-lg); font-weight: 700; margin-bottom: 8px;">🌊 Coastal Mangrove Restoration</h4>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 14px;">Restores tidal mangrove forests that sequester carbon up to 4x faster than terrestrial rainforests.</p>
                                <a href="https://www.goldstandard.org/" target="_blank" class="btn btn-secondary" style="width: 100%;">View Registry ↗</a>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- VIEW 10: Future Scope & Strategic Roadmap -->
                <section class="view-panel" id="view-future">
                    <div class="glass-card">
                        <div class="glass-card-header">
                            <div>
                                <h3 class="glass-card-title">🚀 Strategic Roadmap & Future Scope</h3>
                                <p class="glass-card-subtitle">Architectural evolution towards autonomous sustainability intelligence</p>
                            </div>
                            <span class="status-badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa;">2027-2028 Horizon</span>
                        </div>

                        <div class="glass-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));">
                            <div class="glass-card" style="margin-bottom: 0; background: var(--bg-surface-elevated);">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="font-size: 13px; font-weight: 700; color: var(--text-tertiary);">Q1-Q2 2027</span>
                                    <span class="status-badge" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa;">Architecture</span>
                                </div>
                                <h4 style="font-size: var(--font-lg); font-weight: 800; margin-bottom: 6px;">🔌 IoT & Smart Home Ingestion</h4>
                                <p style="font-size: 14px; color: #60a5fa; font-weight: 600; margin-bottom: 8px;">Matter, MQTT & Zigbee Smart Plugs</p>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Automated telemetry streaming from smart plugs and Google Nest thermostats into FastMCP, removing manual entry completely.</p>
                                <div style="font-size: 13px; color: var(--text-tertiary);">✓ Zero manual input &nbsp;•&nbsp; ✓ Real-time wattage &nbsp;•&nbsp; ✓ Sub-second alerts</div>
                            </div>

                            <div class="glass-card" style="margin-bottom: 0; background: var(--bg-surface-elevated);">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="font-size: 13px; font-weight: 700; color: var(--text-tertiary);">Q2-Q3 2027</span>
                                    <span class="status-badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">Prototyping</span>
                                </div>
                                <h4 style="font-size: var(--font-lg); font-weight: 800; margin-bottom: 6px;">💳 Open Banking Green Fintech</h4>
                                <p style="font-size: 14px; color: #34d399; font-weight: 600; margin-bottom: 8px;">Plaid & Open Banking Aggregation</p>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Merchant Category Code (MCC) footprinting for automated transaction emissions across grocery, fuel, and travel cards.</p>
                                <div style="font-size: 13px; color: var(--text-tertiary);">✓ Bank-grade OAuth &nbsp;•&nbsp; ✓ USEEIO factors &nbsp;•&nbsp; ✓ Automated tracking</div>
                            </div>

                            <div class="glass-card" style="margin-bottom: 0; background: var(--bg-surface-elevated);">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="font-size: 13px; font-weight: 700; color: var(--text-tertiary);">Q3 2027</span>
                                    <span class="status-badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">Research</span>
                                </div>
                                <h4 style="font-size: var(--font-lg); font-weight: 800; margin-bottom: 6px;">🤖 Autonomous A2A Microgrid Auctions</h4>
                                <p style="font-size: 14px; color: #fbbf24; font-weight: 600; margin-bottom: 8px;">Decentralized Smart EV Load Scheduling</p>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Multi-agent ADK negotiation scheduling home EV batteries during peak renewable generation to maximize clean energy use.</p>
                                <div style="font-size: 13px; color: var(--text-tertiary);">✓ Tariff arbitrage &nbsp;•&nbsp; ✓ Zero curtailment &nbsp;•&nbsp; ✓ Grid stabilization</div>
                            </div>

                            <div class="glass-card" style="margin-bottom: 0; background: var(--bg-surface-elevated);">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="font-size: 13px; font-weight: 700; color: var(--text-tertiary);">Q4 2027</span>
                                    <span class="status-badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc;">Concept</span>
                                </div>
                                <h4 style="font-size: var(--font-lg); font-weight: 800; margin-bottom: 6px;">⛓️ Decentralized On-Chain ESG Audit</h4>
                                <p style="font-size: 14px; color: #c084fc; font-weight: 600; margin-bottom: 8px;">Double-Counting-Proof Credit Ledger</p>
                                <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px;">Immutable, zero-greenwashing verification certificates for corporate CSRD and SEC compliance filings.</p>
                                <div style="font-size: 13px; color: var(--text-tertiary);">✓ Verifiable proof &nbsp;•&nbsp; ✓ Anti-greenwashing &nbsp;•&nbsp; ✓ Audit transparency</div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </main>
    </div>

    <!-- Mobile Bottom Navigation Bar -->
    <nav class="mobile-bottom-nav">
        <button class="bottom-nav-item active" id="bot-nav-chat" onclick="switchTab('chat')">
            <span class="bottom-nav-icon">💬</span>
            <span>Chat</span>
        </button>
        <button class="bottom-nav-item" id="bot-nav-scanner" onclick="switchTab('scanner')">
            <span class="bottom-nav-icon">📸</span>
            <span>Scanner</span>
        </button>
        <button class="bottom-nav-item" id="bot-nav-analytics" onclick="switchTab('analytics')">
            <span class="bottom-nav-icon">📊</span>
            <span>Stats</span>
        </button>
        <button class="bottom-nav-item" id="bot-nav-simulator" onclick="switchTab('simulator')">
            <span class="bottom-nav-icon">🔮</span>
            <span>Simulate</span>
        </button>
        <button class="bottom-nav-item" onclick="toggleMobileDrawer()">
            <span class="bottom-nav-icon">☰</span>
            <span>More</span>
        </button>
    </nav>

    <!-- Mobile Drawer Sheet -->
    <div class="mobile-drawer-overlay" id="mobile-drawer" onclick="if(event.target===this) toggleMobileDrawer()">
        <div class="mobile-drawer-sheet">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                <h3 style="font-size: var(--font-lg); font-weight: 800;">Navigation & Tools</h3>
                <button class="btn btn-secondary" style="padding: 6px 12px;" onclick="toggleMobileDrawer()">✕</button>
            </div>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                <button class="nav-button" onclick="switchTab('leaderboard'); toggleMobileDrawer();">🏆 Community Leaderboard</button>
                <button class="nav-button" onclick="switchTab('habits'); toggleMobileDrawer();">⚡ Eco Habits Studio</button>
                <button class="nav-button" onclick="switchTab('esg'); toggleMobileDrawer();">💼 Enterprise ESG Disclosure</button>
                <button class="nav-button" onclick="switchTab('history'); toggleMobileDrawer();">📋 Activity Audit History</button>
                <button class="nav-button" onclick="switchTab('offsets'); toggleMobileDrawer();">🌍 Carbon Offsets Directory</button>
                <button class="nav-button" onclick="switchTab('future'); toggleMobileDrawer();">🚀 Future Scope & Roadmap</button>
                <button class="nav-button" onclick="generateScorecardModal(); toggleMobileDrawer();">🏅 My Eco Scorecard</button>
                <button class="nav-button" onclick="openApiKeyModal(); toggleMobileDrawer();">⚙️ Configure Cloud LLM API Key</button>
            </div>
        </div>
    </div>

    <!-- API Key Modal -->
    <div class="modal-overlay" id="api-key-modal">
        <div class="modal-card">
            <h3 style="font-size: var(--font-lg); font-weight: 800; margin-bottom: 8px;">⚙️ Cloud AI Key Settings</h3>
            <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 16px;">
                Paste your free Gemini API key (or free Groq key) to activate conversational AI reasoning.
            </p>
            <input type="password" id="modal-api-key-input" class="form-input" placeholder="AIzaSy... or gsk_..." style="margin-bottom: 18px;">
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button class="btn btn-secondary" onclick="closeApiKeyModal()">Cancel</button>
                <button class="btn btn-primary" onclick="saveApiKeyModal()">Save Key</button>
            </div>
        </div>
    </div>

    <!-- Eco Scorecard Modal -->
    <div class="modal-overlay" id="scorecard-modal">
        <div class="modal-card" style="text-align: center;">
            <div style="font-size: 38px; margin-bottom: 8px;">🌍</div>
            <h3 style="font-size: var(--font-xl); font-weight: 800; margin-bottom: 4px;">Verified Eco Impact Scorecard</h3>
            <p style="font-size: var(--font-sm); color: var(--text-secondary); margin-bottom: 18px;" id="scorecard-user-label"></p>
            <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 18px; margin-bottom: 18px;">
                <div style="font-size: var(--font-sm); text-transform: uppercase; color: var(--text-secondary); font-weight: 700;">Total Carbon Avoided</div>
                <div style="font-size: var(--font-xxl); font-weight: 800; color: #34d399; margin: 4px 0;" id="scorecard-saved-val">0.0 kg</div>
                <div style="font-size: var(--font-sm); color: var(--text-secondary);" id="scorecard-trees-val">Equivalent to ~0 mature trees</div>
            </div>
            <div style="display: flex; justify-content: center; gap: 10px;">
                <button class="btn btn-secondary" onclick="closeScorecardModal()">Close</button>
                <button class="btn btn-primary" onclick="copyScorecardText()">📋 Copy Text</button>
            </div>
        </div>
    </div>

    <!-- Reset Confirmation Modal -->
    <div class="modal-overlay" id="reset-history-modal">
        <div class="modal-card">
            <h3 style="font-size: var(--font-lg); font-weight: 800; color: #f87171; margin-bottom: 8px;">⚠️ Wipe Activity History?</h3>
            <p style="font-size: var(--font-sm); color: var(--text-secondary); line-height: 1.5; margin-bottom: 18px;">
                This will permanently delete all activity calculations, badges, and history for this user session. This action cannot be reversed.
            </p>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button class="btn btn-secondary" onclick="closeResetModal()">Cancel</button>
                <button class="btn btn-danger" onclick="confirmResetAll()">Confirm Wipe</button>
            </div>
        </div>
    </div>

    <script>
        let currentTabId = 'chat';
        let currentUserId = localStorage.getItem('ecotracker_uid') || 'default_customer';
        let doughnutChartInstance = null;
        let trendChartInstance = null;
        let lastSummaryPayload = null;
        let lastScannedPayload = null;
        let speechRecognition = null;
        let isRecording = false;

        const TAB_HEADERS = {
            chat: { title: 'AI Carbon Chat', subtitle: 'Conversational sustainability intelligence' },
            scanner: { title: 'Multimodal Vision Scanner', subtitle: 'AI OCR for grocery receipts and utility bills' },
            analytics: { title: 'Carbon Analytics & Goals', subtitle: 'Executive footprints, breakdowns, and targets' },
            simulator: { title: 'What-If Climate & ROI Simulator', subtitle: '1, 5, and 10-year transition projections' },
            leaderboard: { title: 'Community Leaderboard', subtitle: 'Rankings across sustainability champions' },
            habits: { title: 'Eco Habits Studio', subtitle: '1-tap habit presets and scientific calculations' },
            esg: { title: 'Enterprise ESG Disclosure', subtitle: 'GHG Protocol Scope 1-2-3 compliance balance sheet' },
            history: { title: 'Activity Audit History', subtitle: 'Verified transactional record management' },
            offsets: { title: 'Verified Carbon Offsets', subtitle: 'Certified Gold Standard & Verra portfolio' },
            future: { title: 'Future Scope & Strategic Roadmap', subtitle: 'IoT telemetry, open banking, autonomous A2A auctions, and on-chain audits' }
        };

        function showToast(message) {
            const container = document.getElementById('toast-container');
            container.innerHTML = '';
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.style.cursor = 'pointer';
            toast.title = 'Click to dismiss';
            toast.innerHTML = `<span>${message}</span><span style="font-size: 13px; opacity: 0.6; margin-left: 8px;">✕</span>`;
            toast.onclick = () => toast.remove();
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-6px)';
                toast.style.transition = 'all 0.25s ease';
                setTimeout(() => toast.remove(), 250);
            }, 1800);
        }

        function switchTab(tabId) {
            currentTabId = tabId;
            document.querySelectorAll('.view-panel').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.nav-button').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.bottom-nav-item').forEach(b => b.classList.remove('active'));

            const panel = document.getElementById(`view-${tabId}`);
            if (panel) panel.classList.add('active');

            const deskBtn = document.getElementById(`desk-nav-${tabId}`);
            if (deskBtn) deskBtn.classList.add('active');

            const botBtn = document.getElementById(`bot-nav-${tabId}`);
            if (botBtn) botBtn.classList.add('active');

            const meta = TAB_HEADERS[tabId];
            if (meta) {
                document.getElementById('page-title').innerText = meta.title;
                document.getElementById('page-subtitle').innerText = meta.subtitle;
            }

            if (tabId === 'analytics') {
                renderCategoryChart();
                loadDailyTrends();
            } else if (tabId === 'simulator') {
                triggerSimulatorCalc();
            } else if (tabId === 'leaderboard') {
                loadLeaderboardData();
            } else if (tabId === 'esg') {
                loadEsgReport();
            } else if (tabId === 'history') {
                loadDashboardData();
            }
        }

        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('ecotracker_theme', next);
        }

        function toggleFontScale() {
            document.documentElement.setAttribute('data-font-scale', 'large');
            showToast('🔤 Font size: LARGE (Default Everywhere)');
        }

        function toggleMobileDrawer() {
            const drawer = document.getElementById('mobile-drawer');
            drawer.classList.toggle('open');
        }

        function switchUser(newUid) {
            currentUserId = newUid.trim() || 'default_customer';
            localStorage.setItem('ecotracker_uid', currentUserId);
            showToast(`Switched user: ${currentUserId}`);
            loadDashboardData();
        }

        // Live Grid Status
        async function fetchLiveGridStatus() {
            try {
                const res = await fetch('/api/grid-intensity?region=auto');
                const data = await res.json();
                const badge = document.getElementById('grid-intensity-badge');
                if (badge) {
                    badge.innerHTML = `⚡ Grid: ${data.intensity_g_kwh} g/kWh (${data.rating})`;
                    if (data.rating === 'GREEN') {
                        badge.style.background = 'rgba(16, 185, 129, 0.2)';
                        badge.style.color = '#34d399';
                    } else if (data.rating === 'MODERATE') {
                        badge.style.background = 'rgba(245, 158, 11, 0.2)';
                        badge.style.color = '#f59e0b';
                    } else {
                        badge.style.background = 'rgba(239, 68, 68, 0.2)';
                        badge.style.color = '#f87171';
                    }
                }
            } catch (err) {
                console.error(err);
            }
        }

        // Ambient Weather via Open-Meteo API
        async function fetchAmbientWeather() {
            try {
                const res = await fetch('https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current_weather=true');
                if (res.ok) {
                    const data = await res.json();
                    const temp = data.current_weather.temperature;
                    const wBadge = document.getElementById('weather-badge');
                    if (wBadge) {
                        const hvacContext = temp > 28 ? 'High AC Load' : temp < 14 ? 'Heating Active' : 'Mild HVAC';
                        wBadge.innerHTML = `🌤️ ${temp}°C (${hvacContext})`;
                    }
                }
            } catch (e) {
                // Ignore if offline
            }
        }

        // Hands-Free Speech Dictation (Web Speech API)
        function toggleVoiceDictation() {
            const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechAPI) {
                showToast('Voice dictation is not supported in this browser. Try Chrome or Safari.');
                return;
            }

            const btn = document.getElementById('voice-dictate-btn');
            if (isRecording) {
                if (speechRecognition) speechRecognition.stop();
                isRecording = false;
                btn.classList.remove('recording');
                showToast('Dictation ended.');
                return;
            }

            speechRecognition = new SpeechAPI();
            speechRecognition.continuous = false;
            speechRecognition.interimResults = false;
            speechRecognition.lang = 'en-US';

            speechRecognition.onstart = function() {
                isRecording = true;
                btn.classList.add('recording');
                showToast('🎙️ Listening... speak your activity now.');
            };

            speechRecognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                const input = document.getElementById('chat-text-input');
                input.value = transcript;
                isRecording = false;
                btn.classList.remove('recording');
                showToast(`Transcribed: "${transcript}"`);
            };

            speechRecognition.onerror = function(e) {
                isRecording = false;
                btn.classList.remove('recording');
                showToast(`Voice error: ${e.error}`);
            };

            speechRecognition.onend = function() {
                isRecording = false;
                btn.classList.remove('recording');
            };

            speechRecognition.start();
        }

        // AI Chat Pipeline
        let conversationHistory = [];

        async function sendChatMessage(customMsg = null) {
            const input = document.getElementById('chat-text-input');
            const msg = (customMsg || input.value).trim();
            if (!msg) return;
            if (!customMsg) input.value = '';

            const feed = document.getElementById('chat-feed');

            // Render User Message
            const userRow = document.createElement('div');
            userRow.className = 'chat-row user-row';
            userRow.innerHTML = `
                <div class="chat-avatar avatar-user">You</div>
                <div class="chat-bubble bubble-user">${msg}</div>
            `;
            feed.appendChild(userRow);
            feed.scrollTop = feed.scrollHeight;
            conversationHistory.push({ role: 'user', content: msg });

            // Typing Indicator
            const typingRow = document.createElement('div');
            typingRow.className = 'chat-row';
            typingRow.id = 'bot-typing-indicator';
            typingRow.innerHTML = `
                <div class="chat-avatar avatar-bot">🌱</div>
                <div class="chat-bubble bubble-bot" style="color: var(--text-secondary); font-style: italic;">Analyzing environmental footprint...</div>
            `;
            feed.appendChild(typingRow);
            feed.scrollTop = feed.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        message: msg,
                        api_key: localStorage.getItem('ecotracker_api_key') || '',
                        history: conversationHistory
                    })
                });
                const data = await res.json();
                typingRow.remove();

                const botRow = document.createElement('div');
                botRow.className = 'chat-row';
                
                let contentHtml = '';
                if (data.co2e_kg > 0 && data.items && data.items.length > 0) {
                    const cardsHtml = data.items.map(item => `
                        <div class="result-card-inner">
                            <div class="result-card-header">
                                <strong style="font-size: var(--font-md);">${item.item_name}</strong>
                                <span class="emissions-badge">${item.emissions_kg} kg CO2e</span>
                            </div>
                            <div style="font-size: var(--font-sm); color: var(--text-secondary); margin-bottom: 6px;">
                                Formula: <code>${item.quantity} ${item.unit} × ${item.factor} kg/unit</code>
                            </div>
                            ${item.swap ? `<div class="swap-recommendation">🌱 <strong>Eco-Swap:</strong> ${item.swap} (Saves ${item.saved_kg} kg CO2e)</div>` : ''}
                        </div>
                    `).join('');

                    let actionHtml = '';
                    if (!data.logged_record && !msg.toLowerCase().includes('log') && !msg.toLowerCase().includes('save')) {
                        actionHtml = `
                            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px;">
                                <button class="btn btn-primary" style="font-size: var(--font-sm); padding: 7px 14px;" onclick="logDirectChoice('${data.category}', '${msg.replace(/'/g, "\\'")}', ${data.co2e_kg}, ${data.saved_co2e_kg || 0})">
                                    📌 Log to Profile (+${data.co2e_kg} kg)
                                </button>
                                <button class="btn btn-secondary" style="font-size: var(--font-sm); padding: 7px 14px;" onclick="quickPrompt('What if I took an electric train instead?')">
                                    🚆 Compare Train
                                </button>
                            </div>
                        `;
                    } else if (data.logged_record) {
                        actionHtml = `<div style="color: #34d399; font-weight: 700; font-size: var(--font-sm); margin-top: 8px;">✅ Verified and recorded into your profile!</div>`;
                    }

                    contentHtml = `
                        <div>🌿 <strong>Calculated Impact Breakdown:</strong></div>
                        ${cardsHtml}
                        ${actionHtml}
                    `;
                } else {
                    contentHtml = (typeof marked !== 'undefined') ? marked.parse(data.reply || '') : data.reply;
                }

                botRow.innerHTML = `
                    <div class="chat-avatar avatar-bot">🌱</div>
                    <div class="chat-bubble bubble-bot">${contentHtml}</div>
                `;
                feed.appendChild(botRow);
                feed.scrollTop = feed.scrollHeight;
                conversationHistory.push({ role: 'assistant', content: data.reply });

                if (data.logged_record) {
                    triggerConfettiCelebration();
                    loadDashboardData();
                }
            } catch (err) {
                typingRow.remove();
                showToast(`Chat error: ${err}`);
            }
        }

        function quickPrompt(text) {
            sendChatMessage(text);
        }

        function triggerNativeCamera() {
            document.getElementById('chat-camera-file').click();
        }

        function handleChatImageUpload(e) {
            const file = e.target.files[0];
            if (!file) return;
            switchTab('scanner');
            processVisionFile(file);
        }

        // Vision Scanner Pipeline
        function handleScannerFile(e) {
            const file = e.target.files[0];
            if (!file) return;
            processVisionFile(file);
        }

        function processVisionFile(file) {
            const reader = new FileReader();
            reader.onload = async function() {
                const b64 = reader.result;
                showToast('📷 Processing image with Gemini Vision AI...');
                try {
                    const res = await fetch('/api/scan-receipt', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            image_base64: b64,
                            api_key: localStorage.getItem('ecotracker_api_key') || ''
                        })
                    });
                    const data = await res.json();
                    renderScannerUI(data);
                } catch (err) {
                    showToast(`Scan error: ${err}`);
                }
            };
            reader.readAsDataURL(file);
        }

        async function loadSampleScan(type) {
            showToast(`Loading sample ${type}...`);
            const endpoint = type === 'utility_bill' ? '/api/scan-bill' : '/api/scan-receipt';
            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ doc_type: type })
                });
                const data = await res.json();
                renderScannerUI(data);
            } catch (err) {
                showToast(`Error: ${err}`);
            }
        }

        function renderScannerUI(data) {
            lastScannedPayload = data;
            document.getElementById('scanner-output').style.display = 'block';
            document.getElementById('scan-vendor-tag').innerText = data.vendor_or_utility || 'Verified Entity';
            document.getElementById('scan-title').innerText = `${data.document_type.replace('_', ' ').toUpperCase()} (${data.date || 'Current Cycle'})`;
            document.getElementById('scan-co2-total').innerText = `${data.total_co2e_kg} kg`;
            document.getElementById('scan-summary-msg').innerText = data.summary || '';

            const tbody = document.getElementById('scan-items-tbody');
            tbody.innerHTML = (data.items || []).map(item => `
                <tr>
                    <td style="font-weight: 700;">${item.name}</td>
                    <td>${item.quantity} ${item.unit || ''}</td>
                    <td style="font-weight: 800; color: #f87171;">${item.co2e_kg} kg</td>
                    <td style="color: #38bdf8;">${item.swap_suggestion}</td>
                    <td style="text-align: right; color: #34d399; font-weight: 700;">-${item.swap_savings_kg} kg</td>
                </tr>
            `).join('');

            showToast(`✓ Scanned: ${data.items ? data.items.length : 0} items extracted!`);
        }

        async function commitScanLog() {
            if (!lastScannedPayload) return;
            try {
                const res = await fetch('/api/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        category: lastScannedPayload.document_type === 'utility_bill' ? 'energy' : 'diet',
                        activity_details: `Scanned ${lastScannedPayload.document_type.replace('_', ' ')} (${lastScannedPayload.vendor_or_utility})`,
                        co2e_kg: lastScannedPayload.total_co2e_kg,
                        saved_co2e_kg: lastScannedPayload.total_potential_savings_kg || 0,
                        notes: `Vision Scan: ${lastScannedPayload.summary}`
                    })
                });
                triggerConfettiCelebration();
                showToast(`✅ Scanned document logged to profile (+${lastScannedPayload.total_co2e_kg} kg)`);
                loadDashboardData();
            } catch (err) {
                showToast(`Error: ${err}`);
            }
        }

        // What-If Simulator Pipeline
        async function triggerSimulatorCalc() {
            const km = parseFloat(document.getElementById('sim-km-slider').value);
            const mode = document.getElementById('sim-mode-select').value;
            const diet = parseInt(document.getElementById('sim-diet-slider').value);
            const solar = document.getElementById('sim-solar-box').checked;
            const heatpump = document.getElementById('sim-heatpump-box').checked;
            const flights = parseInt(document.getElementById('sim-flights-slider').value);

            document.getElementById('sim-km-disp').innerText = `${km} km/wk`;
            document.getElementById('sim-diet-disp').innerText = `${diet} days/wk`;
            document.getElementById('sim-flights-disp').innerText = `${flights} flight${flights !== 1 ? 's' : ''}`;

            try {
                const res = await fetch('/api/simulate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        weekly_commute_km: km,
                        transit_mode: mode,
                        meatless_days_per_week: diet,
                        has_rooftop_solar: solar,
                        has_heat_pump: heatpump,
                        annual_flights_avoided: flights
                    })
                });
                const data = await res.json();
                document.getElementById('sim-co2-1').innerText = `${data.projections.year_1.co2e_abated_tons} MT`;
                document.getElementById('sim-cash-1').innerText = `+$${data.projections.year_1.financial_savings_usd.toLocaleString()}`;

                document.getElementById('sim-co2-5').innerText = `${data.projections.year_5.co2e_abated_tons} MT`;
                document.getElementById('sim-cash-5').innerText = `+$${data.projections.year_5.financial_savings_usd.toLocaleString()}`;

                document.getElementById('sim-co2-10').innerText = `${data.projections.year_10.co2e_abated_tons} MT`;
                document.getElementById('sim-cash-10').innerText = `+$${data.projections.year_10.financial_savings_usd.toLocaleString()}`;

                document.getElementById('sim-summary-container').innerHTML = `
                    🌱 <strong>Annual Impact:</strong> ${data.summary} (${data.trees_equivalent_planted_annual} trees absorption equivalent).
                `;
            } catch (err) {
                console.error(err);
            }
        }

        // Leaderboard Data Pipeline
        async function loadLeaderboardData() {
            try {
                const res = await fetch('/api/leaderboard');
                const data = await res.json();
                const tbody = document.getElementById('leaderboard-tbody');
                if (data.leaderboard && data.leaderboard.length > 0) {
                    tbody.innerHTML = data.leaderboard.map((item, idx) => {
                        const rankClass = idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : idx === 2 ? 'rank-3' : 'rank-other';
                        const isCurrent = item.user_id === currentUserId;
                        return `
                            <tr style="${isCurrent ? 'background: rgba(16, 185, 129, 0.1); font-weight: 700;' : ''}">
                                <td><span class="rank-badge ${rankClass}">${idx + 1}</span></td>
                                <td>${item.user_id} ${isCurrent ? '<span class="status-badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 13px;">You</span>' : ''}</td>
                                <td>${item.total_activities} logged</td>
                                <td style="color: #34d399; font-weight: 700;">+${item.total_saved_kg} kg</td>
                                <td style="color: #f87171;">${item.total_emissions_kg} kg</td>
                                <td style="text-align: right; color: #c084fc; font-weight: 700;">${item.badge_count} 🏅</td>
                            </tr>
                        `;
                    }).join('');
                }
            } catch (err) {
                console.error(err);
            }
        }

        // FastMCP Calculator Options
        const MCP_OPTIONS = {
            transit: { label: 'Vehicle Mode', qtyLabel: 'Distance (km)', defaultVal: 45, items: [
                { val: 'gasoline car', txt: 'Gasoline Car (192 g/km)' },
                { val: 'diesel car', txt: 'Diesel Car (171 g/km)' },
                { val: 'suv', txt: 'SUV (245 g/km)' },
                { val: 'hybrid car', txt: 'Hybrid (110 g/km)' },
                { val: 'electric car', txt: 'Electric Car (45 g/km)' },
                { val: 'diesel bus', txt: 'City Bus (95 g/km)' },
                { val: 'electric train', txt: 'Electric Train (35 g/km)' },
                { val: 'bicycle', txt: 'Bicycle / Walking (0 g/km)' }
            ]},
            diet: { label: 'Food Item', qtyLabel: 'Weight (kg)', defaultVal: 0.5, items: [
                { val: 'beef', txt: 'Beef / Steak (60 kg CO2e/kg)' },
                { val: 'lamb', txt: 'Lamb (24.5 kg CO2e/kg)' },
                { val: 'cheese', txt: 'Cheese (21 kg CO2e/kg)' },
                { val: 'pork', txt: 'Pork (7.2 kg CO2e/kg)' },
                { val: 'chicken', txt: 'Chicken / Poultry (6.1 kg CO2e/kg)' },
                { val: 'milk', txt: 'Dairy Milk (3.15 kg CO2e/L)' }
            ]},
            appliance: { label: 'Appliance', qtyLabel: 'Units', defaultVal: 1, items: [
                { val: 'refrigerator', txt: 'Refrigerator (550 kWh/yr)' },
                { val: 'ac', txt: 'Air Conditioner (1800 kWh/yr)' },
                { val: 'washing machine', txt: 'Washing Machine (380 kWh/yr)' }
            ]},
            waste: { label: 'Material Diverted', qtyLabel: 'Quantity (kg)', defaultVal: 5, items: [
                { val: 'aluminum cans', txt: 'Aluminum Cans (High offset)' },
                { val: 'plastic bottles', txt: 'PET Plastic Bottles' },
                { val: 'food compost', txt: 'Food Compost (Avoids methane)' }
            ]}
        };

        function populateMcpItems(category) {
            const cfg = MCP_OPTIONS[category];
            document.getElementById('mcp-item-label').innerText = cfg.label;
            document.getElementById('mcp-qty-label').innerText = cfg.qtyLabel;
            document.getElementById('mcp-qty-input').value = cfg.defaultVal;
            const select = document.getElementById('mcp-item-select');
            select.innerHTML = cfg.items.map(it => `<option value="${it.val}">${it.txt}</option>`).join('');
        }

        async function runMcpCalculation() {
            const cat = document.getElementById('mcp-calc-category').value;
            const item = document.getElementById('mcp-item-select').value;
            const qty = parseFloat(document.getElementById('mcp-qty-input').value);

            try {
                const res = await fetch('/api/calculate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ calc_type: cat, item_or_mode: item, quantity: qty })
                });
                const data = await res.json();
                const box = document.getElementById('mcp-results-box');
                box.style.display = 'block';
                box.innerHTML = `
                    <div class="result-card-inner">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: var(--font-md);">${data.summary}</strong>
                            <span class="emissions-badge">${data.co2e_kg} kg CO2e</span>
                        </div>
                        <div class="swap-recommendation">${data.recommendation}</div>
                        <button class="btn btn-primary" style="margin-top: 10px;" onclick="logDirectChoice('${data.category}', '${data.summary.replace(/'/g, "\\'")}', ${data.co2e_kg}, ${data.saved_co2e_kg})">
                            💾 Log to Activity History
                        </button>
                    </div>
                `;
            } catch (err) {
                showToast(`Error: ${err}`);
            }
        }

        async function logHabitPreset(category, details, co2, saved) {
            await logDirectChoice(category, details, co2, saved);
        }

        async function logDirectChoice(cat, details, co2, saved) {
            try {
                const res = await fetch('/api/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        category: cat,
                        activity_details: details,
                        co2e_kg: co2,
                        saved_co2e_kg: saved,
                        notes: '1-click choice'
                    })
                });
                triggerConfettiCelebration();
                showToast(`✅ Choice recorded (+${co2} kg CO2e)`);
                loadDashboardData();
            } catch (err) {
                showToast(`Error logging: ${err}`);
            }
        }

        // Enterprise ESG
        async function loadEsgReport() {
            try {
                const res = await fetch(`/api/esg-report?format=json&user_id=${encodeURIComponent(currentUserId)}`);
                const data = await res.json();
                const m = data.metrics;
                document.getElementById('esg-scope1-num').innerHTML = `${m.scope_breakdown_mt.scope_1_direct.toFixed(3)} <span style="font-size: 14px; color: var(--text-secondary);">MT</span>`;
                document.getElementById('esg-scope2-num').innerHTML = `${m.scope_breakdown_mt.scope_2_electricity.toFixed(3)} <span style="font-size: 14px; color: var(--text-secondary);">MT</span>`;
                document.getElementById('esg-scope3-num').innerHTML = `${m.scope_breakdown_mt.scope_3_value_chain.toFixed(3)} <span style="font-size: 14px; color: var(--text-secondary);">MT</span>`;
                document.getElementById('esg-audit-badge').innerText = data.verification_hash;
                document.getElementById('esg-report-link').href = `/api/esg-report?format=html&user_id=${encodeURIComponent(currentUserId)}`;
            } catch (err) {
                console.error(err);
            }
        }

        // Dashboard Summary & History
        async function loadDashboardData() {
            try {
                const res = await fetch(`/api/summary?user_id=${encodeURIComponent(currentUserId)}`);
                const data = await res.json();
                lastSummaryPayload = data;

                document.getElementById('kpi-gross-val').innerHTML = `${data.total_emissions_kg} <span style="font-size: 15px; color: var(--text-secondary);">kg CO2e</span>`;
                document.getElementById('kpi-saved-val').innerHTML = `${data.total_saved_kg} <span style="font-size: 15px; color: var(--text-secondary);">kg CO2e</span>`;
                document.getElementById('kpi-count-val').innerText = `${data.total_entries} activities logged`;
                document.getElementById('desk-history-count').innerText = data.total_entries;

                const pct = Math.min(100, data.budget_used_pct || 0);
                document.getElementById('kpi-budget-val').innerText = `${pct}% utilized`;
                document.getElementById('kpi-budget-bar').style.width = `${pct}%`;

                // Proactive Budget Warning Banner in Chat
                const alertBanner = document.getElementById('budget-alert-banner');
                if (alertBanner) {
                    if (pct >= 100) {
                        alertBanner.style.display = 'block';
                        alertBanner.style.background = 'rgba(239, 68, 68, 0.15)';
                        alertBanner.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                        alertBanner.style.color = '#f87171';
                        alertBanner.innerHTML = `🚨 <strong>Budget Limit Exceeded:</strong> You have logged ${data.total_emissions_kg} kg against your daily budget of ${data.daily_budget_kg} kg CO2e. Try green eco-swaps for subsequent activities today!`;
                    } else if (pct >= 80) {
                        alertBanner.style.display = 'block';
                        alertBanner.style.background = 'rgba(245, 158, 11, 0.15)';
                        alertBanner.style.borderColor = 'rgba(245, 158, 11, 0.4)';
                        alertBanner.style.color = '#fbbf24';
                        alertBanner.innerHTML = `⚠️ <strong>Approaching Daily Target:</strong> ${pct}% of your daily carbon budget (${data.daily_budget_kg} kg) has been used.`;
                    } else {
                        alertBanner.style.display = 'none';
                    }
                }

                if (data.badges && data.badges.length > 0) {
                    document.getElementById('kpi-badges-val').innerText = data.badges.length;
                    document.getElementById('kpi-badge-desc').innerText = data.badges.map(b => b.name).join(', ');
                }

                if (data.daily_budget_kg) {
                    document.getElementById('budget-range-input').value = data.daily_budget_kg;
                    document.getElementById('budget-slider-disp').innerText = `${data.daily_budget_kg} kg/day`;
                }

                // Render History Rows
                const tbody = document.getElementById('history-rows-tbody');
                if (data.recent_logs && data.recent_logs.length > 0) {
                    tbody.innerHTML = data.recent_logs.map(r => `
                        <tr>
                            <td>${r.timestamp ? r.timestamp.slice(0, 10) : 'Recent'}</td>
                            <td><span class="status-badge" style="background: rgba(255,255,255,0.06); font-size: 13.5px;">${r.scope || 'Scope 3'}</span></td>
                            <td style="text-transform: capitalize;">${r.category}</td>
                            <td>${r.activity_details}</td>
                            <td style="font-weight: 700; color: #f87171;">${r.co2e_kg} kg</td>
                            <td style="font-weight: 700; color: #34d399;">${r.saved_co2e_kg} kg</td>
                            <td style="text-align: right;">
                                <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 14px;" onclick="deleteLogEntry(${r.id})">✕</button>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 26px;">No activities recorded yet.</td></tr>`;
                }

                renderCategoryChart();
                loadDailyTrends();
            } catch (err) {
                console.error(err);
            }
        }

        function renderCategoryChart() {
            const canvas = document.getElementById('analyticsDoughnut');
            if (!canvas || !lastSummaryPayload) return;
            const cats = lastSummaryPayload.by_category || [];
            const labels = cats.length > 0 ? cats.map(c => c.category) : ['No logs yet'];
            const vals = cats.length > 0 ? cats.map(c => c.total_co2e) : [1];
            const colors = ['#10b981', '#06b6d4', '#f59e0b', '#a855f7', '#f43f5e', '#64748b'];

            if (doughnutChartInstance) doughnutChartInstance.destroy();
            doughnutChartInstance = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: vals,
                        backgroundColor: colors,
                        borderColor: 'transparent',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 12 } } }
                    },
                    cutout: '68%'
                }
            });
        }

        // 30-Day Daily Trends Line Chart
        async function loadDailyTrends() {
            const canvas = document.getElementById('dailyTrendChart');
            if (!canvas) return;
            try {
                const res = await fetch(`/api/daily-trends?user_id=${encodeURIComponent(currentUserId)}`);
                const data = await res.json();
                const trends = data.trends || [];
                
                const labels = trends.length > 0 ? trends.map(t => t.date.slice(5)) : ['Today'];
                const grossVals = trends.length > 0 ? trends.map(t => t.daily_emissions) : [0];
                const savedVals = trends.length > 0 ? trends.map(t => t.daily_saved) : [0];

                if (trendChartInstance) trendChartInstance.destroy();
                trendChartInstance = new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Gross Emissions (kg)',
                                data: grossVals,
                                borderColor: '#f87171',
                                backgroundColor: 'rgba(248, 113, 113, 0.1)',
                                tension: 0.35,
                                fill: true,
                                pointRadius: 4
                            },
                            {
                                label: 'Carbon Saved (kg)',
                                data: savedVals,
                                borderColor: '#34d399',
                                backgroundColor: 'rgba(52, 211, 153, 0.1)',
                                tension: 0.35,
                                fill: true,
                                pointRadius: 4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { labels: { color: '#94a3b8', font: { size: 12 } } }
                        },
                        scales: {
                            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
                            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } } }
                        }
                    }
                });
            } catch (err) {
                console.error(err);
            }
        }

        function updateBudgetSlider(val) {
            document.getElementById('budget-slider-disp').innerText = `${parseFloat(val).toFixed(1)} kg/day`;
        }

        async function saveUserBudget() {
            const val = parseFloat(document.getElementById('budget-range-input').value);
            try {
                await fetch('/api/goal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: currentUserId, daily_budget_kg: val })
                });
                showToast(`🎯 Budget goal updated to ${val} kg/day`);
                loadDashboardData();
            } catch (err) {
                showToast(`Error: ${err}`);
            }
        }

        async function deleteLogEntry(id) {
            try {
                await fetch(`/api/log/${id}?user_id=${encodeURIComponent(currentUserId)}`, { method: 'DELETE' });
                showToast(`Deleted log #${id}`);
                loadDashboardData();
            } catch (err) {
                showToast(`Error: ${err}`);
            }
        }

        function exportDataCSV() {
            window.location.href = `/api/export-csv?user_id=${encodeURIComponent(currentUserId)}`;
        }

        function updateOffsetDisp(kg) {
            const trees = Math.round(kg / 21);
            const cost = (kg * 0.03).toFixed(2);
            document.getElementById('offset-calc-disp').innerText = `${kg} kg (~${trees} trees, $${cost})`;
        }

        function triggerConfettiCelebration() {
            if (typeof confetti === 'function') {
                confetti({
                    particleCount: 45,
                    spread: 60,
                    origin: { y: 0.8 },
                    colors: ['#10b981', '#06b6d4', '#34d399', '#f59e0b']
                });
            }
        }

        // Scorecard Generator
        function generateScorecardModal() {
            const modal = document.getElementById('scorecard-modal');
            const saved = lastSummaryPayload ? lastSummaryPayload.total_saved_kg : 0.0;
            const trees = Math.round(saved / 21.8);
            document.getElementById('scorecard-user-label').innerText = `Certified for: ${currentUserId}`;
            document.getElementById('scorecard-saved-val').innerText = `${saved} kg CO2e`;
            document.getElementById('scorecard-trees-val').innerText = `Equivalent to ~${trees} mature trees absorbing carbon for 1 full year!`;
            modal.classList.add('open');
        }
        function closeScorecardModal() {
            document.getElementById('scorecard-modal').classList.remove('open');
        }
        function copyScorecardText() {
            const saved = lastSummaryPayload ? lastSummaryPayload.total_saved_kg : 0.0;
            const text = `🌱 I've avoided ${saved} kg of CO2e through verified eco-swaps with EcoTracker AI! Track and abate your lifestyle emissions at EcoTracker.`;
            navigator.clipboard.writeText(text);
            showToast('📋 Copied scorecard text to clipboard!');
        }

        // Modal Helpers
        function openApiKeyModal() {
            document.getElementById('api-key-modal').classList.add('open');
            document.getElementById('modal-api-key-input').value = localStorage.getItem('ecotracker_api_key') || '';
        }
        function closeApiKeyModal() {
            document.getElementById('api-key-modal').classList.remove('open');
        }
        function saveApiKeyModal() {
            const key = document.getElementById('modal-api-key-input').value.trim();
            if (key) {
                localStorage.setItem('ecotracker_api_key', key);
                showToast('✨ Free Cloud LLM key saved!');
            } else {
                localStorage.removeItem('ecotracker_api_key');
                showToast('Key cleared; using conversational rules engine.');
            }
            closeApiKeyModal();
        }

        function openResetModal() {
            document.getElementById('reset-history-modal').classList.add('open');
        }
        function closeResetModal() {
            document.getElementById('reset-history-modal').classList.remove('open');
        }
        async function confirmResetAll() {
            try {
                await fetch(`/api/logs/all?user_id=${encodeURIComponent(currentUserId)}`, { method: 'DELETE' });
                showToast('All activity records wiped.');
                closeResetModal();
                loadDashboardData();
            } catch (err) {
                showToast(`Error: ${err}`);
            }
        }

        // PWA Service Worker Registration
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').catch(() => {});
            });
        }

        // Initialize On Load
        window.addEventListener('DOMContentLoaded', () => {
            const savedTheme = localStorage.getItem('ecotracker_theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
            document.documentElement.setAttribute('data-font-scale', 'large');
            populateMcpItems('transit');
            loadDashboardData();
            fetchLiveGridStatus();
            fetchAmbientWeather();
        });
    </script>
</body>
</html>
"""
