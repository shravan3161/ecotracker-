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

"""Unit tests for the EcoTracker FastMCP Server Tools."""

import json
import pytest
from app.mcp_server import (
    get_transit_emissions,
    get_appliance_efficiency,
    get_waste_offset,
    get_dietary_emissions,
    get_user_profile_summary
)

def test_transit_emissions_gasoline_car():
    res_str = get_transit_emissions(transport_mode="gasoline car", distance_km=50.0)
    data = json.loads(res_str)
    
    assert data["distance_km"] == 50.0
    # 50 km * 192 g/km / 1000 = 9.6 kg CO2e
    assert data["emissions_kg_co2e"] == 9.6
    assert data["emission_factor_g_per_km"] == 192
    assert "benchmarks" in data
    assert data["benchmarks"]["electric_train_kg"] < data["emissions_kg_co2e"]

def test_transit_emissions_train_and_walking():
    train_res = json.loads(get_transit_emissions(transport_mode="electric train", distance_km=100.0))
    # 100 km * 35 g/km / 1000 = 3.5 kg
    assert train_res["emissions_kg_co2e"] == 3.5

    walk_res = json.loads(get_transit_emissions(transport_mode="walking", distance_km=10.0))
    assert walk_res["emissions_kg_co2e"] == 0.0

def test_appliance_efficiency():
    fridge_res = json.loads(get_appliance_efficiency(appliance_name="refrigerator"))
    assert "Refrigerator" in fridge_res["appliance"]
    assert fridge_res["potential_annual_savings_kg_co2e"] > 0
    assert "Energy Star" in fridge_res["recommended_swap"] or "Inverter" in fridge_res["recommended_swap"]

    unknown_res = json.loads(get_appliance_efficiency(appliance_name="unusual_device_xyz"))
    assert unknown_res["standard_annual_kwh"] > 0

def test_waste_offset():
    plastic_res = json.loads(get_waste_offset(item_name="plastic bottle", quantity=20.0))
    assert plastic_res["quantity"] == 20.0
    # 20 * 0.05 = 1.0 kg CO2e
    assert plastic_res["carbon_savings_kg_co2e"] == 1.0

    aluminum_res = json.loads(get_waste_offset(item_name="aluminum can", quantity=10.0))
    # 10 * 0.09 = 0.9 kg CO2e
    assert aluminum_res["carbon_savings_kg_co2e"] == 0.9

def test_dietary_emissions():
    beef_res = json.loads(get_dietary_emissions(food_item="beef", quantity_kg=1.0))
    assert beef_res["emissions_kg_co2e"] == 60.0
    assert beef_res["potential_savings_kg_co2e"] > 50.0

    beans_res = json.loads(get_dietary_emissions(food_item="beans", quantity_kg=2.0))
    # 2 * 0.8 = 1.6 kg
    assert beans_res["emissions_kg_co2e"] == 1.6

def test_user_profile_summary():
    summary_str = get_user_profile_summary()
    summary = json.loads(summary_str)
    assert "total_emissions_kg" in summary
    assert "total_saved_kg" in summary
    assert "badges" in summary
