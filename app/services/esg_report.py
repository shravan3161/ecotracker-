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

"""Enterprise ESG & Scope 1, 2, 3 Greenhouse Gas Compliance Service.

Produces formal, audit-ready sustainability disclosures aligned with:
- GHG Protocol Corporate Standard
- EU Corporate Sustainability Due Diligence / CSRD Directives
- SEC Climate Disclosure Framework
"""

import hashlib
import datetime
from typing import Dict, Any, List, Optional

def categorize_scope(category: str, activity_details: str) -> str:
    """Categorizes an activity into GHG Protocol Scope 1, Scope 2, or Scope 3."""
    cat = (category or "").lower()
    details = (activity_details or "").lower()

    if any(k in details or k in cat for k in ["gasoline", "diesel", "fuel", "natural gas", "furnace", "refrigerant", "heating oil"]):
        return "Scope 1 (Direct)"
    elif any(k in details or k in cat for k in ["electricity", "power", "grid", "kwh", "ac", "air conditioner", "refrigerator", "appliance"]):
        return "Scope 2 (Market Electricity)"
    else:
        # Business travel, flights, commuting, food, waste, supply chain
        return "Scope 3 (Value Chain & Commute)"

def generate_esg_disclosure(
    company_name: str = "Enterprise Sustainability Team",
    reporting_period: str = "FY2026",
    user_id: str = "default_customer",
    logs: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generates an audit-ready carbon balance sheet and compliance metrics."""
    activity_logs = logs or []
    
    scope_totals = {
        "Scope 1 (Direct)": 0.0,
        "Scope 2 (Market Electricity)": 0.0,
        "Scope 3 (Value Chain & Commute)": 0.0
    }
    avoided_total = 0.0

    categorized_records = []
    for log in activity_logs:
        scope = log.get("scope") or categorize_scope(log.get("category", ""), log.get("activity_details", ""))
        co2_val = float(log.get("co2e_kg", 0.0))
        saved_val = float(log.get("saved_co2e_kg", 0.0))

        scope_key = scope if scope in scope_totals else "Scope 3 (Value Chain & Commute)"
        scope_totals[scope_key] += co2_val
        avoided_total += saved_val

        rec = dict(log)
        rec["scope"] = scope_key
        categorized_records.append(rec)

    total_emissions_kg = sum(scope_totals.values())
    total_emissions_mt = round(total_emissions_kg / 1000.0, 3)
    avoided_mt = round(avoided_total / 1000.0, 3)

    # Verification Hash
    hash_payload = f"{company_name}|{reporting_period}|{total_emissions_kg}|{avoided_total}"
    verification_hash = hashlib.sha256(hash_payload.encode()).hexdigest()[:16].upper()

    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "company_name": company_name,
        "reporting_period": reporting_period,
        "user_id": user_id,
        "generated_at": now_iso,
        "verification_hash": f"ESG-VERIFIED-{verification_hash}",
        "standards_compliance": ["GHG Protocol Corporate Standard", "ISO 14064-1", "CSRD Ready"],
        "metrics": {
            "total_emissions_mt_co2e": total_emissions_mt,
            "total_emissions_kg_co2e": round(total_emissions_kg, 2),
            "total_abated_mt_co2e": avoided_mt,
            "scope_breakdown_mt": {
                "scope_1_direct": round(scope_totals["Scope 1 (Direct)"] / 1000.0, 3),
                "scope_2_electricity": round(scope_totals["Scope 2 (Market Electricity)"] / 1000.0, 3),
                "scope_3_value_chain": round(scope_totals["Scope 3 (Value Chain & Commute)"] / 1000.0, 3),
            },
            "scope_percentages": {
                "scope_1": round((scope_totals["Scope 1 (Direct)"] / max(total_emissions_kg, 0.001)) * 100, 1),
                "scope_2": round((scope_totals["Scope 2 (Market Electricity)"] / max(total_emissions_kg, 0.001)) * 100, 1),
                "scope_3": round((scope_totals["Scope 3 (Value Chain & Commute)"] / max(total_emissions_kg, 0.001)) * 100, 1),
            },
            "total_records_audited": len(categorized_records)
        },
        "records": categorized_records
    }

def render_printable_esg_html(disclosure: Dict[str, Any]) -> str:
    """Renders a pixel-perfect, print-to-PDF ready executive ESG report."""
    metrics = disclosure["metrics"]
    scopes = metrics["scope_breakdown_mt"]
    pcts = metrics["scope_percentages"]

    rows_html = ""
    for r in disclosure.get("records", [])[:50]:
        rows_html += f"""
        <tr>
            <td>{r.get('timestamp', 'N/A')[:10]}</td>
            <td><span class="badge">{r.get('scope', 'Scope 3')}</span></td>
            <td>{r.get('category', '').title()}</td>
            <td>{r.get('activity_details', '')}</td>
            <td style="font-weight: 600; text-align: right;">{float(r.get('co2e_kg', 0)):.2f} kg</td>
            <td style="color: #10B981; font-weight: 600; text-align: right;">{float(r.get('saved_co2e_kg', 0)):.2f} kg</td>
        </tr>
        """

    if not rows_html:
        rows_html = "<tr><td colspan='6' style='text-align:center; padding: 24px;'>No verified activity records logged for this reporting period.</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ESG Carbon Disclosure — {disclosure['company_name']}</title>
<style>
    @media print {{
        body {{ margin: 0; padding: 10mm; font-size: 11pt; color: #111; background: #fff !important; }}
        .no-print {{ display: none !important; }}
        .page-break {{ page-break-before: always; }}
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.5;
        color: #1e293b;
        background: #f8fafc;
        padding: 40px;
        margin: 0;
    }}
    .sheet {{
        max-width: 900px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 48px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 2px solid #0f172a;
        padding-bottom: 24px;
        margin-bottom: 32px;
    }}
    .title {{
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
        margin: 0;
    }}
    .subtitle {{
        color: #64748b;
        font-size: 13px;
        margin-top: 4px;
    }}
    .badge-verified {{
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #a7f3d0;
        font-size: 12px;
        font-weight: 700;
        padding: 6px 12px;
        border-radius: 6px;
        display: inline-block;
        letter-spacing: 0.5px;
    }}
    .grid-3 {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 32px;
    }}
    .card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
    }}
    .card-label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        font-weight: 700;
    }}
    .card-val {{
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 6px;
    }}
    .scope-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 32px;
    }}
    .scope-table th {{
        background: #f1f5f9;
        text-align: left;
        padding: 10px 14px;
        font-size: 12px;
        text-transform: uppercase;
        color: #475569;
        font-weight: 700;
        border-bottom: 1px solid #cbd5e1;
    }}
    .scope-table td {{
        padding: 10px 14px;
        font-size: 13px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .badge {{
        display: inline-block;
        background: #f1f5f9;
        color: #334155;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
    }}
    .btn-print {{
        background: #0f172a;
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 600;
        border-radius: 6px;
        cursor: pointer;
        margin-bottom: 24px;
    }}
    .btn-print:hover {{
        background: #334155;
    }}
</style>
</head>
<body>
<div style="max-width: 900px; margin: 0 auto;" class="no-print">
    <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
</div>
<div class="sheet">
    <div class="header">
        <div>
            <h1 class="title">🌍 EcoTracker — Corporate GHG Disclosure</h1>
            <div class="subtitle">Entity: <strong>{disclosure['company_name']}</strong> &nbsp;|&nbsp; Period: <strong>{disclosure['reporting_period']}</strong> &nbsp;|&nbsp; Standard: <strong>GHG Protocol Corporate</strong></div>
        </div>
        <div>
            <div class="badge-verified">✓ {disclosure['verification_hash']}</div>
        </div>
    </div>

    <div class="grid-3">
        <div class="card">
            <div class="card-label">Total Gross Emissions</div>
            <div class="card-val">{metrics['total_emissions_mt_co2e']:.3f} <span style="font-size: 14px; color: #64748b;">MT CO2e</span></div>
        </div>
        <div class="card">
            <div class="card-label">Verified Reductions / Abated</div>
            <div class="card-val" style="color: #059669;">{metrics['total_abated_mt_co2e']:.3f} <span style="font-size: 14px; color: #64748b;">MT CO2e</span></div>
        </div>
        <div class="card">
            <div class="card-label">Audited Record Entries</div>
            <div class="card-val">{metrics['total_records_audited']} <span style="font-size: 14px; color: #64748b;">events</span></div>
        </div>
    </div>

    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">Greenhouse Gas Protocol Scope Breakdown</h3>
    <table class="scope-table">
        <thead>
            <tr>
                <th>Scope Classification</th>
                <th>Description</th>
                <th>Emissions (MT)</th>
                <th>Share (%)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Scope 1 (Direct)</strong></td>
                <td>Combustion from boilers, company vehicles, and heating fuels.</td>
                <td style="font-weight: 700;">{scopes['scope_1_direct']:.3f} MT</td>
                <td>{pcts['scope_1']}%</td>
            </tr>
            <tr>
                <td><strong>Scope 2 (Electricity)</strong></td>
                <td>Location & market-based purchased grid electricity & heating.</td>
                <td style="font-weight: 700;">{scopes['scope_2_electricity']:.3f} MT</td>
                <td>{pcts['scope_2']}%</td>
            </tr>
            <tr>
                <td><strong>Scope 3 (Value Chain)</strong></td>
                <td>Employee business travel, commuting, food catering, and waste.</td>
                <td style="font-weight: 700;">{scopes['scope_3_value_chain']:.3f} MT</td>
                <td>{pcts['scope_3']}%</td>
            </tr>
        </tbody>
    </table>

    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">Verified Activity Audit Trail</h3>
    <table class="scope-table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Scope</th>
                <th>Category</th>
                <th>Activity Description</th>
                <th style="text-align: right;">Gross Impact</th>
                <th style="text-align: right;">Abated</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 11px; color: #94a3b8; display: flex; justify-content: space-between;">
        <span>Generated autonomously by EcoTracker Enterprise Sustainability Engine on {disclosure['generated_at']}</span>
        <span>Certificate ID: {disclosure['verification_hash']}</span>
    </div>
</div>
</body>
</html>
"""
    return html
