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

"""Universal Cloud LLM Client for EcoTracker.

Supports Google Gemini (Free tier) or Groq / LLaMA (Free tier) cloud APIs.
Calculates emission estimates and custom green swaps dynamically based on user input.
"""

import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are EcoTracker AI, an intelligent, warm, and encouraging environmental carbon advisor and conversational chatbot.
Your goal is to have natural, engaging conversations helping users understand and reduce their carbon footprint.
When conversing:
1. Greet the user warmly and converse like a friendly sustainability expert.
2. When the user mentions activities (travel, food, appliances, shopping, waste), calculate the estimated carbon emissions (kg CO2 equivalent) using realistic emission factors (e.g., gasoline car = 0.192 kg/km, EV = 0.045 kg/km, domestic flight = 0.255 kg/km, beef = 60 kg/kg, cheese = 21 kg/kg, average electricity = 0.385 kg/kWh).
3. Recommend specific, high-impact eco-swaps with quantified carbon savings.
4. Maintain conversational context across follow-up questions.
5. Keep your tone encouraging, concise, and helpful. Format with clean Markdown (bold metrics, bullet points, emoji accents)."""

async def generate_llm_response(prompt: str, custom_key: str = "", history: list = None) -> str:
    """Dispatches user prompt to free cloud LLM (Groq or Gemini) dynamically with conversation history."""
    
    # Check custom key first, then environment
    key = custom_key.strip() or os.getenv("GROQ_API_KEY", "") or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not key:
        return ""

    is_groq = key.startswith("gsk_") or "groq" in key.lower()

    if is_groq:
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if history:
                for h in history[-8:]:
                    role = "assistant" if h.get("role") in ["assistant", "agent", "bot"] else "user"
                    messages.append({"role": role, "content": h.get("content", "")})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages,
                        "temperature": 0.5,
                        "max_tokens": 850
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    print(f"Groq Cloud error ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"Groq Cloud exception: {e}")

    # Gemini Cloud Endpoint
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={key}"
        contents = []
        if history:
            for h in history[-8:]:
                role = "model" if h.get("role") in ["assistant", "agent", "bot"] else "user"
                contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Gemini Cloud error ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"Gemini Cloud exception: {e}")

    return ""

