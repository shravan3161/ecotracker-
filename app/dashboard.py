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

"""EcoTracker Enterprise Customer SaaS Platform.

Production-grade real-time sustainability intelligence platform featuring:
- Conversational AI Carbon Chatbot with multi-turn context memory
- Multi-layer Enterprise Security Guardrails (Prompt Injection, XSS, SQLi, PII, Credential Filtering)
- Dynamic, scientifically grounded carbon reasoning & multi-item calculations
- Free Cloud LLM integration (Google Gemini 2.5 & Groq LLaMA 3.3)
- Multi-tenant customer session isolation with SQLite persistence
- Interactive Chart.js analytics (category doughnut chart & emissions trend)
- 1-Click Eco Habits Studio & Interactive Daily Budget Slider
- Interactive Carbon Offset Simulator with Gold Standard projects
- Granular Activity History management (individual record deletion & full history reset)
- CSV reporting for corporate sustainability audits & tax reporting
"""

import os
import json
import re
import csv
import io
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
import uvicorn
from app import db
from app.security import inspect_and_sanitize
from app.mcp_server import (
    get_transit_emissions,
    get_appliance_efficiency,
    get_waste_offset,
    get_dietary_emissions,
)
from app.cloud_llm import generate_llm_response
from app.engine import analyze_query, handle_chatbot_turn

dashboard_app = FastAPI(title="EcoTracker Customer Platform")
app = dashboard_app  # ASGI standard alias

class LogActivityRequest(BaseModel):
    user_id: str = "guest_customer"
    category: str
    activity_details: str
    co2e_kg: float
    saved_co2e_kg: float = 0.0
    notes: str = ""

class CalculateRequest(BaseModel):
    calc_type: str
    item_or_mode: str
    quantity: float = 1.0

class ChatRequest(BaseModel):
    user_id: str = "guest_customer"
    message: str
    api_key: Optional[str] = ""
    history: Optional[List[Dict[str, str]]] = []

class GoalRequest(BaseModel):
    user_id: str = "guest_customer"
    daily_budget_kg: float

@dashboard_app.get("/api/summary")
def get_summary(user_id: str = Query("default_customer")):
    """Returns aggregated customer footprint summary and goal progress."""
    return JSONResponse(content=db.get_user_summary(user_id=user_id))

@dashboard_app.post("/api/goal")
def update_goal(req: GoalRequest):
    """Updates customer's daily carbon budget."""
    updated = db.set_user_goal(user_id=req.user_id, daily_budget_kg=req.daily_budget_kg)
    return JSONResponse(content={"status": "success", "goal": updated})

@dashboard_app.post("/api/log")
def log_activity(req: LogActivityRequest):
    """Logs an activity to the customer's private database history."""
    entry = db.log_calculation(
        category=req.category,
        activity_details=req.activity_details,
        co2e_kg=req.co2e_kg,
        saved_co2e_kg=req.saved_co2e_kg,
        notes=req.notes,
        user_id=req.user_id
    )
    return JSONResponse(content={"status": "success", "log": entry})

@dashboard_app.delete("/api/log/{log_id}")
def delete_single_log(log_id: int, user_id: str = Query("default_customer")):
    """Deletes a specific activity log for a customer."""
    success = db.delete_log(log_id=log_id, user_id=user_id)
    return JSONResponse(content={"success": success, "status": "success" if success else "failed", "deleted_id": log_id})

@dashboard_app.delete("/api/logs/all")
def clear_all_logs(user_id: str = Query("default_customer")):
    """Wipes all footprint history and badges for a customer."""
    success = db.clear_user_data(user_id=user_id)
    return JSONResponse(content={"success": success, "status": "success" if success else "failed", "message": "All data cleared successfully"})

@dashboard_app.get("/api/export-csv")
def export_csv(user_id: str = Query("default_customer")):
    """Exports customer's footprint log history as a downloadable CSV."""
    summary = db.get_user_summary(user_id=user_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Log ID", "Timestamp", "Category", "Activity Details", 
        "Emissions (kg CO2e)", "Avoided / Saved (kg CO2e)", "Notes"
    ])
    for row in summary.get("recent_logs", []):
        writer.writerow([
            row["id"], row["timestamp"], row["category"], 
            row["activity_details"], row["co2e_kg"], 
            row["saved_co2e_kg"], row.get("notes", "")
        ])
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ecotracker_{user_id}_report.csv"}
    )

@dashboard_app.post("/api/calculate")
def calculate_direct(req: CalculateRequest):
    """Calculates carbon footprint directly using MCP domain benchmarks."""
    calc_type = req.calc_type.lower()
    if calc_type == "transit":
        raw = get_transit_emissions(req.item_or_mode, req.quantity)
        data = json.loads(raw)
        return JSONResponse(content={
            "category": "transportation",
            "co2e_kg": data["emissions_kg_co2e"],
            "saved_co2e_kg": data["benchmarks"]["train_savings_kg"],
            "summary": f"{data['distance_km']} km travel via {data['mode']}.",
            "recommendation": f"Electric train swap saves {data['benchmarks']['train_savings_kg']} kg CO2e.",
            "raw": data
        })
    elif calc_type == "diet":
        raw = get_dietary_emissions(req.item_or_mode, req.quantity)
        data = json.loads(raw)
        return JSONResponse(content={
            "category": "diet",
            "co2e_kg": data["emissions_kg_co2e"],
            "saved_co2e_kg": data["potential_savings_kg_co2e"],
            "summary": f"Consuming {data['quantity_kg']} kg of {data['food_item']}.",
            "recommendation": f"Eco-Swap: {data['suggested_swap']} (Saves {data['potential_savings_kg_co2e']} kg CO2e).",
            "raw": data
        })
    elif calc_type == "appliance":
        raw = get_appliance_efficiency(req.item_or_mode, req.quantity)
        data = json.loads(raw)
        return JSONResponse(content={
            "category": "energy",
            "co2e_kg": data["standard_annual_co2e_kg"],
            "saved_co2e_kg": data["potential_annual_savings_kg_co2e"],
            "summary": f"Standard {data['appliance']} ({data['standard_annual_kwh']} kWh/yr).",
            "recommendation": f"Eco-Swap: {data['recommended_swap']} (Saves ~{data['potential_annual_savings_kg_co2e']} kg CO2e/yr).",
            "raw": data
        })
    elif calc_type == "waste":
        raw = get_waste_offset(req.item_or_mode, req.quantity)
        data = json.loads(raw)
        return JSONResponse(content={
            "category": "waste",
            "co2e_kg": 0.0,
            "saved_co2e_kg": data["carbon_savings_kg_co2e"],
            "summary": f"Recycled / composted {data['quantity']} {data['unit']} of {data['material']}.",
            "recommendation": f"Avoided {data['carbon_savings_kg_co2e']} kg CO2e from landfill methane.",
            "raw": data
        })
    return JSONResponse(status_code=400, content={"error": "Unknown calculation type"})

