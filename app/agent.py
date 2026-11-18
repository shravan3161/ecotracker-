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

"""EcoTracker Root Workflow Agent.

Coordinates multi-agent carbon footprint calculations, eco-swap recommendations,
enterprise security checkpoints, and human-in-the-loop (HITL) approval with
database persistence.
"""

import os
import sys
import re
from typing import Any
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool, ToolContext
from google.adk.workflow import Workflow, node, START, Edge, DEFAULT_ROUTE
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.adk.apps import App
from google.genai import types
from mcp import StdioServerParameters
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

from app.config import config
from app.security import inspect_and_sanitize, write_audit_log
from app import db

# Build connection parameters for the local MCP server running as a subprocess
current_dir = os.path.dirname(os.path.abspath(__file__))
mcp_server_path = os.path.join(current_dir, "mcp_server.py")

mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_server_path],
        )
    )
)

# Specialized Sub-Agent 1: Footprint Calculator (uses MCP emission data)
footprint_calculator_agent = LlmAgent(
    name="footprint_calculator_agent",
    model=config.model,
    instruction="""You are a carbon footprint calculator.
Analyze the user's activity details (such as transportation, appliances, food/diet, purchases, or waste).
Estimate the carbon footprint in kilograms of CO2 equivalent (kg CO2e).
Use the available MCP tools (`get_transit_emissions`, `get_appliance_efficiency`, `get_dietary_emissions`, and `get_waste_offset`) to obtain accurate emission data and efficiency factors.
Be concise and output the exact breakdown of the calculation including factors used.""",
    tools=[mcp_toolset],
)

# Specialized Sub-Agent 2: Swap Recommender (uses MCP tools to suggest high-impact alternatives)
swap_recommender_agent = LlmAgent(
    name="swap_recommender_agent",
    model=config.model,
    instruction="""You are an environmental swap recommender.
Based on the user's carbon footprint calculation or activity, recommend 2-3 specific, actionable, and higher-impact eco-friendly alternatives (such as switching transit modes, adopting Energy Star/heat-pump appliances, low-carbon diet alternatives, or waste recycling).
Use the available MCP tools (`get_transit_emissions`, `get_appliance_efficiency`, `get_dietary_emissions`, and `get_waste_offset`) to back your suggestions with concrete kg CO2e savings data.
Be inspiring, concise, and highlight the percentage or kg reduction for each swap.""",
    tools=[mcp_toolset],
)

# Custom tool wrappers that store results into session state
async def run_footprint_calculator(query: str, tool_context: ToolContext) -> str:
    """Calculates the carbon footprint of an activity based on details.
    
    Args:
        query: Details of the activity, transit, food, energy, or purchase.
    """
    agent_tool = AgentTool(footprint_calculator_agent)
    res = await agent_tool.run_async(args={"request": query}, tool_context=tool_context)
    
    recommendations = tool_context.state.get("recommendations", {})
    recommendations["footprint"] = res
    tool_context.state["recommendations"] = recommendations
    return res

async def run_swap_recommender(query: str, tool_context: ToolContext) -> str:
    """Recommends sustainable swaps and alternatives based on a footprint or query.
    
    Args:
        query: Carbon footprint calculation details or query.
    """
    footprint = tool_context.state.get("recommendations", {}).get("footprint", "")
    enriched_query = query
    if footprint and footprint not in query:
        enriched_query = f"Footprint context:\n{footprint}\n\nUser request: {query}"
        
    agent_tool = AgentTool(swap_recommender_agent)
    res = await agent_tool.run_async(args={"request": enriched_query}, tool_context=tool_context)
    
    recommendations = tool_context.state.get("recommendations", {})
    recommendations["swaps"] = res
    tool_context.state["recommendations"] = recommendations
    return res

# Main Orchestrator Agent
orchestrator_agent = LlmAgent(
    name="orchestrator_agent",
    model=config.model,
    instruction="""You are the EcoTracker Orchestrator.
You help users calculate carbon footprints and discover actionable sustainable alternatives.
To calculate a carbon footprint, use the `run_footprint_calculator` tool.
To get alternative recommendation swaps, use the `run_swap_recommender` tool.
Synthesize their responses into a single cohesive response containing the footprint calculation and the eco-swap recommendations.
Always invoke both tools when a footprint or swap is requested.""",
    tools=[
        run_footprint_calculator,
        run_swap_recommender,
    ],
)

# --- Workflow Node Implementations ---

@node
async def security_checkpoint(ctx: Context, node_input: types.Content) -> Event:
    """Inspects and sanitizes user input before processing."""
    user_text = ""
    if isinstance(node_input, types.Content):
        for part in node_input.parts:
            if part.text:
                user_text += part.text
    elif isinstance(node_input, str):
        user_text = node_input

    sec_result = inspect_and_sanitize(
        user_text=user_text,
        injection_enabled=config.injection_detection_enabled,
        pii_enabled=config.pii_redaction_enabled,
    )

    if not sec_result.passed:
        return Event(output=sec_result.rejection_reason, route="security_event")

    # Store sanitized query in session state
    ctx.state["user_query"] = sec_result.sanitized_text
    return Event(output=sec_result.sanitized_text, route="pass")

@node
async def security_event_node(ctx: Context, node_input: str) -> Event:
    """Handles security violations and terminates workflow safely."""
    write_audit_log(
        severity="CRITICAL",
        action="security_event_triggered",
        details={"message": node_input}
    )
    content = types.Content(role='model', parts=[types.Part.from_text(text=node_input)])
    yield Event(content=content)
    yield Event(output=content)

