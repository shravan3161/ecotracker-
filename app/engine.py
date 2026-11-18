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

"""Dynamic Environmental Reasoning & Calculation Engine.

Parses arbitrary user activities (transit, flights, diet, energy, shopping, waste)
and computes mathematically grounded, verified carbon footprint breakdowns with
tailored eco-swaps and contextual advice.
"""

import re
from typing import Dict, Any, List, Tuple

# Scientific emission factors (DEFRA, EPA, Our World In Data)
EMISSION_FACTORS = {
    # Transit (kg CO2e per km)
    "flight": 0.255,
    "domestic flight": 0.255,
    "international flight": 0.195,
    "suv": 0.235,
    "gasoline car": 0.192,
    "car": 0.192,
    "diesel car": 0.171,
    "motorcycle": 0.115,
    "motorbike": 0.115,
    "hybrid car": 0.110,
    "hybrid": 0.110,
    "bus": 0.089,
    "electric car": 0.045,
    "ev": 0.045,
    "tesla": 0.045,
    "train": 0.035,
    "subway": 0.030,
    "metro": 0.030,
    "electric train": 0.035,
    "bicycle": 0.0,
    "bike": 0.0,
    "walking": 0.0,
    "walk": 0.0,

    # Food & Diet (kg CO2e per kg or unit)
    "beef": 60.0,
    "steak": 60.0,
    "burger": 15.0,        # ~250g beef patty equivalent
    "lamb": 24.5,
    "mutton": 24.5,
    "cheese": 21.0,
    "pork": 7.2,
    "bacon": 7.2,
    "chicken": 6.1,
    "poultry": 6.1,
    "fish": 5.4,
    "salmon": 5.4,
    "eggs": 4.5,
    "rice": 4.0,
    "pizza": 3.8,
    "milk": 3.2,
    "coffee": 0.28,        # per cup
    "beer": 0.55,          # per pint
    "bread": 1.4,
    "pasta": 1.6,
    "tofu": 2.0,
    "beans": 0.8,
    "lentils": 0.8,
    "vegetables": 0.5,
    "salad": 0.4,

    # Appliances & Energy (kg CO2e per hour or unit, grid avg 0.385 kg/kWh)
    "ac": 0.65,             # per hour (~1.7 kW)
    "air conditioner": 0.65,
    "space heater": 0.58,   # per hour (1.5 kW)
    "heater": 0.58,
    "water heater": 3.2,    # per day
    "refrigerator": 0.58,   # per day
    "fridge": 0.58,
    "dryer": 1.85,          # per cycle
    "clothes dryer": 1.85,
    "washing machine": 0.48,# per cycle
    "washer": 0.48,
    "dishwasher": 0.62,     # per cycle
    "gaming pc": 0.18,      # per hour
    "tv": 0.05,             # per hour
    "laptop": 0.02,         # per hour

    # Consumer Goods & Shopping (embodied kg CO2e)
    "smartphone": 70.0,
    "iphone": 70.0,
    "laptop computer": 280.0,
    "tablet": 90.0,
    "jeans": 33.4,
    "t-shirt": 7.5,
    "shirt": 7.5,
    "shoes": 14.0,
    "jacket": 25.0,
}

