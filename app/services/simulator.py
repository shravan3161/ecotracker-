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

"""Interactive "What-If" Sustainability & ROI Scenario Simulator.

Models multi-year environmental abatement and cumulative financial savings ($)
across 4 core transition levers:
1. Commute & Transit Mode Shift
2. Clean Home Energy (Solar, Heat Pump, Smart Thermostats)
3. Plant-Forward Dietary Transition
4. Aviation & Business Travel Optimization
"""

from typing import Dict, Any

def simulate_scenarios(
    weekly_commute_km: float = 150.0,
    transit_mode: str = "train",             # train, ev, bike, bus
    meatless_days_per_week: int = 3,         # 0 to 7
    has_rooftop_solar: bool = True,
    has_heat_pump: bool = True,
    annual_flights_avoided: int = 2
) -> Dict[str, Any]:
    """Projects 1-year, 5-year, and 10-year carbon abatement and financial savings."""
    
    # 1. Commute Calculations
    # Baseline: Gas car = 0.192 kg/km, Fuel cost ~$0.15/km
    gas_commute_annual_kg = weekly_commute_km * 50 * 0.192
    gas_commute_annual_cost = weekly_commute_km * 50 * 0.15
    
    transit_factors = {
        "train": (0.035, 0.08),  # (kg/km, cost/km)
        "ev": (0.045, 0.04),
        "bus": (0.089, 0.06),
        "bike": (0.0, 0.01),
    }
    tf, tc = transit_factors.get(transit_mode.lower(), (0.035, 0.08))
    new_commute_annual_kg = weekly_commute_km * 50 * tf
    new_commute_annual_cost = weekly_commute_km * 50 * tc
    
    commute_annual_co2_saved = max(0.0, gas_commute_annual_kg - new_commute_annual_kg)
    commute_annual_money_saved = max(0.0, gas_commute_annual_cost - new_commute_annual_cost)

    # 2. Dietary Transition (3 meals/day, ~250g meat baseline = 15 kg CO2e/day vs plant-based 2.5 kg CO2e/day)
    # Savings per meatless day: ~12.5 kg CO2e + ~$6 in groceries
    diet_annual_co2_saved = meatless_days_per_week * 52 * 12.5
    diet_annual_money_saved = meatless_days_per_week * 52 * 6.0

    # 3. Clean Home Energy
    # Rooftop solar (5kW system): abates ~4,200 kg CO2e/yr + saves ~$850/yr electric bills
    solar_co2_saved = 4200.0 if has_rooftop_solar else 0.0
    solar_money_saved = 850.0 if has_rooftop_solar else 0.0
    
    # Air-source heat pump replacing gas heating: abates ~2,100 kg CO2e/yr + saves ~$420/yr
    heat_pump_co2_saved = 2100.0 if has_heat_pump else 0.0
    heat_pump_money_saved = 420.0 if has_heat_pump else 0.0

    # 4. Aviation Avoidance (Average domestic/regional round-trip flight ~650 kg CO2e + $350 ticket)
    flight_co2_saved = annual_flights_avoided * 650.0
    flight_money_saved = annual_flights_avoided * 350.0

    # Aggregates
    annual_co2_saved_kg = round(
        commute_annual_co2_saved + diet_annual_co2_saved + solar_co2_saved + heat_pump_co2_saved + flight_co2_saved, 1
    )
    annual_money_saved = round(
        commute_annual_money_saved + diet_annual_money_saved + solar_money_saved + heat_pump_money_saved + flight_money_saved, 2
    )

    annual_trees_equivalent = round(annual_co2_saved_kg / 21.77, 0)  # 1 mature tree absorbs ~21.8 kg CO2/year

    return {
        "inputs": {
            "weekly_commute_km": weekly_commute_km,
            "transit_mode": transit_mode.title(),
            "meatless_days_per_week": meatless_days_per_week,
            "has_rooftop_solar": has_rooftop_solar,
            "has_heat_pump": has_heat_pump,
            "annual_flights_avoided": annual_flights_avoided
        },
        "breakdown_annual": {
            "commute_savings_kg": round(commute_annual_co2_saved, 1),
            "diet_savings_kg": round(diet_annual_co2_saved, 1),
            "solar_savings_kg": round(solar_co2_saved, 1),
            "heat_pump_savings_kg": round(heat_pump_co2_saved, 1),
            "aviation_savings_kg": round(flight_co2_saved, 1),
        },
        "financial_savings_annual_usd": annual_money_saved,
        "co2e_saved_annual_kg": annual_co2_saved_kg,
        "co2e_saved_annual_tons": round(annual_co2_saved_kg / 1000.0, 2),
        "trees_equivalent_planted_annual": int(annual_trees_equivalent),
        "projections": {
            "year_1": {
                "co2e_abated_tons": round(annual_co2_saved_kg / 1000.0, 2),
                "financial_savings_usd": round(annual_money_saved, 0),
            },
            "year_5": {
                "co2e_abated_tons": round((annual_co2_saved_kg * 5.0) / 1000.0, 2),
                "financial_savings_usd": round(annual_money_saved * 5.0, 0),
            },
            "year_10": {
                "co2e_abated_tons": round((annual_co2_saved_kg * 10.0) / 1000.0, 2),
                "financial_savings_usd": round(annual_money_saved * 10.0, 0),
            }
        },
        "summary": f"By adopting these green transitions, you will abate {annual_co2_saved_kg / 1000.0:.2f} metric tons of CO2e and save ${annual_money_saved:,.0f} annually ({annual_trees_equivalent:.0f} trees planted equivalent)."
    }
