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

"""Dynamic Grid Carbon Intensity Service.

Provides real-time and regional grid carbon intensity tracking (g CO2e / kWh)
with optimal EV / heavy appliance scheduling recommendations.
Integrates live UK National Grid ESO Carbon Intensity API with regional
scientific fallbacks (US eGRID, EU Entso-E, global averages).
"""

import datetime
from typing import Dict, Any, Optional
import httpx

# Regional baseline carbon intensity factors (g CO2e / kWh)
REGIONAL_FACTORS: Dict[str, Dict[str, Any]] = {
    "uk": {"name": "United Kingdom", "intensity_g_kwh": 145.0, "clean_pct": 58, "source": "National Grid ESO"},
    "us-caiso": {"name": "US California (CAISO)", "intensity_g_kwh": 185.0, "clean_pct": 54, "source": "CAISO / eGRID"},
    "us-ercot": {"name": "US Texas (ERCOT)", "intensity_g_kwh": 375.0, "clean_pct": 36, "source": "ERCOT / eGRID"},
    "us-pjm": {"name": "US Mid-Atlantic (PJM)", "intensity_g_kwh": 385.0, "clean_pct": 32, "source": "PJM / eGRID"},
    "us-nyiso": {"name": "US New York (NYISO)", "intensity_g_kwh": 210.0, "clean_pct": 51, "source": "NYISO / eGRID"},
    "us-average": {"name": "US National Average", "intensity_g_kwh": 370.0, "clean_pct": 40, "source": "EPA eGRID"},
    "eu-france": {"name": "France (Nuclear/Renewable)", "intensity_g_kwh": 55.0, "clean_pct": 91, "source": "RTE / ENTSO-E"},
    "eu-germany": {"name": "Germany", "intensity_g_kwh": 340.0, "clean_pct": 52, "source": "Agora Energiewende"},
    "eu-nordic": {"name": "Nordic (Hydro/Wind)", "intensity_g_kwh": 45.0, "clean_pct": 93, "source": "Statnett / Svenska Kraftnät"},
    "australia": {"name": "Australia (NEM)", "intensity_g_kwh": 510.0, "clean_pct": 34, "source": "AEMO"},
    "india": {"name": "India (National Grid)", "intensity_g_kwh": 690.0, "clean_pct": 23, "source": "CEA India"},
    "global-average": {"name": "Global Average", "intensity_g_kwh": 435.0, "clean_pct": 38, "source": "IEA World Energy Outlook"},
}

_CACHE: Dict[str, Any] = {
    "uk_data": None,
    "last_fetched": None
}

async def fetch_live_uk_intensity() -> Optional[Dict[str, Any]]:
    """Attempts to fetch real-time grid carbon intensity from UK National Grid ESO public API."""
    now = datetime.datetime.now(datetime.timezone.utc)
    if _CACHE["last_fetched"] and (now - _CACHE["last_fetched"]).total_seconds() < 900:
        return _CACHE["uk_data"]

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get("https://api.carbonintensity.org.uk/intensity")
            if resp.status_code == 200:
                data = resp.json()["data"][0]
                actual = data["intensity"]["actual"] or data["intensity"]["forecast"]
                index_rating = data["intensity"]["index"]
                result = {
                    "intensity_g_kwh": float(actual),
                    "index": index_rating,
                    "from_time": data["from"],
                    "to_time": data["to"],
                    "source": "UK National Grid Live API"
                }
                _CACHE["uk_data"] = result
                _CACHE["last_fetched"] = now
                return result
    except Exception:
        pass
    return None

async def get_grid_carbon_intensity(region: str = "auto") -> Dict[str, Any]:
    """Computes grid carbon intensity and recommends optimal charging/usage windows."""
    norm_region = region.lower().strip()
    
    # Try UK Live API first if region is UK or auto
    live_uk = None
    if norm_region in ["uk", "united kingdom", "gb", "auto", "london"]:
        live_uk = await fetch_live_uk_intensity()
    
    if live_uk and norm_region in ["uk", "united kingdom", "gb", "london"]:
        g_kwh = live_uk["intensity_g_kwh"]
        source = live_uk["source"]
        region_name = "United Kingdom (Live)"
    else:
        # Match regional fallback
        matched_key = "global-average"
        for key in REGIONAL_FACTORS:
            if key in norm_region or norm_region in key:
                matched_key = key
                break
        
        info = REGIONAL_FACTORS[matched_key]
        g_kwh = info["intensity_g_kwh"]
        source = info["source"]
        region_name = info["name"]

    # Classify rating
    if g_kwh < 150:
        rating = "GREEN"
        status_msg = "Grid power is exceptionally clean right now. Excellent window for EV charging and running dishwashers/laundry."
        badge_color = "#10B981"
        action = "Run high-power appliances now"
    elif g_kwh < 350:
        rating = "MODERATE"
        status_msg = "Grid power is moderately clean. Balanced mix of renewables and transition power."
        badge_color = "#F59E0B"
        action = "Normal usage; delay EV charging if solar/wind peaks later"
    else:
        rating = "CARBON-INTENSIVE"
        status_msg = "Grid is fossil-heavy right now (coal/gas peaker plants active). Postpone discretionary energy use to off-peak hours."
        badge_color = "#EF4444"
        action = "Postpone heavy cycles to off-peak / overnight window"

    # Savings calculation for shifting a 50 kWh EV charge or 5 kWh appliance cycle to a clean window
    appliance_kwh = 4.0
    ev_kwh = 45.0
    dirty_factor = max(g_kwh, 450.0) / 1000.0  # kg CO2e/kWh
    clean_factor = 0.120                       # kg CO2e/kWh (target renewable window)
    appliance_saving_kg = round(appliance_kwh * (dirty_factor - clean_factor), 2)
    ev_saving_kg = round(ev_kwh * (dirty_factor - clean_factor), 2)

    return {
        "region": region_name,
        "intensity_g_kwh": round(g_kwh, 1),
        "kg_co2e_per_kwh": round(g_kwh / 1000.0, 4),
        "rating": rating,
        "badge_color": badge_color,
        "status_message": status_msg,
        "recommended_action": action,
        "optimal_charging_window": "11:00 PM – 05:00 AM (or peak midday solar)",
        "shift_savings": {
            "appliance_cycle_savings_kg": max(appliance_saving_kg, 0.4),
            "ev_full_charge_savings_kg": max(ev_saving_kg, 4.5)
        },
        "source": source
    }
