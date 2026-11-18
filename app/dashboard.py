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

Clean, high-end Linear/Vercel-inspired App Shell design:
- Uncluttered Sidebar Navigation (Chatbot, Analytics, Habits, History, Offsets)
- True Multi-turn Conversational AI Carbon Chatbot
- Interactive Chart.js category analytics & live budget progress
- One-click daily habit presets with celebratory confetti
- Granular SQLite data management (individual record deletion & full wipe)
- Enterprise multi-layer security checkpoint
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
            "reply": f"🚨 **Security Threat Blocked:** {sec_res.rejection_reason}\n\n*Action intercepted and logged to enterprise security audit stream.*",
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

    # 3. Try Cloud LLM Generation if Key is Provided
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
        items = bot_turn.get("items", [])
        has_benchmark = bot_turn.get("has_benchmark", False)

    # 4. Check if User Requested to Log / Save to Profile
    rec = None
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

    if sec_res.pii_redacted:
        reply_content += "\n\n*(🛡️ Notice: Sensitive personal data like email/phone was redacted for privacy)*"

    return JSONResponse(content={
        "success": True,
        "reply": reply_content,
        "items": items,
        "co2e_kg": total_co2,
        "saved_co2e_kg": total_saved,
        "category": primary_category,
        "is_chat_only": is_chat_only,
        "has_benchmark": has_benchmark,
        "logged_record": rec if rec else None,
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
    <title>EcoTracker — Enterprise Sustainability Intelligence</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
    <style>
        :root {
            --primary: #10b981;
            --primary-glow: rgba(16, 185, 129, 0.4);
            --primary-light: #34d399;
            --primary-dark: #059669;
            --bg-body: #080d19;
            --sidebar-bg: #0b1120;
            --card-bg: rgba(15, 23, 42, 0.85);
            --card-border: rgba(255, 255, 255, 0.08);
            --card-hover: rgba(255, 255, 255, 0.16);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-cyan: #06b6d4;
            --accent-purple: #a855f7;
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.35);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
            background: var(--bg-body);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
        }

        /* App Shell Layout */
        .app-shell {
            display: flex;
            width: 100vw;
            height: 100vh;
        }

        /* Sidebar Rail */
        aside.sidebar {
            width: 270px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--card-border);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 22px 18px;
            flex-shrink: 0;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding-left: 6px;
        }
        .brand-icon {
            width: 38px; height: 38px;
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(16,185,129,0.3), rgba(6,182,212,0.3));
            border: 1px solid rgba(16,185,129,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 0 16px var(--primary-glow);
        }
        .brand-text h1 {
            font-size: 19px;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 40%, #a7f3d0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-badge {
            font-size: 9.5px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            margin-left: 6px;
        }

        /* Nav List */
        .nav-menu {
            display: flex;
            flex-direction: column;
            gap: 6px;
            list-style: none;
        }
        .nav-item button {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 11px 14px;
            border-radius: 10px;
            border: 1px solid transparent;
            background: transparent;
            color: var(--text-muted);
            font-size: 13.5px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .nav-item button:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.04);
        }
        .nav-item button.active {
            background: rgba(16, 185, 129, 0.14);
            border-color: rgba(16, 185, 129, 0.35);
            color: #34d399;
        }
        .nav-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Sidebar Footer */
        .sidebar-footer {
            border-top: 1px solid var(--card-border);
            padding-top: 16px;
        }
        .user-switch-box {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .user-switch-box input {
            background: transparent;
            border: none;
            color: #fff;
            font-size: 12.5px;
            font-weight: 600;
            outline: none;
            width: 100%;
        }

        /* Main Workspace */
        main.main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow-y: auto;
            background: radial-gradient(circle at 15% 15%, rgba(16, 185, 129, 0.07) 0%, transparent 45%),
                        radial-gradient(circle at 85% 85%, rgba(6, 182, 212, 0.06) 0%, transparent 45%),
                        var(--bg-body);
        }

        /* Top Action Bar */
        .top-action-bar {
            padding: 16px 32px;
            border-bottom: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(11, 17, 32, 0.6);
            backdrop-filter: blur(16px);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .view-title-group h2 {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.01em;
            color: #fff;
        }
        .view-title-group p {
            font-size: 12px;
            color: var(--text-muted);
        }
        .top-buttons {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .btn-action {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 12.5px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            border: 1px solid var(--card-border);
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-main);
            transition: all 0.2s;
        }
        .btn-action:hover {
            background: rgba(255, 255, 255, 0.09);
            border-color: rgba(255, 255, 255, 0.2);
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

        /* View Containers */
        .content-body {
            padding: 28px 32px 60px;
            flex: 1;
        }
        .tab-view { display: none; }
        .tab-view.active { display: block; animation: fadeIn 0.2s ease; }

        /* Glassmorphism Cards */
        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            box-shadow: 0 12px 36px -10px rgba(0, 0, 0, 0.5);
        }

        /* View 1: Chatbot Interface */
        .chat-full-view {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 160px);
        }
        .chat-stream {
            flex: 1;
            overflow-y: auto;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .chat-msg-row {
            display: flex;
            gap: 12px;
            align-items: flex-start;
            animation: fadeIn 0.2s ease;
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
            padding: 14px 18px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.6;
        }
        .msg-user {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #fff;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
        }
        .msg-agent {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            word-break: break-word;
        }
        .msg-agent p { margin: 0 0 10px 0; line-height: 1.6; }
        .msg-agent p:last-child { margin-bottom: 0; }
        .msg-agent ul, .msg-agent ol { margin: 8px 0 12px 20px; padding: 0; }
        .msg-agent li { margin-bottom: 6px; line-height: 1.55; color: #cbd5e1; }
        .msg-agent strong { color: #fff; font-weight: 700; }
        .msg-agent em { color: #94a3b8; }
        .msg-agent hr { border: none; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 14px 0; }
        .msg-agent h3, .msg-agent h4 { color: #fff; font-weight: 700; margin: 12px 0 6px; }
        .msg-agent code {
            background: rgba(16, 185, 129, 0.12);
            color: #6ee7b7;
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 12px;
            font-family: ui-monospace, monospace;
        }
        .msg-time {
            font-size: 10.5px;
            color: var(--text-muted);
            margin-top: 4px;
            padding: 0 4px;
        }

        /* Modern Structured Carbon Result Card */
        .carbon-calc-card {
            background: rgba(11, 18, 33, 0.95);
            border: 1px solid rgba(16, 185, 129, 0.28);
            border-radius: 12px;
            padding: 16px 18px;
            margin: 10px 0 6px;
            box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .calc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .calc-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            font-size: 14.5px;
            color: #fff;
        }
        .emissions-pill {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #fca5a5;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12.5px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 5px;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.15);
        }
        .formula-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 14px;
            flex-wrap: wrap;
        }
        .formula-tag {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 11.5px;
            color: #94a3b8;
            font-family: ui-monospace, monospace;
        }
        .baseline-badge {
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.28);
            border-radius: 6px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 600;
        }
        .eco-swap-card {
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-left: 3px solid #10b981;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 12px;
        }
        .eco-swap-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .eco-swap-label {
            font-size: 11px;
            font-weight: 800;
            color: #34d399;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .eco-saved-pill {
            background: rgba(16, 185, 129, 0.22);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #6ee7b7;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
        }
        .eco-swap-desc {
            font-size: 12.5px;
            color: #cbd5e1;
            line-height: 1.5;
        }
        .benchmark-info-box {
            background: rgba(56, 189, 248, 0.05);
            border: 1px dashed rgba(56, 189, 248, 0.3);
            border-radius: 8px;
            padding: 9px 12px;
            font-size: 12px;
            color: #94a3b8;
            margin-bottom: 12px;
            line-height: 1.45;
        }
        .logged-success-card {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 10px;
            padding: 12px 16px;
            color: #6ee7b7;
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 10px 0;
            font-size: 13px;
        }
        
        /* Security Alert Box */
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
        }
        .security-alert-body { font-size: 13px; line-height: 1.5; color: #f87171; }
        .security-alert-meta {
            font-size: 11px;
            color: #94a3b8;
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px solid rgba(239, 68, 68, 0.2);
        }

        .chat-action-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }
        .chat-action-btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #cbd5e1;
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .chat-action-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.25);
            color: #fff;
            transform: translateY(-1px);
        }
        .chat-action-btn.primary {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(5, 150, 105, 0.35));
            border-color: rgba(16, 185, 129, 0.5);
            color: #6ee7b7;
            box-shadow: 0 2px 10px rgba(16, 185, 129, 0.2);
        }
        .chat-action-btn.primary:hover {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.4), rgba(5, 150, 105, 0.5));
            color: #fff;
            border-color: #34d399;
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
            margin: 10px 0;
        }
        .prompt-pill {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 12px;
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
            padding: 14px 18px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .chat-input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-glow); }

        /* View 2: Analytics & Budget Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }
        .metric-card {
            padding: 22px 24px;
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
            letter-spacing: 0.05em;
        }
        .metric-value {
            font-size: 30px;
            font-weight: 800;
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
        .chart-card-full {
            padding: 24px 28px;
            margin-bottom: 24px;
        }
        .chart-box {
            height: 280px;
            position: relative;
        }

        /* View 3: Eco Habits Studio */
        .habits-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }
        .habit-btn {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .habit-btn:hover {
            background: rgba(16, 185, 129, 0.12);
            border-color: rgba(16, 185, 129, 0.45);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15);
        }
        .habit-icon { font-size: 32px; }
        .habit-title { font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .habit-impact { font-size: 12px; color: var(--primary-light); font-weight: 600; }

        /* Calculator Form */
        .calc-form-card { padding: 26px 28px; }
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
        .calc-tab:hover { color: #fff; }
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
        }
        .form-select:focus, .form-input:focus { border-color: var(--primary); }
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

        /* View 4: Activity History Table */
        .history-card { padding: 24px 28px; }
        .table-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .search-box { position: relative; min-width: 260px; }
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
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
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

        /* View 5: Carbon Offsets */
        .offset-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 18px;
            margin-top: 18px;
        }
        .project-card {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s;
        }
        .project-card:hover { border-color: rgba(56, 189, 248, 0.4); transform: translateY(-2px); }

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
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
    </style>
