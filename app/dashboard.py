from app.frontend import get_dashboard_html
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
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
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
    scope: Optional[str] = None
    org_id: str = "default_org"

class ScanDocumentRequest(BaseModel):
    image_base64: str = ""
    text_content: str = ""
    doc_type: str = "receipt"
    api_key: Optional[str] = ""

class FlightRequest(BaseModel):
    origin: str
    destination: str
    cabin_class: str = "economy"
    round_trip: bool = False

class SimulateRequest(BaseModel):
    weekly_commute_km: float = 150.0
    transit_mode: str = "train"
    meatless_days_per_week: int = 3
    has_rooftop_solar: bool = True
    has_heat_pump: bool = True
    annual_flights_avoided: int = 2

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
        user_id=req.user_id,
        scope=req.scope,
        org_id=req.org_id
    )
    return JSONResponse(content={"status": "success", "log": entry})

@dashboard_app.post("/api/scan-receipt")
async def scan_receipt(req: ScanDocumentRequest):
    """Multimodal Vision Scanner for grocery receipts."""
    from app.services.vision_scanner import analyze_document_image, heuristic_parse_text
    if req.text_content:
        res = heuristic_parse_text(req.text_content, doc_type="receipt")
    elif req.image_base64:
        res = await analyze_document_image(req.image_base64, doc_type_hint="grocery_receipt", api_key=req.api_key)
    else:
        res = heuristic_parse_text("Sample Grocery Receipt", doc_type="receipt")
    return JSONResponse(content=res)

@dashboard_app.post("/api/scan-bill")
async def scan_bill(req: ScanDocumentRequest):
    """Multimodal Vision Scanner for electricity & gas utility bills."""
    from app.services.vision_scanner import analyze_document_image, heuristic_parse_text
    if req.text_content:
        res = heuristic_parse_text(req.text_content, doc_type="utility_bill")
    elif req.image_base64:
        res = await analyze_document_image(req.image_base64, doc_type_hint="utility_bill", api_key=req.api_key)
    else:
        res = heuristic_parse_text("Sample Utility Bill 480 kWh", doc_type="utility_bill")
    return JSONResponse(content=res)

@dashboard_app.get("/api/grid-intensity")
async def grid_intensity(region: str = Query("auto")):
    """Live and regional grid carbon intensity tracking (g CO2e / kWh)."""
    from app.services.grid_intensity import get_grid_carbon_intensity
    data = await get_grid_carbon_intensity(region)
    return JSONResponse(content=data)

@dashboard_app.post("/api/flight-emissions")
def flight_emissions(req: FlightRequest):
    """Airport-to-airport flight emission calculator using DEFRA and Haversine distance."""
    from app.services.flight_calculator import calculate_flight_emissions
    data = calculate_flight_emissions(req.origin, req.destination, req.cabin_class, req.round_trip)
    return JSONResponse(content=data)

@dashboard_app.post("/api/simulate")
def run_simulation(req: SimulateRequest):
    """Interactive What-If Sustainability and ROI Scenario Simulator."""
    from app.services.simulator import simulate_scenarios
    res = simulate_scenarios(
        weekly_commute_km=req.weekly_commute_km,
        transit_mode=req.transit_mode,
        meatless_days_per_week=req.meatless_days_per_week,
        has_rooftop_solar=req.has_rooftop_solar,
        has_heat_pump=req.has_heat_pump,
        annual_flights_avoided=req.annual_flights_avoided
    )
    return JSONResponse(content=res)

@dashboard_app.get("/api/esg-report")
def export_esg_report(
    user_id: str = Query("default_customer"),
    org_id: str = Query("default_org"),
    company_name: str = Query("Enterprise Sustainability Team"),
    reporting_period: str = Query("FY2026"),
    format: str = Query("html")
):
    """Generates an audit-ready GHG Protocol Scope 1-2-3 ESG carbon balance sheet."""
    from app.services.esg_report import generate_esg_disclosure, render_printable_esg_html
    logs = db.get_all_user_logs(user_id=user_id, org_id=org_id)
    disclosure = generate_esg_disclosure(
        company_name=company_name,
        reporting_period=reporting_period,
        user_id=user_id,
        logs=logs
    )
    if format.lower() == "html":
        html = render_printable_esg_html(disclosure)
        return HTMLResponse(content=html)
    return JSONResponse(content=disclosure)

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

@dashboard_app.get("/api/leaderboard")
def get_leaderboard_endpoint():
    """Returns community and team sustainability rankings."""
    return JSONResponse(content={"status": "success", "leaderboard": db.get_leaderboard()})

@dashboard_app.get("/api/daily-trends")
def get_daily_trends_endpoint(user_id: str = Query("default_customer")):
    """Returns daily emissions and savings timeline for historical trend charts."""
    return JSONResponse(content={"status": "success", "trends": db.get_daily_trends(user_id=user_id)})

@dashboard_app.get("/manifest.json")
def get_manifest():
    """Returns PWA Web App Manifest for mobile installation."""
    manifest = {
        "name": "EcoTracker AI Sustainability",
        "short_name": "EcoTracker",
        "description": "Enterprise AI Carbon Intelligence Platform",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#080d1a",
        "theme_color": "#10b981",
        "icons": [
            {
                "src": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f331.png",
                "sizes": "72x72",
                "type": "image/png"
            },
            {
                "src": "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/1f331.png",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    }
    return JSONResponse(content=manifest, headers={"Content-Type": "application/manifest+json"})

@dashboard_app.get("/sw.js")
def get_service_worker():
    """Returns basic service worker script for offline shell caching."""
    sw_script = """
    const CACHE_NAME = 'ecotracker-v1';
    self.addEventListener('install', e => { self.skipWaiting(); });
    self.addEventListener('activate', e => { e.waitUntil(clients.claim()); });
    self.addEventListener('fetch', e => {
        if (e.request.mode === 'navigate') {
            e.respondWith(fetch(e.request).catch(() => caches.match('/')));
        }
    });
    """
    return Response(content=sw_script, media_type="application/javascript")

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

STATIC_DIST_DIR = Path(__file__).resolve().parent.parent / "static_dist"
if (STATIC_DIST_DIR / "assets").exists():
    dashboard_app.mount("/assets", StaticFiles(directory=str(STATIC_DIST_DIR / "assets")), name="static-assets")

@dashboard_app.get("/", response_class=HTMLResponse)
def index():
    dist_index = STATIC_DIST_DIR / "index.html"
    if dist_index.exists():
        return HTMLResponse(content=dist_index.read_text(encoding="utf-8"))
    return HTMLResponse(content=get_dashboard_html())

@dashboard_app.get("/classic", response_class=HTMLResponse)
def classic_index():
    return HTMLResponse(content=get_dashboard_html())

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
