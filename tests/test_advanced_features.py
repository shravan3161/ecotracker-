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

"""Automated tests for Senior-Developer Grade Platform Enhancements:
- Multimodal Vision Scanner (Receipt & Utility Bill OCR)
- Real-Time Grid Carbon Intensity
- Airport-to-Airport Aviation & Rail Substitution
- Interactive What-If Climate & ROI Scenario Simulator
- Enterprise ESG & Scope 1, 2, 3 GHG Protocol Disclosures
"""

import json
import pytest
from starlette.testclient import TestClient
from app.dashboard import app
from app import db
from app.services.flight_calculator import calculate_flight_emissions
from app.services.simulator import simulate_scenarios
from app.services.vision_scanner import heuristic_parse_text
from app.mcp_server import get_flight_emissions, get_grid_carbon_intensity

TEST_USER = "test_enterprise_corp"

@pytest.fixture(autouse=True)
def clean_test_env():
    db.init_db("ecotracker.db")
    db.clear_user_data(TEST_USER, db_path="ecotracker.db")
    yield
    db.clear_user_data(TEST_USER, db_path="ecotracker.db")

def test_multimodal_vision_scanner():
    client = TestClient(app)

    # 1. Grocery receipt scan
    res_receipt = client.post("/api/scan-receipt", json={"doc_type": "receipt"})
    assert res_receipt.status_code == 200
    data_receipt = res_receipt.json()
    assert data_receipt["document_type"] == "grocery_receipt"
    assert data_receipt["total_co2e_kg"] > 0
    assert len(data_receipt["items"]) >= 1
    assert "swap_suggestion" in data_receipt["items"][0]

    # 2. Utility bill scan
    res_bill = client.post("/api/scan-bill", json={"doc_type": "utility_bill"})
    assert res_bill.status_code == 200
    data_bill = res_bill.json()
    assert data_bill["document_type"] == "utility_bill"
    assert data_bill["total_co2e_kg"] > 0
    assert "Grid Electricity" in data_bill["items"][0]["name"]

    # 3. Custom text OCR parsing
    custom_ocr = "Grocery Mart\nBeef Steak 500g\nWhole Milk 2L\nBread 1 loaf"
    parsed = heuristic_parse_text(custom_ocr, doc_type="receipt")
    assert parsed["total_co2e_kg"] > 0
    assert any("beef" in item["name"].lower() for item in parsed["items"])

def test_grid_carbon_intensity_service():
    client = TestClient(app)

    res = client.get("/api/grid-intensity?region=us-caiso")
    assert res.status_code == 200
    data = res.json()
    assert data["intensity_g_kwh"] > 0
    assert data["rating"] in ["GREEN", "MODERATE", "CARBON-INTENSIVE"]
    assert "optimal_charging_window" in data
    assert data["shift_savings"]["ev_full_charge_savings_kg"] > 0

