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

"""EcoTracker High-Precision FastMCP Server.

Exposes domain-specific carbon calculation and efficiency tools over MCP (Model Context Protocol).
Grounds calculations in verified benchmarks (UK DEFRA, US EPA, Poore & Nemecek food lifecycle).
"""

import json
from mcp.server.fastmcp import FastMCP
from app import db

# Initialize FastMCP Server
mcp = FastMCP("EcoTrackerServer")

GRID_INTENSITY_KG_PER_KWH = 0.385  # Global average grid factor

TRANSIT_FACTORS_G_PER_KM = {
    "gasoline car": 192,
    "diesel car": 171,
    "hybrid car": 110,
    "electric car": 45,
    "ev": 45,
    "suv": 245,
    "pickup truck": 260,
    "motorcycle": 103,
    "diesel bus": 95,
    "electric bus": 35,
    "bus": 95,
    "subway": 28,
    "metro": 28,
    "electric train": 35,
    "train": 35,
    "high speed rail": 15,
    "domestic flight": 255,
    "flight": 210,
    "plane": 210,
    "long haul flight": 190,
    "electric scooter": 12,
    "scooter": 12,
    "electric bike": 5,
    "e-bike": 5,
    "bicycle": 0,
    "bike": 0,
    "walking": 0,
    "walk": 0
}

APPLIANCES_DATA = {
    "refrigerator": {
        "standard_kwh": 550,
        "efficient_kwh": 160,
        "swap": "Upgrade to an Energy Star Inverter refrigerator; ensure door seals are intact and set to 37-40°F (3-4°C).",
    },
    "air conditioner": {
        "standard_kwh": 1800,
        "efficient_kwh": 850,
        "swap": "Switch to a modern variable-speed heat pump / inverter AC and maintain thermostat at 78°F (25°C) with ceiling fans.",
    },
    "ac": {
        "standard_kwh": 1800,
        "efficient_kwh": 850,
        "swap": "Switch to a modern variable-speed heat pump / inverter AC and maintain thermostat at 78°F (25°C) with ceiling fans.",
    },
    "washing machine": {
        "standard_kwh": 380,
        "efficient_kwh": 110,
        "swap": "Wash laundry in cold water (saves up to 85% of wash cycle energy) and run only full loads.",
    },
    "dryer": {
        "standard_kwh": 750,
        "efficient_kwh": 220,
        "swap": "Line-dry clothes when feasible, or upgrade to a heat-pump clothes dryer with moisture sensor.",
    },
    "water heater": {
        "standard_kwh": 3200,
        "efficient_kwh": 950,
        "swap": "Replace traditional electric resistance tank with a hybrid heat pump water heater (saves ~70% energy).",
    },
    "dishwasher": {
        "standard_kwh": 300,
        "efficient_kwh": 160,
        "swap": "Run only full loads, select Eco Mode, and disable heated dry cycle in favor of air drying.",
    },
    "lighting": {
        "standard_kwh": 140,
        "efficient_kwh": 20,
        "swap": "Replace remaining incandescent or halogen bulbs with ENERGY STAR certified LED bulbs (uses 85% less electricity).",
    },
    "bulb": {
        "standard_kwh": 140,
        "efficient_kwh": 20,
        "swap": "Replace remaining incandescent or halogen bulbs with ENERGY STAR certified LED bulbs (uses 85% less electricity).",
    }
}

WASTE_OFFSETS = {
    "plastic bottle": {"factor": 0.05, "unit": "items", "material": "PET Plastic"},
    "bottle": {"factor": 0.05, "unit": "items", "material": "Plastic"},
    "plastic": {"factor": 1.50, "unit": "kg", "material": "Rigid Plastic"},
    "aluminum can": {"factor": 0.09, "unit": "items", "material": "Aluminum"},
    "can": {"factor": 0.09, "unit": "items", "material": "Aluminum"},
    "aluminum": {"factor": 9.00, "unit": "kg", "material": "Bulk Aluminum"},
    "paper": {"factor": 1.15, "unit": "kg", "material": "Paper / Mixed Paper"},
    "cardboard": {"factor": 1.25, "unit": "kg", "material": "Corrugated Cardboard"},
    "glass bottle": {"factor": 0.12, "unit": "items", "material": "Glass Container"},
    "glass": {"factor": 0.35, "unit": "kg", "material": "Bulk Glass"},
    "food waste": {"factor": 0.85, "unit": "kg", "material": "Composted Organic Matter"},
    "compost": {"factor": 0.85, "unit": "kg", "material": "Composted Organic Matter"},
    "textile": {"factor": 3.80, "unit": "kg", "material": "Recycled / Donated Clothing"},
    "clothing": {"factor": 3.80, "unit": "kg", "material": "Recycled / Donated Clothing"}
}