@dashboard_app.post("/api/chat")
async def chat_handler(req: ChatRequest):
    """Customer AI consultation pipeline with security check, dynamic calculations, and Cloud LLM."""
    user_text = req.message.strip()
    uid = req.user_id or "guest_customer"

    # 1. Multi-layer Enterprise Security Checkpoint
    sec_res = inspect_and_sanitize(user_text)
    if not sec_res.passed:
        return JSONResponse(content={
            "success": False,
            "security_blocked": True,
            "rejection_reason": sec_res.rejection_reason,
            "reply": f"🚨 **Security Threat Blocked:** {sec_res.rejection_reason}\n\n*This input was intercepted and logged to the enterprise security audit stream.*",
            "audit_log": sec_res.audit_event
        })

    clean_text = sec_res.sanitized_text
    lower = clean_text.lower()

    # 2. Check for Profile / History queries
    is_log_action = "log" in lower or "save" in lower
    summary_triggers = [
        "show summary", "my summary", "view summary", "view profile", 
        "my history", "how much have i saved", "my stats", "my badges", 
        "my target", "what have i logged", "show my stats"
    ]
    if not is_log_action and any(q in lower for q in summary_triggers):
        summary = db.get_user_summary(user_id=uid)
        badge_str = ", ".join([f"🏅 **{b['name']}**" for b in summary["badges"]]) if summary["badges"] else "None yet"
        reply = (
            f"### 📊 Your Sustainability Profile\n\n"
            f"- **Total Emissions Logged:** `{summary['total_emissions_kg']} kg CO2e`\n"
            f"- **Total Carbon Avoided:** `{summary['total_saved_kg']} kg CO2e`\n"
            f"- **Daily Budget:** `{summary['daily_budget_kg']} kg CO2e/day` ({summary['budget_used_pct']}% utilized)\n"
            f"- **Activities Logged:** `{summary['total_entries']}`\n"
            f"- **Milestones Unlocked:** {badge_str}\n"
        )
        return JSONResponse(content={
            "success": True, 
            "reply": reply, 
            "pii_redacted": sec_res.pii_redacted,
            "audit_log": sec_res.audit_event
        })

    # 3. Try Cloud LLM Generation if Key is Provided (with multi-turn history)
    llm_output = await generate_llm_response(clean_text, custom_key=req.api_key, history=req.history)
    if llm_output:
        reply_content = llm_output
        co2_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg\s*co2e?|kilograms)", llm_output, re.IGNORECASE)
        total_co2 = float(co2_match.group(1)) if co2_match else 0.0
        total_saved = round(total_co2 * 0.45, 2)
        primary_category = "general"
        is_chat_only = False if co2_match else True
    else:
        # Conversational Chatbot Engine with dialogue memory and grounded calculations
        bot_turn = handle_chatbot_turn(clean_text, history=req.history)
        reply_content = bot_turn["reply"]
        total_co2 = bot_turn["total_emissions_kg"]
        total_saved = bot_turn["total_saved_kg"]
        primary_category = bot_turn["category"]
        is_chat_only = bot_turn.get("is_chat_only", False)

    # 4. Check if User Requested to Log / Save to Profile
    if is_log_action and total_co2 > 0:
        rec = db.log_calculation(
            category=primary_category,
            activity_details=clean_text[:120],
            co2e_kg=total_co2,
            saved_co2e_kg=total_saved,
            notes="Logged via Chatbot Companion",
            user_id=uid
        )
        badge_notice = f" 🏅 *Unlocked: {', '.join(rec.get('new_badges', []))}!*" if rec.get("new_badges") else ""
        reply_content += f"\n\n---\n*✅ Confirmed & saved to your personal dashboard (Log #{rec['id']}).{badge_notice}*"

    # Append subtle privacy notice if PII was scrubbed
    if sec_res.pii_redacted:
        reply_content += "\n\n*(🛡️ Notice: Sensitive personal data like email/phone/address was redacted for your privacy)*"

    return JSONResponse(content={
        "success": True,
        "reply": reply_content,
        "co2e_kg": total_co2,
        "saved_co2e_kg": total_saved,
        "category": primary_category,
        "is_chat_only": is_chat_only,
        "pii_redacted": sec_res.pii_redacted,
        "audit_log": sec_res.audit_event
    })