def test_flight_emissions_and_rail_benchmark():
    client = TestClient(app)

    # 1. Airport route via API
    flight_payload = {
        "origin": "LHR",
        "destination": "JFK",
        "cabin_class": "economy",
        "round_trip": True
    }
    res = client.post("/api/flight-emissions", json=flight_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["distance_km"] > 10000.0  # round trip transatlantic
    assert data["emissions_kg_co2e"] > 1000.0

    # 2. European corridor with high-speed train viability (Paris to Amsterdam)
    train_route = calculate_flight_emissions("CDG", "AMS", cabin_class="economy")
    assert train_route["train_alternative"]["viable_land_corridor"] is True
    assert train_route["train_alternative"]["potential_savings_kg"] > 0

def test_what_if_scenario_simulator():
    client = TestClient(app)

    sim_payload = {
        "weekly_commute_km": 200.0,
        "transit_mode": "train",
        "meatless_days_per_week": 4,
        "has_rooftop_solar": True,
        "has_heat_pump": True,
        "annual_flights_avoided": 3
    }
    res = client.post("/api/simulate", json=sim_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["co2e_saved_annual_tons"] > 5.0
    assert data["financial_savings_annual_usd"] > 1000.0
    assert data["projections"]["year_5"]["co2e_abated_tons"] > data["projections"]["year_1"]["co2e_abated_tons"]

def test_enterprise_esg_disclosure_and_html_generation():
    client = TestClient(app)

    # 1. Log Scope 1 fuel entry
    db.log_calculation(
        category="transportation",
        activity_details="Gasoline company van fleet fuel 50 liters",
        co2e_kg=115.0,
        saved_co2e_kg=25.0,
        user_id=TEST_USER,
        scope="Scope 1 (Direct)"
    )

    # 2. Log Scope 2 electricity entry
    db.log_calculation(
        category="energy",
        activity_details="Headquarters grid electricity 1200 kWh",
        co2e_kg=462.0,
        saved_co2e_kg=120.0,
        user_id=TEST_USER,
        scope="Scope 2 (Market Electricity)"
    )

    # 3. Log Scope 3 employee travel entry
    db.log_calculation(
        category="transit",
        activity_details="Executive flight SFO to JFK",
        co2e_kg=680.0,
        saved_co2e_kg=0.0,
        user_id=TEST_USER,
        scope="Scope 3 (Value Chain & Commute)"
    )

    # 4. Fetch JSON ESG report
    res_json = client.get(f"/api/esg-report?format=json&user_id={TEST_USER}")
    assert res_json.status_code == 200
    esg_data = res_json.json()
    assert esg_data["verification_hash"].startswith("ESG-VERIFIED-")
    assert esg_data["metrics"]["scope_breakdown_mt"]["scope_1_direct"] > 0
    assert esg_data["metrics"]["scope_breakdown_mt"]["scope_2_electricity"] > 0
    assert esg_data["metrics"]["scope_breakdown_mt"]["scope_3_value_chain"] > 0

    # 5. Fetch Printable HTML ESG disclosure
    res_html = client.get(f"/api/esg-report?format=html&user_id={TEST_USER}")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers.get("content-type", "")
    assert "EcoTracker — Corporate GHG Disclosure" in res_html.text
    assert "Scope 1 (Direct)" in res_html.text
    assert "Print / Save as PDF" in res_html.text

def test_mcp_advanced_tools():
    # 1. Flight emissions tool
    raw_flight = get_flight_emissions("SFO", "HND", cabin_class="business")
    flight_data = json.loads(raw_flight)
    assert flight_data["emissions_kg_co2e"] > 0
    assert "Tokyo Haneda" in flight_data["destination"]

    # 2. Live Grid Intensity tool
    raw_grid = get_grid_carbon_intensity("uk")
    grid_data = json.loads(raw_grid)
    assert grid_data["intensity_g_kwh"] > 0
    assert "United Kingdom" in grid_data["region"]

def test_leaderboard_and_daily_trends():
    client = TestClient(app)

    # 1. Fetch leaderboard
    res_lead = client.get("/api/leaderboard")
    assert res_lead.status_code == 200
    lead_data = res_lead.json()
    assert "leaderboard" in lead_data
    assert len(lead_data["leaderboard"]) >= 1

    # 2. Fetch daily trends
    res_trends = client.get(f"/api/daily-trends?user_id={TEST_USER}")
    assert res_trends.status_code == 200
    trends_data = res_trends.json()
    assert "trends" in trends_data

def test_pwa_manifest_and_sw():
    client = TestClient(app)

    # 1. Manifest
    res_man = client.get("/manifest.json")
    assert res_man.status_code == 200
    man_data = res_man.json()
    assert man_data["short_name"] == "EcoTracker"
    assert man_data["display"] == "standalone"

    # 2. Service worker
    res_sw = client.get("/sw.js")
    assert res_sw.status_code == 200
    assert "application/javascript" in res_sw.headers.get("content-type", "")
    assert "CACHE_NAME" in res_sw.text