def analyze_query(query: str) -> Dict[str, Any]:
    """Dynamically parses and analyzes any arbitrary sustainability query."""
    lower = query.lower()
    
    # 1. Extract numeric quantities and distances
    dist_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?|miles?|mi)\b", lower)
    weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms?|grams?|g|lbs?|pounds?)\b", lower)
    hours_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b", lower)
    count_match = re.search(r"(\d+)\s*(?:cups?|items?|meals?|trips?|units?|cycles?|pints?|glasses?|bottles?|pairs?)\b", lower)
    generic_num = re.search(r"\b(\d+(?:\.\d+)?)\b", lower)

    # 2. Match activities
    detected = []
    primary_category = "general"

    # Transit Detection
    transit_keys = [
        "domestic flight", "international flight", "flight", "flew", "fly", "flying", 
        "plane", "suv", "gasoline car", "diesel car", "hybrid car", "electric car", 
        "ev", "tesla", "motorcycle", "motorbike", "bus", "electric train", "train", 
        "subway", "metro", "bicycle", "bike", "walking", "walk", "car", "drove", "drive"
    ]
    for tk in transit_keys:
        if tk in lower or (tk == "car" and re.search(r"\bcar\b", lower)):
            mapped_key = "flight" if tk in ["flight", "flew", "fly", "flying", "plane", "domestic flight", "international flight"] else (
                "gasoline car" if tk in ["car", "drove", "drive"] else tk
            )
            factor = EMISSION_FACTORS.get(mapped_key, 0.192)
            # Determine distance
            km = 45.0
            has_explicit_dist = False
            if dist_match:
                val = float(dist_match.group(1))
                if "mile" in dist_match.group(0) or "mi" in dist_match.group(0):
                    km = round(val * 1.60934, 1)
                else:
                    km = val
                has_explicit_dist = True
            elif mapped_key == "flight":
                km = 800.0 if "domestic" in lower else 2400.0
                has_explicit_dist = True if ("domestic" in lower or "international" in lower) else False
            else:
                km = 25.0  # standard average daily commute baseline

            co2 = round(km * factor, 2)
            
            # Compute swap savings
            if factor > 0.045:
                train_factor = EMISSION_FACTORS["electric train"]
                savings = round(max(0.0, (km * factor) - (km * train_factor)), 2)
                swap_text = f"Taking an electric train for this {km} km journey would emit just {round(km * train_factor, 2)} kg, saving {savings} kg CO2e ({round((savings/co2)*100)}% reduction)."
            else:
                savings = 0.0
                swap_text = f"Excellent low-carbon transit choice! You avoided substantial road emissions."

            formula_text = f"{km} km × {factor} kg CO2e/km"
            if not has_explicit_dist:
                formula_text += " (using standard 25 km commute baseline)"

            detected.append({
                "category": "transportation",
                "title": f"🚗 Travel via {tk.title()} ({km} km)",
                "emissions": co2,
                "savings": savings,
                "formula": formula_text,
                "swap": swap_text,
                "has_number": has_explicit_dist
            })
            primary_category = "transportation"
            break

    # Diet Detection
    food_keys = [
        "burger", "beef", "steak", "lamb", "mutton", "cheese", "pork", "bacon", 
        "chicken", "poultry", "salmon", "fish", "eggs", "pizza", "rice", "milk", 
        "coffee", "beer", "tofu", "beans", "lentils", "salad", "bread"
    ]
    for fk in food_keys:
        if fk in lower:
            qty = 0.35 if fk in ["beef", "steak", "lamb", "pork", "chicken", "fish"] else 1.0
            if weight_match:
                w_val = float(weight_match.group(1))
                w_unit = weight_match.group(0).lower()
                if "g" in w_unit and "kg" not in w_unit:
                    qty = w_val / 1000.0
                elif "lb" in w_unit:
                    qty = round(w_val * 0.453592, 2)
                else:
                    qty = w_val
            elif count_match and fk in ["coffee", "beer", "burger", "pizza"]:
                qty = float(count_match.group(1))

            factor = EMISSION_FACTORS[fk]
            co2 = round(qty * factor, 2)
            plant_factor = 1.2
            savings = round(max(0.0, co2 - (qty * plant_factor)), 2)
            
            swap_text = (
                f"Swapping {fk.title()} for a chef-crafted plant-based alternative (lentils, beans, or savory mushroom/tofu) "
                f"emits only ~{round(qty * plant_factor, 2)} kg, avoiding {savings} kg CO2e."
            )

            detected.append({
                "category": "diet",
                "title": f"🥗 Diet & Nutrition ({fk.title()})",
                "emissions": co2,
                "savings": savings,
                "formula": f"{qty} units/kg × {factor} kg CO2e/unit",
                "swap": swap_text
            })
            if primary_category == "general":
                primary_category = "diet"
            break

    # Energy / Appliance Detection
    appliance_keys = [
        "ac", "air conditioner", "space heater", "heater", "dryer", "clothes dryer", 
        "washing machine", "washer", "dishwasher", "refrigerator", "fridge", 
        "water heater", "gaming pc", "tv", "laptop"
    ]
    for ak in appliance_keys:
        if ak in lower:
            hours = 4.0
            if hours_match:
                hours = float(hours_match.group(1))
            elif count_match:
                hours = float(count_match.group(1))

            factor = EMISSION_FACTORS[ak]
            co2 = round(hours * factor, 2)
            savings = round(co2 * 0.40, 2)
            swap_text = (
                f"Upgrading to an ENERGY STAR or high-efficiency inverter model with smart thermostat "
                f"scheduling cuts operating emissions by ~40%, saving {savings} kg CO2e."
            )

            detected.append({
                "category": "energy",
                "title": f"⚡ Appliance Power ({ak.upper() if len(ak)<=3 else ak.title()})",
                "emissions": co2,
                "savings": savings,
                "formula": f"{hours} hrs/cycles × {factor} kg CO2e/unit",
                "swap": swap_text
            })
            if primary_category == "general":
                primary_category = "energy"
            break

    # Shopping & Goods Detection
    goods_keys = ["smartphone", "iphone", "laptop computer", "tablet", "jeans", "t-shirt", "shirt", "shoes", "jacket"]
    for gk in goods_keys:
        if gk in lower:
            qty = 1.0
            if count_match:
                qty = float(count_match.group(1))
            factor = EMISSION_FACTORS[gk]
            co2 = round(qty * factor, 2)
            savings = round(co2 * 0.65, 2)
            swap_text = (
                f"Choosing certified refurbished hardware or circular/recycled fabrics avoids "
                f"raw extraction emissions, saving ~{savings} kg CO2e ({round((savings/co2)*100)}% avoided)."
            )

            detected.append({
                "category": "shopping",
                "title": f"🛍️ Consumer Purchase ({gk.title()})",
                "emissions": co2,
                "savings": savings,
                "formula": f"{qty} item(s) × {factor} kg CO2e/item",
                "swap": swap_text
            })
            if primary_category == "general":
                primary_category = "shopping"
            break

    total_emissions = round(sum(d["emissions"] for d in detected), 2)
    total_savings = round(sum(d["savings"] for d in detected), 2)

    return {
        "items": detected,
        "total_emissions_kg": total_emissions,
        "total_saved_kg": total_savings,
        "category": primary_category if detected else "none",
        "has_activity": len(detected) > 0
    }