FOOD_EMISSION_FACTORS = {
    "beef": {"co2e_per_kg": 60.0, "swap": "Lentils, beans, or cultivated plant-based patties (0.8 - 2.5 kg CO2e/kg, >95% reduction)"},
    "steak": {"co2e_per_kg": 60.0, "swap": "Grilled Portobello mushrooms or seitan steaks (1.5 - 2.0 kg CO2e/kg)"},
    "lamb": {"co2e_per_kg": 24.5, "swap": "Roasted spiced chickpeas or tempeh (1.0 - 2.0 kg CO2e/kg)"},
    "mutton": {"co2e_per_kg": 24.5, "swap": "Lentils or marinated tofu (0.8 - 2.0 kg CO2e/kg)"},
    "cheese": {"co2e_per_kg": 21.0, "swap": "Cashew or nutritional yeast plant-based artisan cheese (3.0 kg CO2e/kg, 85% reduction)"},
    "pork": {"co2e_per_kg": 7.2, "swap": "Tofu stir-fry or jackfruit carnitas (1.5 - 2.0 kg CO2e/kg)"},
    "poultry": {"co2e_per_kg": 6.1, "swap": "Marinated tofu, seitan, or chickpea cutlets (1.2 - 2.0 kg CO2e/kg)"},
    "chicken": {"co2e_per_kg": 6.1, "swap": "Marinated tofu, seitan, or chickpea cutlets (1.2 - 2.0 kg CO2e/kg)"},
    "fish": {"co2e_per_kg": 5.4, "swap": "Algae-derived Omega-3 foods and seasoned hearts of palm or tofu fillets"},
    "eggs": {"co2e_per_kg": 4.5, "swap": "Chickpea flour scramble or tofu scramble (1.0 kg CO2e/kg)"},
    "rice": {"co2e_per_kg": 4.0, "swap": "Quinoa, millet, or barley (1.2 - 1.6 kg CO2e/kg, lower methane impact)"},
    "dairy milk": {"co2e_per_kg": 3.2, "swap": "Oat milk or soy milk (0.9 kg CO2e/L, 70% reduction)"},
    "milk": {"co2e_per_kg": 3.2, "swap": "Oat milk or soy milk (0.9 kg CO2e/L, 70% reduction)"},
    "tofu": {"co2e_per_kg": 2.0, "swap": "Locally grown beans or lentils (0.8 kg CO2e/kg)"},
    "beans": {"co2e_per_kg": 0.8, "swap": "Already a gold-standard sustainable protein!"},
    "lentils": {"co2e_per_kg": 0.8, "swap": "Already a gold-standard sustainable protein!"},
    "vegetables": {"co2e_per_kg": 0.5, "swap": "Focus on seasonal, locally sourced produce to minimize transport"},
}

@mcp.tool()
def get_transit_emissions(transport_mode: str, distance_km: float) -> str:
    """Calculates carbon emissions for a given travel mode and distance using EPA/DEFRA benchmarks.
    
    Args:
        transport_mode: Mode of transport (e.g. gasoline car, diesel car, EV, hybrid, bus, electric train, plane, bicycle, walk).
        distance_km: Distance traveled in kilometers.
    """
    mode_clean = transport_mode.lower().strip()
    factor = 120
    matched = "average vehicle"
    
    # Match longest key first for precision (e.g., "electric car" before "car")
    sorted_factors = sorted(TRANSIT_FACTORS_G_PER_KM.items(), key=lambda x: len(x[0]), reverse=True)
    for key, val in sorted_factors:
        if key in mode_clean or mode_clean in key:
            factor = val
            matched = key
            break
            
    emissions_kg = round((factor * distance_km) / 1000.0, 3)
    
    # Comparison benchmarks
    train_emissions = round((35 * distance_km) / 1000.0, 3)
    ev_emissions = round((45 * distance_km) / 1000.0, 3)
    
    result = {
        "mode": matched.title(),
        "distance_km": distance_km,
        "emissions_kg_co2e": emissions_kg,
        "emission_factor_g_per_km": factor,
        "benchmarks": {
            "electric_train_kg": train_emissions,
            "ev_kg": ev_emissions,
            "train_savings_kg": max(0.0, round(emissions_kg - train_emissions, 3))
        },
        "source": "UK DEFRA / US EPA 2024 Transportation Benchmarks"
    }
    return json.dumps(result)

@mcp.tool()
def get_appliance_efficiency(appliance_name: str, hours_per_day: float = 0.0) -> str:
    """Returns annual energy consumption and eco-swap savings for household appliances.
    
    Args:
        appliance_name: The name of the appliance (e.g. refrigerator, ac, washing machine, dryer, dishwasher, water heater, lighting).
        hours_per_day: Optional usage hours per day for custom calculations.
    """
    name_clean = appliance_name.lower().strip()
    matched = None
    data = None
    
    sorted_appliances = sorted(APPLIANCES_DATA.items(), key=lambda x: len(x[0]), reverse=True)
    for key, val in sorted_appliances:
        if key in name_clean or name_clean in key:
            matched = key
            data = val
            break
            
    if not data:
        data = {
            "standard_kwh": 350,
            "efficient_kwh": 120,
            "swap": "Choose an ENERGY STAR certified model and utilize eco power-saving settings."
        }
        matched = appliance_name

    annual_std_emissions = round(data["standard_kwh"] * GRID_INTENSITY_KG_PER_KWH, 2)
    annual_eff_emissions = round(data["efficient_kwh"] * GRID_INTENSITY_KG_PER_KWH, 2)
    saved_kg = round(annual_std_emissions - annual_eff_emissions, 2)
    saved_kwh = data["standard_kwh"] - data["efficient_kwh"]

    result = {
        "appliance": matched.title(),
        "standard_annual_kwh": data["standard_kwh"],
        "energy_star_annual_kwh": data["efficient_kwh"],
        "standard_annual_co2e_kg": annual_std_emissions,
        "efficient_annual_co2e_kg": annual_eff_emissions,
        "potential_annual_savings_kg_co2e": saved_kg,
        "potential_annual_savings_kwh": saved_kwh,
        "recommended_swap": data["swap"]
    }
    return json.dumps(result)