</head>
<body>
    <div class="app-shell">
        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <div>
                <div class="brand">
                    <div class="brand-icon">🌱</div>
                    <div class="brand-text">
                        <h1>EcoTracker<span class="brand-badge">SaaS</span></h1>
                    </div>
                </div>

                <ul class="nav-menu">
                    <li class="nav-item">
                        <button class="active" id="nav-chat" onclick="switchNav('chat')">
                            <span class="nav-left">💬 AI Carbon Chat</span>
                            <span style="font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(16,185,129,0.2); color: #34d399;">Bot</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button id="nav-analytics" onclick="switchNav('analytics')">
                            <span class="nav-left">📊 Analytics & Goals</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button id="nav-habits" onclick="switchNav('habits')">
                            <span class="nav-left">⚡ Habits & Calculator</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button id="nav-history" onclick="switchNav('history')">
                            <span class="nav-left">📋 Activity History</span>
                            <span id="nav-history-count" style="font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.06); color: #94a3b8;">0</span>
                        </button>
                    </li>
                    <li class="nav-item">
                        <button id="nav-offsets" onclick="switchNav('offsets')">
                            <span class="nav-left">🌍 Carbon Offsets</span>
                        </button>
                    </li>
                </ul>
            </div>

            <div class="sidebar-footer">
                <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; font-weight: 700;">Customer Session</div>
                <div class="user-switch-box">
                    <span>👤</span>
                    <input type="text" id="user-id-input" value="default_customer" placeholder="Customer ID" title="Switch customer account">
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn-action" style="flex: 1; justify-content: center; font-size: 11.5px;" onclick="openKeyModal()">⚙️ Cloud API Key</button>
                </div>
            </div>
        </aside>

        <!-- Main Content Canvas -->
        <main class="main-content">
            <!-- Top Action Header -->
            <div class="top-action-bar">
                <div class="view-title-group">
                    <h2 id="current-view-title">AI Carbon Chatbot</h2>
                    <p id="current-view-subtitle">Interactive conversational advisor with real-time carbon intelligence</p>
                </div>
                <div class="top-buttons">
                    <span style="font-size: 11.5px; padding: 4px 10px; border-radius: 6px; background: rgba(16, 185, 129, 0.15); color: #34d399; font-weight: 600;" id="llm-status-pill">
                        ⚡ Dynamic Chatbot
                    </span>
                    <button class="btn-action" onclick="exportDataCSV()">📥 Export CSV</button>
                    <button class="btn-action btn-danger-outline" onclick="openResetModal()">🗑️ Reset</button>
                </div>
            </div>

            <div class="content-body">
                <!-- VIEW 1: AI Carbon Chatbot (Dedicated & Clean) -->
                <div class="tab-view active" id="view-chat">
                    <div class="chat-full-view">
                        <div class="glass-card chat-stream" id="chat-stream">
                            <div class="chat-msg-row">
                                <div class="chat-avatar avatar-bot">🌱</div>
                                <div class="msg-wrapper">
                                    <div class="msg-bubble msg-agent">
                                        👋 <strong>Hello! I'm EcoTracker AI, your conversational sustainability chatbot.</strong><br><br>
                                        Tell me about any activity—like driving to work, a flight, what you had for lunch, or home appliances you ran. I'll calculate your exact carbon footprint and suggest realistic, high-impact eco-swaps!<br><br>
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
                            <input type="text" class="chat-input" id="chat-input" placeholder="Message EcoTracker AI (e.g. 'I drove 40 km' or 'Hi')..." onkeydown="if(event.key==='Enter') submitChat()">
                            <button class="btn-action" style="background: var(--primary); color: #042f2e; font-weight: 700; padding: 0 24px;" onclick="submitChat()">Send ↵</button>
                        </div>
                    </div>
                </div>

                <!-- VIEW 2: Analytics & Budget Overview -->
                <div class="tab-view" id="view-analytics">
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

                    <div class="glass-card chart-card-full">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <h3 style="font-size: 16px; font-weight: 700;">Emissions Breakdown by Category</h3>
                            <span style="font-size: 12px; color: var(--text-muted);">Real-Time Distribution</span>
                        </div>
                        <div class="chart-box">
                            <canvas id="categoryChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- VIEW 3: 1-Click Habits & FastMCP Calculator -->
                <div class="tab-view" id="view-habits">
                    <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">Eco Habits Studio</h3>
                    <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">Tap any daily habit to instantly log verified emissions with 1 click.</p>
                    
                    <div class="habits-grid">
                        <div class="habit-btn" onclick="quickLogHabit('Morning Coffee', 'diet', 0.28, 0.0)">
                            <span class="habit-icon">☕</span>
                            <div>
                                <div class="habit-title">Morning Coffee</div>
                                <div class="habit-impact">+0.28 kg CO2e</div>
                            </div>
                        </div>
                        <div class="habit-btn" onclick="quickLogHabit('Electric Train (25 km)', 'transportation', 0.88, 3.92)">
                            <span class="habit-icon">🚆</span>
                            <div>
                                <div class="habit-title">Train Commute (25 km)</div>
                                <div class="habit-impact">-3.92 kg CO2e avoided</div>
                            </div>
                        </div>
                        <div class="habit-btn" onclick="quickLogHabit('Plant-Based Lunch Bowl', 'diet', 0.40, 4.50)">
                            <span class="habit-icon">🥗</span>
                            <div>
                                <div class="habit-title">Plant-Based Lunch</div>
                                <div class="habit-impact">-4.50 kg CO2e avoided</div>
                            </div>
                        </div>
                        <div class="habit-btn" onclick="quickLogHabit('Bicycle Commute (10 km)', 'transportation', 0.0, 1.92)">
                            <span class="habit-icon">🚲</span>
                            <div>
                                <div class="habit-title">Bicycle Ride (10 km)</div>
                                <div class="habit-impact">-1.92 kg CO2e avoided</div>
                            </div>
                        </div>
                        <div class="habit-btn" onclick="quickLogHabit('AC Eco-Scheduling (2 hrs)', 'energy', 0.60, 0.70)">
                            <span class="habit-icon">❄️</span>
                            <div>
                                <div class="habit-title">AC Eco-Scheduling</div>
                                <div class="habit-impact">-0.70 kg CO2e avoided</div>
                            </div>
                        </div>
                        <div class="habit-btn" onclick="quickLogHabit('Composted Food Scraps (3 kg)', 'waste', 0.0, 2.40)">
                            <span class="habit-icon">♻️</span>
                            <div>
                                <div class="habit-title">Composted Food Scraps</div>
                                <div class="habit-impact">-2.40 kg CO2e avoided</div>
                            </div>
                        </div>
                    </div>

                    <!-- FastMCP Domain Calculator -->
                    <div class="glass-card calc-form-card" style="max-width: 680px;">
                        <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 14px;">FastMCP Scientific Calculator</h3>
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
                </div>

                <!-- VIEW 4: Activity History Table -->
                <div class="tab-view" id="view-history">
                    <div class="glass-card history-card">
                        <div class="table-controls">
                            <div>
                                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 4px;">Verified Activity History</h3>
                                <p style="font-size: 12px; color: var(--text-muted);">Inspect, search, and delete individual records in your private session.</p>
                            </div>
                            <div style="display: flex; gap: 12px; align-items: center;">
                                <div class="search-box">
                                    <span class="search-icon">🔍</span>
                                    <input type="text" class="search-input" id="search-input" placeholder="Search activities..." oninput="renderTable()">
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

                <!-- VIEW 5: Carbon Offsets Marketplace -->
                <div class="tab-view" id="view-offsets">
                    <div class="glass-card" style="padding: 24px 28px; margin-bottom: 24px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                            <div>
                                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 4px;">Verified Carbon Offset Directory</h3>
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
                </div>
            </div>
        </main>
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

        // Navigation Switcher
        const NAV_METADATA = {
            chat: { title: 'AI Carbon Chatbot', subtitle: 'Interactive conversational advisor with real-time carbon intelligence' },
            analytics: { title: 'Carbon Analytics & Goals', subtitle: 'Executive emission breakdowns, category distribution, and daily targets' },
            habits: { title: 'Eco Habits Studio & Calculator', subtitle: '1-click daily habit logging and FastMCP verified estimation tools' },
            history: { title: 'Verified Activity History', subtitle: 'Granular audit log, record deletion, and compliance reporting' },
            offsets: { title: 'Verified Carbon Offsets', subtitle: 'Certified Gold Standard and Verra VCS offset project directory' }
        };

        function switchNav(viewId) {
            document.querySelectorAll('.tab-view').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.nav-menu button').forEach(b => b.classList.remove('active'));

            const targetView = document.getElementById(`view-${viewId}`);
            const targetBtn = document.getElementById(`nav-${viewId}`);
            if (targetView) targetView.classList.add('active');
            if (targetBtn) targetBtn.classList.add('active');

            const meta = NAV_METADATA[viewId];
            if (meta) {
                document.getElementById('current-view-title').innerText = meta.title;
                document.getElementById('current-view-subtitle').innerText = meta.subtitle;
            }

            if (viewId === 'analytics' && lastSummaryData) {
                setTimeout(() => renderChart(lastSummaryData.by_category || []), 50);
            }
        }

        // Calculator Tab Configuration
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
                showToast(`⚡ Habit logged: ${name}`);
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
                document.getElementById('nav-history-count').innerText = data.total_entries;
                
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
            const chartCanvas = document.getElementById('categoryChart');
            if (!chartCanvas) return;
            const ctx = chartCanvas.getContext('2d');
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
                                font: { size: 12, family: 'Inter' },
                                boxWidth: 14
                            }
                        }
                    },
                    cutout: '70%'
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
                                    <span>🚨 Security Guardrail Triggered</span>
                                </div>
                                <div class="security-alert-body">
                                    <strong>Blocked:</strong> ${data.rejection_reason || 'Potential prompt injection, unauthorized override, or sensitive data leak detected.'}
                                </div>
                                <div class="security-alert-meta">
                                    Audit Action: Blocked & Logged • Enterprise Zero-Trust Sandbox
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

                // Helper to render markdown cleanly
                function renderMarkdown(text) {
                    if (!text) return '';
                    if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
                        return marked.parse(text);
                    }
                    let html = text
                        .replace(/### (.*?)\n/g, '<h4 style="margin: 8px 0 4px; color: #fff;">$1</h4>')
                        .replace(/#### (.*?)\n/g, '<h5 style="margin: 6px 0 2px; color: #38bdf8;">$1</h5>')
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>')
                        .replace(/^---$/gm, '<hr>')
                        .replace(/^- (.*)$/gm, '<li>$1</li>');
                    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
                    return html.split('\n\n').map(p => p.trim() ? `<p>${p.replace(/\n/g, '<br>')}</p>` : '').join('');
                }

                let bubbleHtml = '';
                if (data.items && data.items.length > 0) {
                    let cardsHtml = '';
                    for (const it of data.items) {
                        const isBenchmarked = !it.has_number;
                        const formulaClean = (it.formula || '').replace(/\(using standard.*?\)/i, '').replace(/\(default.*?\)/i, '').trim();
                        cardsHtml += `
                            <div class="carbon-calc-card">
                                <div class="calc-header">
                                    <div class="calc-title">
                                        <span>${it.title}</span>
                                    </div>
                                    <div class="emissions-pill">
                                        <span>💨</span>
                                        <span>${Number(it.emissions).toFixed(2)} kg CO2e</span>
                                    </div>
                                </div>
                                <div class="formula-meta">
                                    <span class="formula-tag">📐 ${formulaClean}</span>
                                    ${isBenchmarked ? '<span class="baseline-badge">📌 Standard Baseline Average</span>' : ''}
                                </div>
                                ${it.swap ? `
                                    <div class="eco-swap-card">
                                        <div class="eco-swap-top">
                                            <span class="eco-swap-label">💡 Recommended Eco-Swap</span>
                                            ${it.savings > 0 ? `<span class="eco-saved-pill">🌱 Avoids ~${Number(it.savings).toFixed(2)} kg CO2e</span>` : ''}
                                        </div>
                                        <div class="eco-swap-desc">${it.swap}</div>
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    }

                    let benchmarkNotice = '';
                    if (data.has_benchmark) {
                        benchmarkNotice = `
                            <div class="benchmark-info-box">
                                💡 <strong>Benchmark Note:</strong> Since no specific numbers (distance, weight, or hours) were provided, this was estimated using standard daily averages. Reply with your exact numbers (e.g. <em>"it was 14 km"</em>) to recalculate!
                            </div>
                        `;
                    }

                    let loggedNotice = '';
                    if (data.logged_record) {
                        const rec = data.logged_record;
                        loggedNotice = `
                            <div class="logged-success-card">
                                <span>✅</span>
                                <div><strong>Confirmed & Recorded!</strong> Saved to your private activity history (Log #${rec.id}).</div>
                            </div>
                        `;
                    }

                    let actionHtml = '';
                    if (!data.is_chat_only && !data.logged_record && data.co2e_kg > 0 && !promptText.toLowerCase().includes('log') && !promptText.toLowerCase().includes('save')) {
                        actionHtml = `
                            <div class="chat-action-pills">
                                <button class="chat-action-btn primary" onclick="saveDirectFromChat('${data.category}', '${promptText.replace(/'/g, "\\'")}', ${data.co2e_kg}, ${data.saved_co2e_kg || 0})">
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

                    bubbleHtml = `
                        <div style="font-size: 13.5px; color: #cbd5e1; margin-bottom: 8px;">
                            🌿 <strong>Carbon Impact Breakdown:</strong>
                        </div>
                        ${cardsHtml}
                        ${benchmarkNotice}
                        ${loggedNotice}
                        ${actionHtml}
                    `;
                } else {
                    bubbleHtml = renderMarkdown(data.reply);
                }

                botRow.innerHTML = `
                    <div class="chat-avatar avatar-bot">🌱</div>
                    <div class="msg-wrapper">
                        <div class="msg-bubble msg-agent">
                            ${bubbleHtml}
                        </div>
                        <span class="msg-time">${formatTimeNow()}</span>
                    </div>
                `;
                stream.appendChild(botRow);
                stream.scrollTop = stream.scrollHeight;

                chatHistory.push({ role: 'assistant', content: data.reply });

                if (promptText.toLowerCase().includes('log') || promptText.toLowerCase().includes('save') || data.logged_record) {
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