@node
async def post_process_node(ctx: Context, node_input: Any) -> Event:
    """Checks for profile summary queries or HITL logging requests."""
    text = ""
    if isinstance(node_input, str):
        text = node_input
    elif hasattr(node_input, "parts"):
        for part in node_input.parts:
            if part.text:
                text += part.text
    elif isinstance(node_input, dict) and "parts" in node_input:
        for part in node_input["parts"]:
            if isinstance(part, dict) and "text" in part:
                text += part["text"]
    else:
        text = str(node_input)

    user_query = ctx.state.get("user_query", "").lower()

    # If user requests their sustainability summary or profile history, augment output
    summary_triggers = ["summary", "profile", "my history", "how much have i saved", "my badges", "my stats"]
    if any(st in user_query for st in summary_triggers):
        summary = db.get_user_summary()
        summary_md = f"\n\n---\n### 📊 Your Profile Summary & History\n" \
                     f"- **Total Emissions Logged:** {summary['total_emissions_kg']} kg CO2e\n" \
                     f"- **Total CO2e Saved:** {summary['total_saved_kg']} kg CO2e\n" \
                     f"- **Activities Recorded:** {summary['total_entries']}\n"
        if summary["badges"]:
            badges_str = ", ".join([f"🏅 **{b['name']}**" for b in summary["badges"]])
            summary_md += f"- **Milestones Unlocked:** {badges_str}\n"
        text += summary_md

    # Check if user requested logging / persistence
    needs_approval = "log" in user_query or "save" in user_query

    if needs_approval:
        write_audit_log(
            severity="INFO",
            action="hitl_requested",
            details={"reason": "User query requires log/save confirmation"}
        )
        return Event(output=text, route="needs_approval")
    else:
        write_audit_log(
            severity="INFO",
            action="auto_approved",
            details={"reason": "Normal query, no confirmation required"}
        )
        return Event(output=text, route="auto_approved")

@node(rerun_on_resume=True)
async def hitl_approval_node(ctx: Context, node_input: str):
    """Human-in-the-Loop node: prompts user and persists record upon confirmation."""
    if not ctx.resume_inputs or "log_confirm" not in ctx.resume_inputs:
        write_audit_log(
            severity="INFO",
            action="hitl_waiting",
            details={"interrupt_id": "log_confirm"}
        )
        yield RequestInput(
            interrupt_id="log_confirm",
            message="Do you want to log this carbon footprint calculation to your profile? (yes/no)"
        )
        return

    user_reply = ctx.resume_inputs["log_confirm"]
    if user_reply.strip().lower() in ("yes", "y"):
        user_query = ctx.state.get("user_query", "Carbon activity")
        
        # Parse calculated CO2e from response text
        co2e_kg = 0.0
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg\s*co2e?|kilograms?\s*(?:of\s*)?co2e?)", node_input, re.IGNORECASE)
        if match:
            co2e_kg = float(match.group(1))
        else:
            co2e_kg = 2.5
            
        # Parse potential savings
        saved_kg = 0.0
        save_match = re.search(r"(?:save|reduce|cut|offset)s?\s*(?:by\s*)?(\d+(?:\.\d+)?)\s*(?:kg\s*co2e?|kg)", node_input, re.IGNORECASE)
        if save_match:
            saved_kg = float(save_match.group(1))

        # Classify category
        category = "general"
        query_lower = user_query.lower()
        if any(w in query_lower for w in ["drive", "car", "km", "miles", "flight", "bus", "train", "commute", "travel", "plane"]):
            category = "transportation"
        elif any(w in query_lower for w in ["beef", "chicken", "diet", "food", "meat", "meal", "milk", "lamb", "pork", "rice"]):
            category = "diet"
        elif any(w in query_lower for w in ["fridge", "ac", "appliance", "washer", "dryer", "heater", "electricity", "bulb"]):
            category = "energy"
        elif any(w in query_lower for w in ["recycle", "bottle", "plastic", "waste", "compost", "cardboard", "aluminum", "can"]):
            category = "waste"

        # Persist to SQLite
        record = db.log_calculation(
            category=category,
            activity_details=user_query,
            co2e_kg=co2e_kg,
            saved_co2e_kg=saved_kg,
            notes="Logged via HITL approval from session"
        )
        
        badge_notice = ""
        if record.get("new_badges"):
            badge_notice = f" 🏅 *New Milestone Unlocked: {', '.join(record['new_badges'])}!*"
            
        log_status = f"Successfully logged to profile database (Log ID #{record['id']}).{badge_notice}"
    else:
        log_status = "Footprint calculation not logged"

    write_audit_log(
        severity="INFO",
        action="hitl_response_received",
        details={"user_reply": user_reply, "log_status": log_status}
    )
    yield Event(output=node_input, state={"log_status": log_status})

@node
async def final_output_node(ctx: Context, node_input: str):
    """Formats final response and displays log status."""
    log_status = ctx.state.get("log_status", "No log requested")
    final_text = f"{node_input}\n\n*Log Status: {log_status}*"
    
    content = types.Content(role='model', parts=[types.Part.from_text(text=final_text)])
    yield Event(content=content)
    yield Event(output=content)

# Build the Workflow Graph
root_agent = Workflow(
    name="ecotracker_workflow",
    edges=[
        (START, security_checkpoint),
        Edge(from_node=security_checkpoint, to_node=orchestrator_agent, route=DEFAULT_ROUTE),
        Edge(from_node=security_checkpoint, to_node=security_event_node, route="security_event"),
        (orchestrator_agent, post_process_node),
        Edge(from_node=post_process_node, to_node=hitl_approval_node, route="needs_approval"),
        Edge(from_node=post_process_node, to_node=final_output_node, route=DEFAULT_ROUTE),
        (hitl_approval_node, final_output_node)
    ]
)

# App configuration
app = App(
    root_agent=root_agent,
    name="app",
)