def handle_chatbot_turn(query: str, history: List[Dict[str, str]] = None, user_summary: Dict[str, Any] = None) -> Dict[str, Any]:
    """Conversational AI Chatbot handler with memory, greetings, and contextual advice."""
    clean = query.strip()
    lower = clean.lower()
    
    # 1. Greetings
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy", "sup", "yo", "hi there", "hello there"]
    if lower in greetings or re.match(r"^(hi|hello|hey|greetings)\b", lower):
        return {
            "reply": (
                "👋 **Hey there! Welcome to EcoTracker AI.**\n\n"
                "I'm your personal conversational carbon advisor. You can chat with me naturally about your daily lifestyle—"
                "like your commute, flights, what you had for lunch, or home appliances you ran.\n\n"
                "I will calculate your real-time carbon footprint with scientific precision and suggest tailored, high-impact eco-swaps.\n\n"
                "**What activity would you like to explore today?** *(e.g. \"I drove 45 km to work\", \"Had a beef burger for lunch\", or \"Flew 1000 km\")*"
            ),
            "is_chat_only": True,
            "total_emissions_kg": 0.0,
            "total_saved_kg": 0.0,
            "category": "general"
        }

    # 2. Gratitude / Positive Sentiment
    gratitude = ["thank you", "thanks", "thx", "appreciate it", "great job", "awesome", "cool", "nice", "perfect"]
    if lower in gratitude or any(g in lower for g in ["thank you", "thanks", "awesome"]):
        return {
            "reply": (
                "😊 **You're very welcome!** Every green choice makes a real, measurable difference.\n\n"
                "Let me know if you want to evaluate another trip, compare eco-swaps, or review your daily budget goal! 🌱"
            ),
            "is_chat_only": True,
            "total_emissions_kg": 0.0,
            "total_saved_kg": 0.0,
            "category": "general"
        }

    # 3. Dismissal / Frustration / Rude inputs
    dismissive = ["shutup", "shut up", "quiet", "be quiet", "stop talking", "go away", "leave me alone", "fuck off", "stfu"]
    if any(d in lower for d in dismissive):
        return {
            "reply": (
                "🌿 **Understood!** I'll pause right here.\n\n"
                "Whenever you'd like to calculate travel emissions, compare eco-swaps, or track your carbon budget, "
                "just send me a message anytime!"
            ),
            "is_chat_only": True,
            "total_emissions_kg": 0.0,
            "total_saved_kg": 0.0,
            "category": "general"
        }

    # 4. Bot Identity & Capabilities
    if any(q in lower for q in ["who are you", "what are you", "what can you do", "help me", "how does this work"]):
        return {
            "reply": (
                "🤖 **I'm your EcoTracker AI Sustainability Companion!**\n\n"
                "Here is what you can ask me to do in plain English:\n"
                "- 🚗 **Travel & Transit:** *\"Calculate emissions for driving 50 km in a gasoline car vs EV\"*\n"
                "- ✈️ **Aviation:** *\"What is the footprint of an 800 km domestic flight?\"*\n"
                "- 🥗 **Food & Diet:** *\"I had a 250g steak dinner and 2 beers\"*\n"
                "- ⚡ **Appliances & Energy:** *\"How much CO2 does running an AC for 6 hours emit?\"*\n"
                "- 📊 **Profile & Badges:** *\"Show my sustainability summary\"*\n"
                "- 📌 **Logging:** Say *\"log this to my profile\"* anytime to record verified actions!\n\n"
                "What would you like to check right now?"
            ),
            "is_chat_only": True,
            "total_emissions_kg": 0.0,
            "total_saved_kg": 0.0,
            "category": "general"
        }

    # 4. Contextual Follow-Up Swaps (e.g. "what about train?", "how about an electric car?")
    if any(w in lower for w in ["what about", "how about", "what if i take", "what if i use"]):
        # Search past history for distance
        past_km = None
        if history:
            for msg in reversed(history):
                m_text = msg.get("content", "").lower()
                d_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?|miles?)\b", m_text)
                if d_match:
                    past_km = float(d_match.group(1))
                    if "mile" in d_match.group(0):
                        past_km = round(past_km * 1.60934, 1)
                    break

        km_target = past_km or 45.0
        if "train" in lower:
            co2 = round(km_target * EMISSION_FACTORS["electric train"], 2)
            car_co2 = round(km_target * EMISSION_FACTORS["gasoline car"], 2)
            saved = round(max(0.0, car_co2 - co2), 2)
            pct = round((saved / car_co2) * 100) if car_co2 > 0 else 0
            return {
                "reply": (
                    f"🚆 **Great question! Comparing to an Electric Train:**\n\n"
                    f"For that **{km_target} km** journey, an electric train emits only **`{co2} kg CO2e`** "
                    f"(compared to `{car_co2} kg` in a standard car).\n\n"
                    f"🌟 **Net Impact:** You avoid **`{saved} kg CO2e` ({pct}% reduction)**!\n\n"
                    f"Would you like me to log this eco-friendly transit choice to your dashboard? Say **\"log it\"** to record it."
                ),
                "is_chat_only": False,
                "total_emissions_kg": co2,
                "total_saved_kg": saved,
                "category": "transportation"
            }
        elif "electric" in lower or "ev" in lower:
            co2 = round(km_target * EMISSION_FACTORS["electric car"], 2)
            car_co2 = round(km_target * EMISSION_FACTORS["gasoline car"], 2)
            saved = round(max(0.0, car_co2 - co2), 2)
            pct = round((saved / car_co2) * 100) if car_co2 > 0 else 0
            return {
                "reply": (
                    f"⚡ **Electric Vehicle (EV) Analysis:**\n\n"
                    f"Covering that **{km_target} km** route in an EV emits only **`{co2} kg CO2e`** "
                    f"(based on average grid charging intensity of 45 g/km).\n\n"
                    f"🌟 **Net Impact:** You avoid **`{saved} kg CO2e` ({pct}% reduction)** vs gasoline driving!\n\n"
                    f"Would you like me to save this EV trip to your profile? Say **\"log it\"**."
                ),
                "is_chat_only": False,
                "total_emissions_kg": co2,
                "total_saved_kg": saved,
                "category": "transportation"
            }

    # 5. Full Activity Parsing & Conversational Breakdown
    analysis = analyze_query(clean)
    items = analysis["items"]
    tot_co2 = analysis["total_emissions_kg"]
    tot_saved = analysis["total_saved_kg"]
    cat = analysis["category"]

    # If no carbon-emitting activity was identified in query
    if not items:
        return {
            "reply": (
                f"💬 *\"{clean}\"*\n\n"
                "I didn't detect any specific lifestyle or carbon-emitting activity in your message.\n\n"
                "To calculate your real-time carbon footprint, tell me about an activity such as:\n"
                "- 🚗 **Travel & Commute:** *\"I drove 25 km in a gasoline car\"*\n"
                "- ✈️ **Aviation:** *\"Took an 800 km domestic flight\"*\n"
                "- 🥗 **Food & Dining:** *\"Ate a 250g steak dinner\"*\n"
                "- ⚡ **Home Energy:** *\"Ran my air conditioner for 4 hours\"*\n\n"
                "*Tip: You can include exact numbers (e.g., \"25 km\", \"250g\"), or just state the activity and I'll apply industry average benchmarks!*"
            ),
            "is_chat_only": True,
            "total_emissions_kg": 0.0,
            "total_saved_kg": 0.0,
            "category": "general"
        }

    lines = [
        f"🌿 **I analyzed your activity:** *\"{clean}\"*\n",
        f"Here is your calculated carbon impact breakdown:\n"
    ]

    for it in items:
        lines.append(f"**{it['title']}**")
        lines.append(f"- 💨 **Emissions:** `{it['emissions']} kg CO2e` *(Formula: {it['formula']})*")
        lines.append(f"- 💡 **Eco-Swap:** {it['swap']}\n")

    lines.append(f"---")
    lines.append(f"📊 **Total Activity Footprint:** `{tot_co2} kg CO2e`")
    if tot_saved > 0:
        lines.append(f"🌱 **Potential Avoided Emissions:** `{tot_saved} kg CO2e`")

    has_unspecified = any(not it.get("has_number", True) for it in items)
    if has_unspecified:
        lines.append("\n💡 *Benchmark Note: Since no specific numbers were provided, this was calculated using standard daily averages. Reply with your actual numbers (e.g. \"it was 15 km\") and I'll recalculate!*")

    lines.append(f"\n*Would you like me to log this to your dashboard? Reply **\"log this\"** or use the quick action button below.*")

    return {
        "reply": "\n".join(lines),
        "is_chat_only": False,
        "total_emissions_kg": tot_co2,
        "total_saved_kg": tot_saved,
        "category": cat
    }

