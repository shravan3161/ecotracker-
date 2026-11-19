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

"""Airport-to-Airport Aviation Carbon Intelligence Service.

Computes great-circle flight distances (Haversine formula), passenger emissions
using DEFRA/ICAO methodologies with high-altitude Radiative Forcing Index (RFI),
cabin class multipliers, and electric train substitution benchmarks.
"""

import math
from typing import Dict, Any, Tuple, Optional

# Major global airport coordinates (Latitude, Longitude, City, Country)
AIRPORT_COORDINATES: Dict[str, Tuple[float, float, str, str]] = {
    "LHR": (51.4700, -0.4543, "London", "UK"),
    "LGW": (51.1537, -0.1821, "London Gatwick", "UK"),
    "CDG": (49.0097, 2.5479, "Paris", "France"),
    "AMS": (52.3105, 4.7683, "Amsterdam", "Netherlands"),
    "FRA": (50.0379, 8.5622, "Frankfurt", "Germany"),
    "ZRH": (47.4582, 8.5555, "Zurich", "Switzerland"),
    "JFK": (40.6413, -73.7781, "New York", "USA"),
    "EWR": (40.6895, -74.1745, "Newark", "USA"),
    "LAX": (33.9416, -118.4085, "Los Angeles", "USA"),
    "SFO": (37.6213, -122.3790, "San Francisco", "USA"),
    "ORD": (41.9742, -87.9073, "Chicago", "USA"),
    "BOS": (42.3656, -71.0096, "Boston", "USA"),
    "SEA": (47.4502, -122.3088, "Seattle", "USA"),
    "DXB": (25.2532, 55.3657, "Dubai", "UAE"),
    "SIN": (1.3644, 103.9915, "Singapore", "Singapore"),
    "HND": (35.5494, 139.7798, "Tokyo Haneda", "Japan"),
    "NRT": (35.7720, 140.3929, "Tokyo Narita", "Japan"),
    "SYD": (-33.9399, 151.1753, "Sydney", "Australia"),
    "DEL": (28.5562, 77.1000, "New Delhi", "India"),
    "BOM": (19.0896, 72.8656, "Mumbai", "India"),
    "BLR": (13.1986, 77.7066, "Bengaluru", "India"),
}

# DEFRA 2024 Passenger km emission factors (kg CO2e per passenger-km with RFI)
# Short-haul (<3700 km), Long-haul (>=3700 km)
CABIN_MULTIPLIERS = {
    "economy": 1.0,
    "premium_economy": 1.6,
    "business": 2.9,
    "first": 4.0
}

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates."""
    r = 6371.0  # Earth radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

def calculate_flight_emissions(
    origin_iata: str,
    destination_iata: str,
    cabin_class: str = "economy",
    round_trip: bool = False
) -> Dict[str, Any]:
    """Computes flight distance, carbon footprint, and high-speed rail benchmarks."""
    orig = origin_iata.strip().upper()
    dest = destination_iata.strip().upper()
    cabin = cabin_class.strip().lower()
    if cabin not in CABIN_MULTIPLIERS:
        cabin = "economy"

    orig_info = AIRPORT_COORDINATES.get(orig)
    dest_info = AIRPORT_COORDINATES.get(dest)

    if not orig_info or not dest_info:
        # Fallback to estimated generic flight if unknown IATA
        dist_km = 1200.0
        orig_city = orig
        dest_city = dest
    else:
        dist_km = haversine_distance_km(orig_info[0], orig_info[1], dest_info[0], dest_info[1])
        # Add 50 km for typical taxiing & circuit holding patterns
        dist_km += 50.0
        orig_city = f"{orig_info[2]} ({orig})"
        dest_city = f"{dest_info[2]} ({dest})"

    multiplier = 2.0 if round_trip else 1.0
    total_dist = round(dist_km * multiplier, 1)

    # Base factor: Short-haul 0.155 kg/km, Long-haul 0.148 kg/km (Economy with RFI)
    base_factor = 0.155 if total_dist < 3700 else 0.148
    cabin_mult = CABIN_MULTIPLIERS[cabin]
    
    emissions_kg = round(total_dist * base_factor * cabin_mult, 2)

    # Train comparison (0.035 kg/km for high speed electric train)
    train_emissions_kg = round(total_dist * 0.035, 2)
    train_savings_kg = round(max(0.0, emissions_kg - train_emissions_kg), 2)
    train_viable = total_dist <= 1500

    return {
        "origin": orig_city,
        "destination": dest_city,
        "distance_km": total_dist,
        "round_trip": round_trip,
        "cabin_class": cabin.replace("_", " ").title(),
        "emissions_kg_co2e": emissions_kg,
        "carbon_intensity_factor_kg_km": round(base_factor * cabin_mult, 3),
        "radiative_forcing_multiplier": "1.9x (includes high-altitude NOx & contrails)",
        "train_alternative": {
            "viable_land_corridor": train_viable,
            "train_emissions_kg": train_emissions_kg,
            "potential_savings_kg": train_savings_kg,
            "savings_percentage": round((train_savings_kg / max(emissions_kg, 1.0)) * 100, 1)
        },
        "summary": f"{orig_city} to {dest_city} ({total_dist} km, {cabin.title()}) produces {emissions_kg} kg CO2e."
    }