@mcp.tool()
def get_waste_offset(item_name: str, quantity: float, unit: str = "items") -> str:
    """Calculates lifecycle carbon savings in kg CO2e from recycling or composting materials.
    
    Args:
        item_name: Material or item type (e.g. plastic bottle, aluminum can, paper, cardboard, food waste, glass, clothing).
        quantity: Quantity count or weight.
        unit: 'items' or 'kg'.
    """
    name_clean = item_name.lower().strip()
    matched = None
    factor = 0.5
    default_unit = unit
    material_label = item_name

    sorted_offsets = sorted(WASTE_OFFSETS.items(), key=lambda x: len(x[0]), reverse=True)
    for key, val in sorted_offsets:
        if key in name_clean or name_clean in key:
            matched = key
            factor = val["factor"]
            default_unit = val["unit"]
            material_label = val["material"]
            break

    total_savings = round(factor * quantity, 3)

    result = {
        "material": material_label,
        "quantity": quantity,
        "unit": default_unit,
        "carbon_savings_kg_co2e": total_savings,
        "offset_factor": factor,
        "recommendation": f"Recycling or composting {quantity} {default_unit} of {material_label} prevents landfill methane release and virgin extraction."
    }
    return json.dumps(result)

@mcp.tool()
def get_dietary_emissions(food_item: str, quantity_kg: float) -> str:
    """Calculates carbon emissions for foods and provides data-backed plant-based swaps.
    
    Args:
        food_item: Food product (e.g. beef, lamb, cheese, pork, chicken, fish, eggs, rice, milk).
        quantity_kg: Quantity in kilograms (or liters for milk).
    """
    name_clean = food_item.lower().strip()
    matched = "general food"
    factor = 2.5
    swap_info = "Choose whole plant foods and minimally processed local legumes."

    sorted_food = sorted(FOOD_EMISSION_FACTORS.items(), key=lambda x: len(x[0]), reverse=True)
    for key, val in sorted_food:
        if key in name_clean or name_clean in key:
            matched = key
            factor = val["co2e_per_kg"]
            swap_info = val["swap"]
            break

    total_emissions = round(factor * quantity_kg, 3)
    plant_alternative_emissions = round(1.5 * quantity_kg, 3)
    savings = max(0.0, round(total_emissions - plant_alternative_emissions, 3))

    result = {
        "food_item": matched.title(),
        "quantity_kg": quantity_kg,
        "emissions_kg_co2e": total_emissions,
        "emission_factor_kg_per_kg": factor,
        "suggested_swap": swap_info,
        "potential_savings_kg_co2e": savings,
        "source": "Poore & Nemecek (Science) Global Food System Benchmark"
    }
    return json.dumps(result)

@mcp.tool()
def get_user_profile_summary() -> str:
    """Retrieves user's persisted carbon footprint history, total emissions, savings, and milestones from database."""
    summary = db.get_user_summary()
    return json.dumps(summary)

@mcp.tool()
def get_flight_emissions(origin_iata: str, destination_iata: str, cabin_class: str = "economy", round_trip: bool = False) -> str:
    """Calculates flight distance, radiative forcing emissions, and electric rail comparisons.
    
    Args:
        origin_iata: 3-letter IATA code of departure airport (e.g. LHR, JFK, SFO, CDG).
        destination_iata: 3-letter IATA code of arrival airport (e.g. CDG, LAX, AMS, DXB).
        cabin_class: Cabin class (economy, premium_economy, business, first).
        round_trip: Whether the flight itinerary is a round trip.
    """
    from app.services.flight_calculator import calculate_flight_emissions
    res = calculate_flight_emissions(origin_iata, destination_iata, cabin_class, round_trip)
    return json.dumps(res)

@mcp.tool()
def get_grid_carbon_intensity(region: str = "auto") -> str:
    """Retrieves real-time or regional grid carbon intensity (g CO2e / kWh) and smart load scheduling.
    
    Args:
        region: Geographic region (e.g. 'uk', 'us-caiso', 'us-ercot', 'eu-france', 'eu-germany', 'australia', 'india', 'auto').
    """
    import asyncio
    from app.services.grid_intensity import get_grid_carbon_intensity as fetch_grid
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        res = loop.run_until_complete(fetch_grid(region))
    else:
        res = asyncio.run(fetch_grid(region))
    return json.dumps(res)

if __name__ == "__main__":
    mcp.run()