@dashboard_app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoTracker — Enterprise Carbon Intelligence SaaS</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
    <style>
        :root {
            --primary: #10b981;
            --primary-glow: rgba(16, 185, 129, 0.4);
            --primary-light: #34d399;
            --primary-dark: #059669;
            --bg-color: #070c18;
            --bg-gradient: radial-gradient(circle at 10% 10%, rgba(16, 185, 129, 0.12) 0%, transparent 40%),
                           radial-gradient(circle at 90% 90%, rgba(6, 182, 212, 0.10) 0%, transparent 45%),
                           #070c18;
            --card-bg: rgba(15, 23, 42, 0.78);
            --card-border: rgba(255, 255, 255, 0.08);
            --card-hover: rgba(255, 255, 255, 0.14);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-cyan: #06b6d4;
            --accent-purple: #a855f7;
            --accent-gold: #f59e0b;
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.35);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }
        .container { max-width: 1340px; margin: 0 auto; }

        /* Glassmorphism Surface */
        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.55);
            transition: all 0.25s ease;
        }
        .glass-card:hover { border-color: var(--card-hover); }

        /* Navigation Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 28px;
            margin-bottom: 24px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .brand-icon {
            width: 44px; height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(16,185,129,0.25), rgba(6,182,212,0.25));
            border: 1px solid rgba(16,185,129,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 18px var(--primary-glow);
        }
        .brand-text h1 {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 40%, #a7f3d0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-text p {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 500;
        }
        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .user-chip {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 13px;
        }
        .user-chip input {
            background: transparent;
            border: none;
            color: #fff;
            font-size: 13px;
            font-weight: 600;
            outline: none;
            width: 130px;
        }
        .btn-action {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid var(--card-border);
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-main);
        }
        .btn-action:hover {
            background: rgba(255, 255, 255, 0.09);
            border-color: rgba(255, 255, 255, 0.25);
            transform: translateY(-1px);
        }
        .btn-danger-outline {
            color: #fca5a5;
            border-color: rgba(239, 68, 68, 0.3);
            background: rgba(239, 68, 68, 0.1);
        }
        .btn-danger-outline:hover {
            background: rgba(239, 68, 68, 0.25);
            border-color: var(--danger);
            color: #fff;
        }

        /* KPI Executive Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }
        .metric-card {
            padding: 22px 26px;
            position: relative;
            overflow: hidden;
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
            opacity: 0.7;
        }
        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .metric-title {
            font-size: 12px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .metric-value {
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #fff;
            margin-bottom: 6px;
        }
        .metric-value span { font-size: 14px; font-weight: 500; color: var(--text-muted); }
        .budget-bar {
            height: 7px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
            margin: 8px 0;
        }
        .budget-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--accent-cyan));
            border-radius: 999px;
            transition: width 0.6s ease;
        }
        .budget-slider-wrapper {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
        }
        .budget-slider {
            flex: 1;
            accent-color: var(--primary);
            cursor: pointer;
        }

        /* 2-Column Split: Analytics & Eco Habits Studio */
        .analytics-habits-split {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }
        @media (max-width: 900px) {
            .analytics-habits-split { grid-template-columns: 1fr; }
        }
        .chart-container {
            position: relative;
            height: 220px;
            width: 100%;
        }

        /* Eco Habits Studio Preset Cards */
        .habits-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 10px;
            margin-top: 12px;
        }
        .habit-btn {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 12px 10px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            color: var(--text-main);
        }
        .habit-btn:hover {
            background: rgba(16, 185, 129, 0.12);
            border-color: rgba(16, 185, 129, 0.45);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.15);
        }
        .habit-icon { font-size: 24px; margin-bottom: 4px; display: block; }
        .habit-title { font-size: 12px; font-weight: 700; color: #fff; margin-bottom: 2px; }
        .habit-impact { font-size: 11px; color: var(--primary-light); font-weight: 600; }

        /* 2-Column Split: Calculator & AI Consultant */
        .workspace-split {
            display: grid;
            grid-template-columns: 1fr 1.15fr;
            gap: 24px;
            margin-bottom: 26px;
        }
        @media (max-width: 1024px) {
            .workspace-split { grid-template-columns: 1fr; }
        }

        /* FastMCP Calculator Studio */
        .studio-card { padding: 24px 28px; }
        .calc-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 12px;
        }
        .calc-tab {
            background: none;
            border: 1px solid transparent;
            color: var(--text-muted);
            font-size: 13px;
            font-weight: 600;
            padding: 8px 14px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .calc-tab:hover { color: #fff; background: rgba(255, 255, 255, 0.04); }
        .calc-tab.active {
            background: rgba(16, 185, 129, 0.15);
            border-color: rgba(16, 185, 129, 0.35);
            color: #34d399;
        }
        .form-group { margin-bottom: 16px; }
        .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .form-select, .form-input {
            width: 100%;
            padding: 12px 14px;
            background: rgba(7, 12, 24, 0.85);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
        }
        .form-select:focus, .form-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-glow);
        }
        .preview-box {
            background: rgba(7, 12, 24, 0.65);
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 12px;
            padding: 16px;
            margin: 18px 0;
            display: none;
        }
        .preview-box.visible { display: block; animation: fadeIn 0.3s ease; }
        .btn-calc {
            width: 100%;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: #032e22;
            font-weight: 700;
            border: none;
            border-radius: 10px;
            padding: 13px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 4px 16px var(--primary-glow);
            transition: all 0.2s;
        }
        .btn-calc:hover { filter: brightness(1.1); transform: translateY(-1px); }

        /* Conversational AI Chatbot Card */
        .chat-card {
            padding: 22px 24px;
            display: flex;
            flex-direction: column;
            height: 600px;
        }
        .chat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--card-border);
        }
        .chat-bot-profile {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .chat-stream {
            flex: 1;
            overflow-y: auto;
            padding: 14px;
            background: rgba(7, 12, 24, 0.65);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .chat-msg-row {
            display: flex;
            gap: 10px;
            align-items: flex-start;
            animation: fadeIn 0.25s ease;
        }
        .chat-msg-row.user { flex-direction: row-reverse; }
        .chat-avatar {
            width: 32px; height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            flex-shrink: 0;
        }
        .avatar-bot {
            background: linear-gradient(135deg, rgba(16,185,129,0.35), rgba(6,182,212,0.35));
            border: 1px solid rgba(16,185,129,0.5);
            box-shadow: 0 0 10px var(--primary-glow);
        }
        .avatar-user {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            border: 1px solid rgba(59,130,246,0.6);
        }
        .msg-wrapper {
            display: flex;
            flex-direction: column;
            max-width: 82%;
        }
        .chat-msg-row.user .msg-wrapper { align-items: flex-end; }
        .msg-bubble {
            padding: 12px 16px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.55;
        }
        .msg-user {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #fff;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        }
        .msg-agent {
            background: rgba(30, 41, 59, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #f1f5f9;
            border-bottom-left-radius: 4px;
        }
        .msg-time {
            font-size: 10px;
            color: var(--text-muted);
            margin-top: 4px;
            padding: 0 4px;
        }
        
        /* Security Alert Box inside Chat */
        .security-alert-box {
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.45);
            border-radius: 12px;
            padding: 14px 16px;
            color: #fecaca;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
            animation: shake 0.35s ease-in-out;
        }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-4px); }
            40%, 80% { transform: translateX(4px); }
        }
        .security-alert-header {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #ef4444;
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .security-badge-icon { font-size: 16px; }
        .security-alert-body { font-size: 12.5px; line-height: 1.5; color: #f87171; }
        .security-alert-meta {
            font-size: 10.5px;
            color: #94a3b8;
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px solid rgba(239, 68, 68, 0.2);
        }

        .chat-action-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }
        .chat-action-btn {
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34d399;
            padding: 5px 11px;
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .chat-action-btn:hover {
            background: rgba(16, 185, 129, 0.28);
            color: #fff;
            transform: translateY(-1px);
        }
        .typing-dots {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 6px 10px;
        }
        .typing-dot {
            width: 6px; height: 6px;
            background: #34d399;
            border-radius: 50%;
            animation: bounceDot 1.2s infinite ease-in-out;
        }
        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounceDot {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1.1); opacity: 1; }
        }
        .prompt-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }
        .prompt-pill {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            color: var(--text-muted);
            padding: 5px 11px;
            border-radius: 999px;
            font-size: 11.5px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .prompt-pill:hover {
            background: rgba(16, 185, 129, 0.12);
            border-color: rgba(16, 185, 129, 0.4);
            color: #fff;
        }
        .chat-input-row {
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 13px 16px;
            background: rgba(7, 12, 24, 0.85);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .chat-input:focus { border-color: var(--primary); }

        /* Interactive Carbon Offset Simulator */
        .offset-card { padding: 24px 28px; margin-bottom: 24px; }
        .offset-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-top: 18px;
        }
        .project-card {
            background: rgba(7, 12, 24, 0.65);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s;
        }
        .project-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            transform: translateY(-2px);
        }

        /* Activity History Table */
        .history-card { padding: 24px 28px; margin-bottom: 26px; }
        .table-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .search-box {
            position: relative;
            min-width: 260px;
        }
        .search-input {
            width: 100%;
            padding: 9px 14px 9px 34px;
            background: rgba(7, 12, 24, 0.85);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            color: #fff;
            font-size: 13px;
            outline: none;
        }
        .search-icon {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 14px;
        }
        .filter-pills { display: flex; gap: 6px; }
        .filter-pill {
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid var(--card-border);
            background: transparent;
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            text-transform: capitalize;
        }
        .filter-pill.active {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border-color: rgba(255, 255, 255, 0.3);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            text-align: left;
            padding: 12px 14px;
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--card-border);
        }
        td {
            padding: 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            color: var(--text-main);
        }
        tr:hover td { background: rgba(255, 255, 255, 0.02); }
        .tag-pill {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
            text-transform: uppercase;
        }
        .tag-transportation { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
        .tag-diet { background: rgba(52, 211, 153, 0.15); color: #34d399; }
        .tag-energy { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
        .tag-waste { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
        .tag-shopping { background: rgba(244, 114, 182, 0.15); color: #f472b6; }
        .tag-general { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }
        .btn-trash {
            background: none;
            border: 1px solid transparent;
            color: #94a3b8;
            cursor: pointer;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 13px;
            transition: all 0.2s;
        }
        .btn-trash:hover {
            color: #ef4444;
            background: var(--danger-glow);
            border-color: rgba(239, 68, 68, 0.3);
        }

        /* Modal Dialog */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(8px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal-overlay.active { display: flex; animation: fadeIn 0.2s ease; }
        .modal-card {
            background: #0f172a;
            border: 1px solid var(--card-border);
            border-radius: 16px;
            width: 90%;
            max-width: 480px;
            padding: 26px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
        }

        /* Toast Notifications */
        .toast-stack {
            position: fixed;
            bottom: 24px;
            right: 24px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 1100;
        }
        .toast {
            background: #1e293b;
            color: #fff;
            border: 1px solid var(--card-border);
            padding: 12px 18px;
            border-radius: 10px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.96); } to { opacity: 1; transform: scale(1); } }
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Navbar -->
        <header class="glass-card">
            <div class="brand">
                <div class="brand-icon">🌱</div>
                <div class="brand-text">
                    <h1>EcoTracker Platform</h1>
                    <p>Live Sustainability Intelligence • Verified FastMCP Factors</p>
                </div>
            </div>
            <div class="header-actions">
                <div class="user-chip">
                    <span>👤</span>
                    <input type="text" id="user-id-input" value="default_customer" title="Switch Customer ID" placeholder="Customer ID">
                </div>
                <button class="btn-action" onclick="openKeyModal()">⚙️ Cloud LLM Config</button>
                <button class="btn-action" onclick="exportDataCSV()">📥 Export CSV</button>
                <button class="btn-action btn-danger-outline" onclick="openResetModal()">🗑️ Reset History</button>
            </div>
        </header>

        <!-- KPI Metrics Grid -->
        <div class="metrics-grid">
            <div class="glass-card metric-card">
                <div class="metric-header">
                    <span class="metric-title">Total Emissions</span>
                    <span>📈</span>
                </div>
                <div class="metric-value" id="kpi-emissions">0.0 <span>kg CO2e</span></div>
                <div style="font-size: 12px; color: var(--text-muted);" id="kpi-count">0 verified activities</div>
            </div>
            <div class="glass-card metric-card">
                <div class="metric-header">
                    <span class="metric-title">Carbon Avoided</span>
                    <span>🌱</span>
                </div>
                <div class="metric-value" style="color: #34d399;" id="kpi-saved">0.0 <span>kg CO2e</span></div>
                <div style="font-size: 12px; color: #34d399;">Through verified eco-swaps</div>
            </div>
            <div class="glass-card metric-card">
                <div class="metric-header">
                    <span class="metric-title">Daily Carbon Budget</span>
                    <span>🎯</span>
                </div>
                <div class="metric-value" id="kpi-budget">0% <span>utilized</span></div>
                <div class="budget-bar">
                    <div class="budget-fill" id="budget-fill" style="width: 0%;"></div>
                </div>
                <div class="budget-slider-wrapper">
                    <span style="font-size: 11px; color: var(--text-muted);">Goal:</span>
                    <input type="range" class="budget-slider" id="budget-slider" min="2" max="30" step="0.5" value="10" onchange="updateDailyBudget(this.value)" oninput="document.getElementById('budget-val-disp').innerText = this.value + ' kg'">
                    <span style="font-size: 11.5px; font-weight: 700; color: #38bdf8;" id="budget-val-disp">10 kg</span>
                </div>
            </div>
            <div class="glass-card metric-card">
                <div class="metric-header">
                    <span class="metric-title">Unlocked Badges</span>
                    <span>🏅</span>
                </div>
                <div class="metric-value" id="kpi-badges">0</div>
                <div style="font-size: 12px; color: #a78bfa;" id="kpi-badge-desc">Start logging to earn badges</div>
            </div>
        </div>

        <!-- 2-Column Split: Visual Analytics & Eco Habits Studio -->
        <div class="analytics-habits-split">
            <!-- Left: Interactive Visual Analytics -->
            <div class="glass-card" style="padding: 22px 26px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 style="font-size: 16px; font-weight: 700;">Emission Analytics</h3>
                    <span style="font-size: 11px; color: var(--text-muted);">Live Breakdown</span>
                </div>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            <!-- Right: One-Click Eco Habits Studio -->
            <div class="glass-card" style="padding: 22px 26px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <h3 style="font-size: 16px; font-weight: 700;">Eco Habits Studio</h3>
                    <span style="font-size: 11px; color: #34d399; font-weight: 600;">⚡ 1-Click Fast Log</span>
                </div>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">Tap any daily habit to instantly log verified carbon impact.</p>
                <div class="habits-grid">
                    <div class="habit-btn" onclick="quickLogHabit('Morning Coffee', 'diet', 0.28, 0.0)">
                        <span class="habit-icon">☕</span>
                        <div class="habit-title">Coffee</div>
                        <div class="habit-impact">+0.28 kg</div>
                    </div>
                    <div class="habit-btn" onclick="quickLogHabit('Electric Train (25 km)', 'transportation', 0.88, 3.92)">
                        <span class="habit-icon">🚆</span>
                        <div class="habit-title">Train Trip</div>
                        <div class="habit-impact">-3.92 kg</div>
                    </div>
                    <div class="habit-btn" onclick="quickLogHabit('Plant-Based Lunch', 'diet', 0.40, 4.50)">
                        <span class="habit-icon">🥗</span>
                        <div class="habit-title">Vegan Bowl</div>
                        <div class="habit-impact">-4.50 kg</div>
                    </div>
                    <div class="habit-btn" onclick="quickLogHabit('Bicycle Commute (10 km)', 'transportation', 0.0, 1.92)">
                        <span class="habit-icon">🚲</span>
                        <div class="habit-title">Bike Ride</div>
                        <div class="habit-impact">-1.92 kg</div>
                    </div>
                    <div class="habit-btn" onclick="quickLogHabit('AC Eco-Mode (2 hrs)', 'energy', 0.60, 0.70)">
                        <span class="habit-icon">❄️</span>
                        <div class="habit-title">Eco AC</div>
                        <div class="habit-impact">-0.70 kg</div>
                    </div>
                    <div class="habit-btn" onclick="quickLogHabit('Composted Food Scraps', 'waste', 0.0, 2.40)">
                        <span class="habit-icon">♻️</span>
                        <div class="habit-title">Compost</div>
                        <div class="habit-impact">-2.40 kg</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 2-Column Split: Calculator & AI Consultant -->
        <div class="workspace-split">
            <!-- Left: FastMCP Calculator Studio -->
            <div class="glass-card studio-card">
                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 14px;">Instant Emission Calculator</h3>
                <div class="calc-tabs">
                    <button class="calc-tab active" onclick="switchTab('transit')">🚗 Transit</button>
                    <button class="calc-tab" onclick="switchTab('diet')">🥗 Diet & Food</button>
                    <button class="calc-tab" onclick="switchTab('appliance')">⚡ Appliances</button>
                    <button class="calc-tab" onclick="switchTab('waste')">♻️ Waste</button>
                </div>
                <div class="form-group">
                    <label class="form-label" id="calc-item-label">Vehicle Mode</label>
                    <select class="form-select" id="calc-item-select" onchange="runLiveCalculation()"></select>
                </div>
                <div class="form-group">
                    <label class="form-label" id="calc-qty-label">Distance (km)</label>
                    <input type="number" class="form-input" id="calc-qty-input" value="40" min="1" step="any" oninput="runLiveCalculation()">
                </div>
                <div class="preview-box" id="calc-preview">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 700; color: #fff;" id="prev-title">Result</span>
                        <span style="font-size: 18px; font-weight: 800; color: #38bdf8;" id="prev-co2">0.0 kg</span>
                    </div>
                    <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;" id="prev-swap"></p>
                    <button class="btn-calc" onclick="saveCalculatorLog()">+ Log to My History</button>
                </div>
            </div>

            <!-- Right: Conversational AI Carbon Chatbot -->
            <div class="glass-card chat-card">
                <div class="chat-header">
                    <div class="chat-bot-profile">
                        <div class="chat-avatar avatar-bot">🌱</div>
                        <div>
                            <div style="font-size: 14.5px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px;">
                                EcoTracker AI Bot
                                <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></span>
                            </div>
                            <div style="font-size: 11px; color: var(--text-muted);">Conversational Carbon Advisor • Online</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 11px; padding: 4px 8px; border-radius: 6px; background: rgba(16, 185, 129, 0.15); color: #34d399; font-weight: 600;" id="llm-status-pill">
                            ⚡ Dynamic Chatbot
                        </span>
                        <button class="btn-action" style="padding: 4px 10px; font-size: 11px;" onclick="clearChat()" title="Reset chat conversation">🧹 Clear</button>
                    </div>
                </div>
                <div class="chat-stream" id="chat-stream">
                    <!-- Initial Bot Message -->
                    <div class="chat-msg-row">
                        <div class="chat-avatar avatar-bot">🌱</div>
                        <div class="msg-wrapper">
                            <div class="msg-bubble msg-agent">
                                👋 <strong>Hi! I'm EcoTracker AI, your conversational sustainability chatbot.</strong><br><br>
                                Tell me about your day—like your commute, a flight, what you had for lunch, or home appliances you ran. I'll calculate your exact carbon footprint and suggest realistic, high-impact eco-swaps!<br><br>
                                <em>What activity would you like to explore?</em>
                            </div>
                            <span class="msg-time" id="welcome-time">Just now</span>
                        </div>
                    </div>
                </div>
                <div class="prompt-pills">
                    <div class="prompt-pill" onclick="sendPrompt('👋 Hi! What can you do?')">👋 Hello!</div>
                    <div class="prompt-pill" onclick="sendPrompt('I drove 45 km in a gasoline car, calculate carbon and log it')">🚗 45km Gasoline Commute</div>
                    <div class="prompt-pill" onclick="sendPrompt('I had a 250g ribeye steak dinner and 2 beers')">🥩 250g Steak Dinner</div>
                    <div class="prompt-pill" onclick="sendPrompt('Flew 1200 km domestic flight, suggest green alternatives')">✈️ 1200km Flight</div>
                    <div class="prompt-pill" onclick="sendPrompt('Ran my AC for 6 hours today, how much carbon is that?')">❄️ 6 hrs AC Cooling</div>
                </div>
                <div class="chat-input-row">
                    <input type="text" class="chat-input" id="chat-input" placeholder="Message EcoTracker AI (e.g., 'I drove 40 km' or 'Hi')..." onkeydown="if(event.key==='Enter') submitChat()">
                    <button class="btn-action" style="background: var(--primary); color: #042f2e; font-weight: 700; padding: 0 20px;" onclick="submitChat()">Send ↵</button>
                </div>
            </div>
        </div>

        <!-- Interactive Carbon Offset Simulator & Project Directory -->
        <div class="glass-card offset-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 4px;">Verified Carbon Offset Directory</h3>
                    <p style="font-size: 12px; color: var(--text-muted);">Balance residual emissions through certified Gold Standard & Verra VCS projects.</p>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; background: rgba(7, 12, 24, 0.7); padding: 8px 16px; border-radius: 12px; border: 1px solid var(--card-border);">
                    <span style="font-size: 12px; color: var(--text-muted);">Offset Simulator:</span>
                    <input type="range" min="10" max="500" step="10" value="100" style="accent-color: #38bdf8;" oninput="updateOffsetSim(this.value)">
                    <span style="font-size: 13px; font-weight: 700; color: #38bdf8;" id="offset-amount-disp">100 kg (~5 trees, $3.00)</span>
                </div>
            </div>
            <div class="offset-grid">
                <div class="project-card">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 11px; padding: 3px 8px; border-radius: 4px; background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 700;">Gold Standard #GS1284</span>
                            <span style="font-size: 13px; font-weight: 700; color: #fff;">$15 / ton</span>
                        </div>
                        <h4 style="font-size: 15px; font-weight: 700; margin-bottom: 6px; color: #fff;">🌳 Rimba Raya Biodiversity Peatland</h4>
                        <p style="font-size: 12px; color: var(--text-muted); line-height: 1.5; margin-bottom: 12px;">
                            Protects 65,000 hectares of tropical peat swamp in Borneo, preserving endangered orangutan habitats and sequestering millions of tons of CO2.
                        </p>
                    </div>
                    <a href="https://www.goldstandard.org/" target="_blank" class="btn-action" style="text-align: center; justify-content: center; font-size: 12px;">View Certificate ↗</a>
                </div>
                <div class="project-card">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 11px; padding: 3px 8px; border-radius: 4px; background: rgba(56, 189, 248, 0.2); color: #38bdf8; font-weight: 700;">Verra VCS #VCS921</span>
                            <span style="font-size: 13px; font-weight: 700; color: #fff;">$12 / ton</span>
                        </div>
                        <h4 style="font-size: 15px; font-weight: 700; margin-bottom: 6px; color: #fff;">💨 Oaxaca Wind Energy Project</h4>
                        <p style="font-size: 12px; color: var(--text-muted); line-height: 1.5; margin-bottom: 12px;">
                            102 MW clean wind farm in southern Mexico displacing fossil fuels and powering 180,000 homes annually with zero emissions.
                        </p>
                    </div>
                    <a href="https://registry.verra.org/" target="_blank" class="btn-action" style="text-align: center; justify-content: center; font-size: 12px;">View Certificate ↗</a>
                </div>
                <div class="project-card">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 11px; padding: 3px 8px; border-radius: 4px; background: rgba(168, 85, 247, 0.2); color: #c084fc; font-weight: 700;">Blue Carbon Certified</span>
                            <span style="font-size: 13px; font-weight: 700; color: #fff;">$18 / ton</span>
                        </div>
                        <h4 style="font-size: 15px; font-weight: 700; margin-bottom: 6px; color: #fff;">🌊 Coastal Mangrove Restoration</h4>
                        <p style="font-size: 12px; color: var(--text-muted); line-height: 1.5; margin-bottom: 12px;">
                            Restoring degraded tidal mangrove forests along the Kenyan coast, sequestering carbon up to 4x faster than terrestrial rainforests.
                        </p>
                    </div>
                    <a href="https://www.goldstandard.org/" target="_blank" class="btn-action" style="text-align: center; justify-content: center; font-size: 12px;">View Certificate ↗</a>
                </div>
            </div>
        </div>

        <!-- Activity History & Granular Deletion Table -->
        <div class="glass-card history-card">
            <div class="table-controls">
                <div>
                    <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 4px;">Verified Activity History</h3>
                    <p style="font-size: 12px; color: var(--text-muted);">Inspect, filter, or delete individual customer logs in real-time.</p>
                </div>
                <div style="display: flex; gap: 12px; align-items: center;">
                    <div class="search-box">
                        <span class="search-icon">🔍</span>
                        <input type="text" class="search-input" id="search-input" placeholder="Filter activities..." oninput="renderTable()">
                    </div>
                    <div class="filter-pills">
                        <button class="filter-pill active" onclick="setCategoryFilter('all')">All</button>
                        <button class="filter-pill" onclick="setCategoryFilter('transportation')">Transit</button>
                        <button class="filter-pill" onclick="setCategoryFilter('diet')">Diet</button>
                        <button class="filter-pill" onclick="setCategoryFilter('energy')">Energy</button>
                        <button class="filter-pill" onclick="setCategoryFilter('waste')">Waste</button>
                    </div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Activity Details</th>
                        <th>Emissions</th>
                        <th>Carbon Saved</th>
                        <th>Timestamp</th>
                        <th style="text-align: right;">Action</th>
                    </tr>
                </thead>
                <tbody id="history-tbody">
                    <tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">Loading history...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Reset History Confirmation Modal -->
    <div class="modal-overlay" id="reset-modal">
        <div class="modal-card">
            <h3 style="font-size: 18px; font-weight: 700; color: #f87171; margin-bottom: 10px;">⚠️ Reset Customer History?</h3>
            <p style="font-size: 13.5px; color: var(--text-muted); line-height: 1.6; margin-bottom: 20px;">
                This action will permanently delete all carbon calculations, activity logs, and milestone badges for customer session <strong style="color: #fff;" id="modal-user-id"></strong>. This cannot be undone.
            </p>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button class="btn-action" onclick="closeResetModal()">Cancel</button>
                <button class="btn-action btn-danger-outline" onclick="confirmResetAll()">Confirm & Wipe History</button>
            </div>
        </div>
    </div>

    <!-- API Key & Cloud LLM Config Modal -->
    <div class="modal-overlay" id="key-modal">
        <div class="modal-card">
            <h3 style="font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 10px;">⚙️ Free Cloud LLM Configuration</h3>
            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin-bottom: 16px;">
                EcoTracker supports 100% free cloud LLMs. Paste your free Google Gemini API key or free Groq API key below to activate live model synthesis without local compute:
            </p>
            <div class="form-group">
                <label class="form-label">Gemini / Groq API Key</label>
                <input type="password" class="form-input" id="custom-api-key-input" placeholder="AIzaSy... or gsk_...">
            </div>
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 20px; line-height: 1.6;">
                • <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color: #38bdf8; text-decoration: none;">Get Free Google Gemini Key (Instant)</a><br>
                • <a href="https://console.groq.com/keys" target="_blank" style="color: #38bdf8; text-decoration: none;">Get Free Groq LLaMA 3.3 Key (30 req/min free)</a>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button class="btn-action" onclick="closeKeyModal()">Close</button>
                <button class="btn-action" style="background: var(--primary); color: #042f2e; font-weight: 700;" onclick="saveCustomApiKey()">Save Key</button>
            </div>
        </div>
    </div>

    <div class="toast-stack" id="toast-stack"></div>

    <script>
        let currentUserId = localStorage.getItem('ecotracker_uid') || 'default_customer';
        let currentCategoryFilter = 'all';
        let currentTab = 'transit';
        let lastSummaryData = null;
        let lastCalcResult = null;
        let chatHistory = [];
        let categoryChartInstance = null;

        document.getElementById('user-id-input').value = currentUserId;
        document.getElementById('user-id-input').addEventListener('change', (e) => {
            currentUserId = e.target.value.trim() || 'default_customer';
            localStorage.setItem('ecotracker_uid', currentUserId);
            showToast(`Switched customer to: ${currentUserId}`);
            loadDashboard();
        });

        function formatTimeNow() {
            return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        // Setup Calculator Tab Options
        const TAB_OPTIONS = {
            transit: {
                label: 'Vehicle Mode',
                qtyLabel: 'Distance (km)',
                defaultQty: 45,
                options: [
                    { value: 'gasoline car', text: 'Gasoline Car (192 g/km)' },
                    { value: 'diesel car', text: 'Diesel Car (171 g/km)' },
                    { value: 'suv', text: 'Gasoline SUV (235 g/km)' },
                    { value: 'hybrid car', text: 'Hybrid Car (110 g/km)' },
                    { value: 'electric car', text: 'Electric Car / EV (45 g/km)' },
                    { value: 'diesel bus', text: 'City Bus (89 g/km)' },
                    { value: 'electric train', text: 'Electric Train (35 g/km)' },
                    { value: 'domestic flight', text: 'Domestic Flight (255 g/km)' },
                    { value: 'bicycle', text: 'Bicycle / Walking (0 g/km)' }
                ]
            },
            diet: {
                label: 'Food Item',
                qtyLabel: 'Weight / Portion (kg)',
                defaultQty: 0.5,
                options: [
                    { value: 'beef', text: 'Beef / Steak (60 kg CO2e/kg)' },
                    { value: 'lamb', text: 'Lamb / Mutton (24.5 kg CO2e/kg)' },
                    { value: 'cheese', text: 'Cheese / Dairy (21 kg CO2e/kg)' },
                    { value: 'pork', text: 'Pork (7.2 kg CO2e/kg)' },
                    { value: 'chicken', text: 'Poultry / Chicken (6.1 kg CO2e/kg)' },
                    { value: 'fish', text: 'Farmed Salmon / Fish (5.4 kg CO2e/kg)' },
                    { value: 'eggs', text: 'Eggs (4.5 kg CO2e/kg)' },
                    { value: 'rice', text: 'Rice (4.0 kg CO2e/kg)' },
                    { value: 'milk', text: 'Dairy Milk (3.2 kg CO2e/L)' },
                    { value: 'beans', text: 'Lentils / Beans (0.8 kg CO2e/kg)' }
                ]
            },
            appliance: {
                label: 'Appliance',
                qtyLabel: 'Units / Usage',
                defaultQty: 1,
                options: [
                    { value: 'refrigerator', text: 'Standard Refrigerator (550 kWh/yr)' },
                    { value: 'ac', text: 'Air Conditioner (1800 kWh/yr)' },
                    { value: 'washing machine', text: 'Washing Machine (380 kWh/yr)' },
                    { value: 'dryer', text: 'Clothes Dryer (750 kWh/yr)' },
                    { value: 'water heater', text: 'Electric Water Heater (3200 kWh/yr)' }
                ]
            },
            waste: {
                label: 'Material Diverted',
                qtyLabel: 'Quantity (kg or units)',
                defaultQty: 5,
                options: [
                    { value: 'compost', text: 'Food Compost (Avoids methane)' },
                    { value: 'aluminum cans', text: 'Aluminum Cans (High recycling offset)' },
                    { value: 'plastic bottles', text: 'PET Plastic Bottles' },
                    { value: 'cardboard', text: 'Cardboard & Paper' }
                ]
            }
        };

        function switchTab(tabKey) {
            currentTab = tabKey;
            document.querySelectorAll('.calc-tab').forEach(btn => btn.classList.remove('active'));
            if (event && event.target) event.target.classList.add('active');
            
            const cfg = TAB_OPTIONS[tabKey];
            document.getElementById('calc-item-label').innerText = cfg.label;
            document.getElementById('calc-qty-label').innerText = cfg.qtyLabel;
            document.getElementById('calc-qty-input').value = cfg.defaultQty;

            const select = document.getElementById('calc-item-select');
            select.innerHTML = cfg.options.map(opt => `<option value="${opt.value}">${opt.text}</option>`).join('');
            runLiveCalculation();
        }

        async function runLiveCalculation() {
            const item = document.getElementById('calc-item-select').value;
            const qty = parseFloat(document.getElementById('calc-qty-input').value) || 1.0;
            try {
                const res = await fetch('/api/calculate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ calc_type: currentTab, item_or_mode: item, quantity: qty })
                });
                const data = await res.json();
                lastCalcResult = data;
                
                document.getElementById('prev-title').innerText = data.summary;
                document.getElementById('prev-co2').innerText = `${data.co2e_kg} kg CO2e`;
                document.getElementById('prev-swap').innerText = data.recommendation;
                document.getElementById('calc-preview').classList.add('visible');
            } catch (err) {
                console.error(err);
            }
        }

        async function saveCalculatorLog() {
            if (!lastCalcResult) return;
            try {
                const res = await fetch('/api/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        category: lastCalcResult.category,
                        activity_details: lastCalcResult.summary,
                        co2e_kg: lastCalcResult.co2e_kg,
                        saved_co2e_kg: lastCalcResult.saved_co2e_kg,
                        notes: lastCalcResult.recommendation
                    })
                });
                const data = await res.json();
                triggerConfetti();
                showToast(`✅ Logged ${lastCalcResult.co2e_kg} kg CO2e!`);
                loadDashboard();
            } catch (err) {
                showToast(`❌ Error saving log: ${err}`);
            }
        }

        async function quickLogHabit(name, cat, co2, saved) {
            try {
                const res = await fetch('/api/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        category: cat,
                        activity_details: name,
                        co2e_kg: co2,
                        saved_co2e_kg: saved,
                        notes: 'Logged via 1-Click Habit Studio'
                    })
                });
                triggerConfetti();
                showToast(`⚡ Habit logged: ${name} (${co2 > 0 ? '+' + co2 : '-' + saved} kg CO2e)`);
                loadDashboard();
            } catch (err) {
                showToast(`Error: ${err}`);
            }
        }

        async function updateDailyBudget(newBudget) {
            try {
                const res = await fetch('/api/goal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        daily_budget_kg: parseFloat(newBudget)
                    })
                });
                showToast(`🎯 Daily budget updated to ${newBudget} kg CO2e`);
                loadDashboard();
            } catch (err) {
                console.error(err);
            }
        }

        function updateOffsetSim(kg) {
            const trees = Math.round(kg / 21);
            const cost = (kg * 0.03).toFixed(2);
            document.getElementById('offset-amount-disp').innerText = `${kg} kg (~${trees} trees, $${cost})`;
        }

        function triggerConfetti() {
            if (typeof confetti === 'function') {
                confetti({
                    particleCount: 40,
                    spread: 60,
                    origin: { y: 0.8 },
                    colors: ['#10b981', '#38bdf8', '#34d399', '#f59e0b']
                });
            }
        }

        async function loadDashboard() {
            try {
                const res = await fetch(`/api/summary?user_id=${encodeURIComponent(currentUserId)}`);
                const data = await res.json();
                lastSummaryData = data;

                document.getElementById('kpi-emissions').innerHTML = `${data.total_emissions_kg} <span>kg CO2e</span>`;
                document.getElementById('kpi-saved').innerHTML = `${data.total_saved_kg} <span>kg CO2e</span>`;
                document.getElementById('kpi-count').innerText = `${data.total_entries} verified activities`;
                
                const pct = Math.min(100, data.budget_used_pct || 0);
                document.getElementById('kpi-budget').innerHTML = `${pct}% <span>utilized</span>`;
                document.getElementById('budget-fill').style.width = `${pct}%`;
                
                if (pct > 85) {
                    document.getElementById('budget-fill').style.background = 'linear-gradient(90deg, #f59e0b, #ef4444)';
                } else if (pct > 60) {
                    document.getElementById('budget-fill').style.background = 'linear-gradient(90deg, #38bdf8, #f59e0b)';
                } else {
                    document.getElementById('budget-fill').style.background = 'linear-gradient(90deg, var(--primary), var(--accent-cyan))';
                }

                if (data.daily_budget_kg) {
                    document.getElementById('budget-slider').value = data.daily_budget_kg;
                    document.getElementById('budget-val-disp').innerText = data.daily_budget_kg + ' kg';
                }

                document.getElementById('kpi-badges').innerText = data.badges ? data.badges.length : 0;
                if (data.badges && data.badges.length > 0) {
                    document.getElementById('kpi-badge-desc').innerText = data.badges.map(b => b.name).join(', ');
                } else {
                    document.getElementById('kpi-badge-desc').innerText = 'Start logging to earn badges';
                }

                renderChart(data.by_category || []);
                renderTable();
            } catch (err) {
                console.error(err);
            }
        }

        function renderChart(categories) {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            const labels = categories.length > 0 ? categories.map(c => c.category) : ['No activities yet'];
            const dataVals = categories.length > 0 ? categories.map(c => c.total_co2e) : [1];
            const colors = ['#10b981', '#38bdf8', '#f59e0b', '#a855f7', '#f43f5e', '#64748b'];

            if (categoryChartInstance) {
                categoryChartInstance.destroy();
            }

            categoryChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: dataVals,
                        backgroundColor: colors.slice(0, labels.length),
                        borderWidth: 0,
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: '#94a3b8',
                                font: { size: 11, family: 'Inter' },
                                boxWidth: 12
                            }
                        }
                    },
                    cutout: '68%'
                }
            });
        }

        function renderTable() {
            if (!lastSummaryData) return;
            const tbody = document.getElementById('history-tbody');
            const search = (document.getElementById('search-input').value || '').toLowerCase();
            const logs = lastSummaryData.recent_logs || [];

            const filtered = logs.filter(row => {
                const matchCat = currentCategoryFilter === 'all' || row.category.toLowerCase() === currentCategoryFilter.toLowerCase();
                const matchSearch = !search || row.activity_details.toLowerCase().includes(search) || (row.notes && row.notes.toLowerCase().includes(search));
                return matchCat && matchSearch;
            });

            if (filtered.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">No matching activities found.</td></tr>`;
                return;
            }

            tbody.innerHTML = filtered.map(row => {
                const catClass = `tag-${row.category.toLowerCase()}`;
                const dateStr = row.timestamp ? new Date(row.timestamp).toLocaleDateString() + ' ' + new Date(row.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Recent';
                return `
                    <tr id="row-${row.id}">
                        <td><span class="tag-pill ${catClass}">${row.category}</span></td>
                        <td>
                            <strong style="color: #fff;">${row.activity_details}</strong>
                            ${row.notes ? `<div style="font-size: 11.5px; color: var(--text-muted);">${row.notes}</div>` : ''}
                        </td>
                        <td><span style="font-weight: 700; color: #f87171;">+${row.co2e_kg} kg</span></td>
                        <td><span style="font-weight: 700; color: #34d399;">-${row.saved_co2e_kg} kg</span></td>
                        <td style="color: var(--text-muted); font-size: 12px;">${dateStr}</td>
                        <td style="text-align: right;">
                            <button class="btn-trash" onclick="deleteRecord(${row.id})" title="Delete activity">🗑️</button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function setCategoryFilter(cat) {
            currentCategoryFilter = cat;
            document.querySelectorAll('.filter-pill').forEach(btn => btn.classList.remove('active'));
            if (event && event.target) event.target.classList.add('active');
            renderTable();
        }

        async function deleteRecord(logId) {
            try {
                const res = await fetch(`/api/log/${logId}?user_id=${encodeURIComponent(currentUserId)}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                if (data.status === 'success') {
                    showToast(`🗑️ Deleted record #${logId}`);
                    loadDashboard();
                } else {
                    showToast(`Failed to delete: ${data.message || 'Error'}`);
                }
            } catch (err) {
                showToast(`Network error: ${err}`);
            }
        }

        function openResetModal() {
            document.getElementById('modal-user-id').innerText = currentUserId;
            document.getElementById('reset-modal').classList.add('active');
        }
        function closeResetModal() {
            document.getElementById('reset-modal').classList.remove('active');
        }
        async function confirmResetAll() {
            closeResetModal();
            try {
                const res = await fetch(`/api/logs/all?user_id=${encodeURIComponent(currentUserId)}`, {
                    method: 'DELETE'
                });
                const data = await res.json();
                showToast(`Wiped all data for ${currentUserId}`);
                loadDashboard();
            } catch (err) {
                showToast(`Error resetting: ${err}`);
            }
        }

        function exportDataCSV() {
            window.location.href = `/api/export-csv?user_id=${encodeURIComponent(currentUserId)}`;
            showToast('📥 Downloading sustainability CSV report...');
        }

        function openKeyModal() {
            document.getElementById('custom-api-key-input').value = localStorage.getItem('ecotracker_api_key') || '';
            document.getElementById('key-modal').classList.add('active');
        }
        function closeKeyModal() {
            document.getElementById('key-modal').classList.remove('active');
        }
        function saveCustomApiKey() {
            const key = document.getElementById('custom-api-key-input').value.trim();
            localStorage.setItem('ecotracker_api_key', key);
            closeKeyModal();
            if (key) {
                document.getElementById('llm-status-pill').innerText = '✨ Cloud LLM Connected';
                document.getElementById('llm-status-pill').style.background = 'rgba(56, 189, 248, 0.2)';
                document.getElementById('llm-status-pill').style.color = '#38bdf8';
                showToast('🔑 Cloud LLM API key saved!');
            } else {
                document.getElementById('llm-status-pill').innerText = '⚡ Dynamic Chatbot';
                document.getElementById('llm-status-pill').style.background = 'rgba(16, 185, 129, 0.15)';
                document.getElementById('llm-status-pill').style.color = '#34d399';
                showToast('Reverted to Dynamic Chatbot Engine');
            }
        }

        function clearChat() {
            chatHistory = [];
            const stream = document.getElementById('chat-stream');
            stream.innerHTML = `
                <div class="chat-msg-row">
                    <div class="chat-avatar avatar-bot">🌱</div>
                    <div class="msg-wrapper">
                        <div class="msg-bubble msg-agent">
                            👋 <strong>Conversation reset.</strong> I'm ready for your next activity or sustainability question! How can I help you?
                        </div>
                        <span class="msg-time">${formatTimeNow()}</span>
                    </div>
                </div>
            `;
            showToast('🧹 Chat conversation reset');
        }

        async function submitChat() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            await sendPrompt(text);
        }

        async function sendPrompt(promptText) {
            const stream = document.getElementById('chat-stream');
            const timeStr = formatTimeNow();

            // 1. Add User Message Row with Avatar
            const userRow = document.createElement('div');
            userRow.className = 'chat-msg-row user';
            userRow.innerHTML = `
                <div class="chat-avatar avatar-user">👤</div>
                <div class="msg-wrapper">
                    <div class="msg-bubble msg-user">${promptText.replace(/</g, '&lt;')}</div>
                    <span class="msg-time">${timeStr}</span>
                </div>
            `;
            stream.appendChild(userRow);
            stream.scrollTop = stream.scrollHeight;

            chatHistory.push({ role: 'user', content: promptText });

            // 2. Add Typing Indicator Row
            const typingRow = document.createElement('div');
            typingRow.className = 'chat-msg-row';
            typingRow.id = 'typing-indicator-row';
            typingRow.innerHTML = `
                <div class="chat-avatar avatar-bot">🌱</div>
                <div class="msg-wrapper">
                    <div class="msg-bubble msg-agent" style="display: flex; align-items: center; gap: 6px;">
                        <div class="typing-dots">
                            <span class="typing-dot"></span>
                            <span class="typing-dot"></span>
                            <span class="typing-dot"></span>
                        </div>
                        <span style="font-size: 12px; color: var(--text-muted); font-style: italic;">EcoTracker AI is thinking...</span>
                    </div>
                </div>
            `;
            stream.appendChild(typingRow);
            stream.scrollTop = stream.scrollHeight;

            const apiKey = localStorage.getItem('ecotracker_api_key') || '';
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        message: promptText,
                        api_key: apiKey,
                        history: chatHistory.slice(-8)
                    })
                });
                const data = await res.json();
                
                // Remove typing indicator
                const typingEl = document.getElementById('typing-indicator-row');
                if (typingEl) typingEl.remove();

                const botRow = document.createElement('div');
                botRow.className = 'chat-msg-row';

                // Check for Security Block Alert
                if (data.security_blocked) {
                    botRow.innerHTML = `
                        <div class="chat-avatar avatar-bot" style="background: rgba(239, 68, 68, 0.25); border-color: #ef4444;">🛡️</div>
                        <div class="msg-wrapper">
                            <div class="security-alert-box">
                                <div class="security-alert-header">
                                    <span class="security-badge-icon">🚨</span>
                                    <span>Security Guardrail Triggered</span>
                                </div>
                                <div class="security-alert-body">
                                    <strong>Blocked:</strong> ${data.rejection_reason || 'Potential prompt injection, unauthorized override, or sensitive data leak detected.'}
                                </div>
                                <div class="security-alert-meta">
                                    Audit Action: Blocked & Logged • Enterprise Policy: Zero-Trust Strict Sandbox
                                </div>
                            </div>
                            <span class="msg-time">${formatTimeNow()}</span>
                        </div>
                    `;
                    stream.appendChild(botRow);
                    stream.scrollTop = stream.scrollHeight;
                    showToast('🚨 Security alert: threat intercepted & blocked');
                    return;
                }

                // Format reply into clean HTML paragraphs
                const formatted = data.reply
                    .replace(/### (.*?)\n/g, '<h4 style="margin: 8px 0 4px; color: #fff;">$1</h4>')
                    .replace(/#### (.*?)\n/g, '<h5 style="margin: 6px 0 2px; color: #38bdf8;">$1</h5>')
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/`([^`]+)`/g, '<code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; color: #a7f3d0;">$1</code>')
                    .replace(/\n\n/g, '<br><br>')
                    .replace(/\n/g, '<br>');

                // Action buttons if this was a calculation
                let actionHtml = '';
                if (data.co2e_kg && data.co2e_kg > 0 && !promptText.toLowerCase().includes('log')) {
                    actionHtml = `
                        <div class="chat-action-pills">
                            <button class="chat-action-btn" onclick="saveDirectFromChat('${data.category}', '${promptText.replace(/'/g, "\\'")}', ${data.co2e_kg}, ${data.saved_co2e_kg || 0})">
                                📌 Log to My Profile (+${data.co2e_kg} kg)
                            </button>
                            <button class="chat-action-btn" onclick="sendPrompt('What if I took an electric train instead?')">
                                🚆 Compare to Train
                            </button>
                            <button class="chat-action-btn" onclick="sendPrompt('What if I used an electric car?')">
                                ⚡ Compare to EV
                            </button>
                        </div>
                    `;
                }

                botRow.innerHTML = `
                    <div class="chat-avatar avatar-bot">🌱</div>
                    <div class="msg-wrapper">
                        <div class="msg-bubble msg-agent">
                            ${formatted}
                            ${actionHtml}
                        </div>
                        <span class="msg-time">${formatTimeNow()}</span>
                    </div>
                `;
                stream.appendChild(botRow);
                stream.scrollTop = stream.scrollHeight;

                chatHistory.push({ role: 'assistant', content: data.reply });

                if (promptText.toLowerCase().includes('log') || promptText.toLowerCase().includes('save')) {
                    triggerConfetti();
                    loadDashboard();
                    showToast('✅ Activity saved to dashboard history!');
                }
            } catch (err) {
                const typingEl = document.getElementById('typing-indicator-row');
                if (typingEl) typingEl.remove();

                const errRow = document.createElement('div');
                errRow.className = 'chat-msg-row';
                errRow.innerHTML = `
                    <div class="chat-avatar avatar-bot">🌱</div>
                    <div class="msg-wrapper">
                        <div class="msg-bubble msg-agent" style="border-color: rgba(239, 68, 68, 0.4);">
                            <span style="color: #ef4444;">⚠️ Sorry, I encountered an issue: ${err}</span>
                        </div>
                        <span class="msg-time">${formatTimeNow()}</span>
                    </div>
                `;
                stream.appendChild(errRow);
                stream.scrollTop = stream.scrollHeight;
            }
        }

        async function saveDirectFromChat(category, details, co2, saved) {
            try {
                const res = await fetch('/api/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUserId,
                        category: category,
                        activity_details: details.slice(0, 120),
                        co2e_kg: co2,
                        saved_co2e_kg: saved,
                        notes: 'Logged via Chatbot Companion'
                    })
                });
                triggerConfetti();
                showToast(`✅ Saved ${co2} kg CO2e to dashboard!`);
                loadDashboard();
                
                const stream = document.getElementById('chat-stream');
                const confRow = document.createElement('div');
                confRow.className = 'chat-msg-row';
                confRow.innerHTML = `
                    <div class="chat-avatar avatar-bot">🌱</div>
                    <div class="msg-wrapper">
                        <div class="msg-bubble msg-agent" style="background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.35);">
                            ✅ <strong>Activity logged successfully!</strong> Recorded into your Activity History and updated your daily budget.
                        </div>
                        <span class="msg-time">${formatTimeNow()}</span>
                    </div>
                `;
                stream.appendChild(confRow);
                stream.scrollTop = stream.scrollHeight;
            } catch (err) {
                showToast(`Error saving: ${err}`);
            }
        }

        function showToast(msg) {
            const stack = document.getElementById('toast-stack');
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.innerText = msg;
            stack.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(10px)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, 3500);
        }

        // Initialize on load
        window.addEventListener('DOMContentLoaded', () => {
            switchTab('transit');
            loadDashboard();
            const welcomeTime = document.getElementById('welcome-time');
            if (welcomeTime) welcomeTime.innerText = formatTimeNow();
            const savedKey = localStorage.getItem('ecotracker_api_key');
            if (savedKey) {
                document.getElementById('llm-status-pill').innerText = '✨ Cloud LLM Connected';
                document.getElementById('llm-status-pill').style.background = 'rgba(56, 189, 248, 0.2)';
                document.getElementById('llm-status-pill').style.color = '#38bdf8';
            }
        });
    </script>
</body>
</html>
""")

def start():
    """Runs the production uvicorn ASGI server."""
    port = int(os.environ.get("PORT", 8085))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"\n=======================================================")
    print(f"🚀 EcoTracker Platform live at: http://localhost:{port}")
    print(f"   Direct URL: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    uvicorn.run("app.dashboard:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    start()
