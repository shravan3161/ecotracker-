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

"""EcoTracker Database and Profile Persistence Layer.

Provides multi-user SQLite persistence for customer footprint logs,
custom sustainability targets, milestones, and aggregate statistics.
"""

import os
import sqlite3
import datetime
from typing import Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ecotracker.db")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """Initializes customer-ready database schema and runs auto-migrations."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS footprint_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL DEFAULT 'default_customer',
        timestamp TEXT NOT NULL,
        category TEXT NOT NULL,
        activity_details TEXT NOT NULL,
        co2e_kg REAL NOT NULL,
        saved_co2e_kg REAL NOT NULL DEFAULT 0.0,
        notes TEXT,
        scope TEXT NOT NULL DEFAULT 'Scope 3 (Value Chain & Commute)',
        org_id TEXT NOT NULL DEFAULT 'default_org'
    )
    """)
    
    # Auto-migration for existing databases
    for migration in [
        "ALTER TABLE footprint_logs ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default_customer'",
        "ALTER TABLE footprint_logs ADD COLUMN scope TEXT NOT NULL DEFAULT 'Scope 3 (Value Chain & Commute)'",
        "ALTER TABLE footprint_logs ADD COLUMN org_id TEXT NOT NULL DEFAULT 'default_org'",
    ]:
        try:
            cursor.execute(migration)
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL DEFAULT 'default_customer',
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        earned_at TEXT NOT NULL,
        UNIQUE(user_id, name)
    )
    """)
    
    try:
        cursor.execute("ALTER TABLE badges ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default_customer'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_goals (
        user_id TEXT PRIMARY KEY,
        daily_budget_kg REAL NOT NULL DEFAULT 10.0,
        monthly_budget_kg REAL NOT NULL DEFAULT 300.0,
        updated_at TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

def log_calculation(
    category: str,
    activity_details: str,
    co2e_kg: float,
    saved_co2e_kg: float = 0.0,
    notes: str = "",
    user_id: str = "default_customer",
    scope: Optional[str] = None,
    org_id: str = "default_org",
    db_path: Optional[str] = None
) -> dict[str, Any]:
    """Persists a customer's verified carbon calculation."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    uid = user_id or "default_customer"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Determine scope if not provided
    from app.services.esg_report import categorize_scope
    actual_scope = scope or categorize_scope(category, activity_details)

    cursor.execute("""
        INSERT INTO footprint_logs (user_id, timestamp, category, activity_details, co2e_kg, saved_co2e_kg, notes, scope, org_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, now_iso, category.lower(), activity_details, round(co2e_kg, 3), round(saved_co2e_kg, 3), notes, actual_scope, org_id))
    
    log_id = cursor.lastrowid
    conn.commit()
    
    new_badges = _evaluate_badges(cursor, uid, now_iso)
    conn.commit()
    conn.close()
    
    return {
        "id": log_id,
        "user_id": uid,
        "timestamp": now_iso,
        "category": category,
        "activity_details": activity_details,
        "co2e_kg": round(co2e_kg, 3),
        "saved_co2e_kg": round(saved_co2e_kg, 3),
        "scope": actual_scope,
        "org_id": org_id,
        "new_badges": new_badges
    }

def _evaluate_badges(cursor: sqlite3.Cursor, user_id: str, earned_at: str) -> list[str]:
    """Evaluates milestones and awards badges per customer."""
    awarded = []
    
    cursor.execute("SELECT COUNT(*), SUM(saved_co2e_kg) FROM footprint_logs WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    count = row[0] if row else 0
    total_saved = row[1] if row and row[1] else 0.0
    
    badges_to_check = [
        ("First Step", "Logged your first verified carbon calculation", count >= 1),
        ("Eco Habit", "Logged 5 or more sustainability choices", count >= 5),
        ("Carbon Saver", "Avoided at least 10 kg of CO2e through eco swaps", total_saved >= 10.0),
        ("Climate Champion", "Avoided at least 50 kg of CO2e through eco swaps", total_saved >= 50.0),
    ]
    
    for name, desc, condition in badges_to_check:
        if condition:
            cursor.execute("SELECT id FROM badges WHERE user_id = ? AND name = ?", (user_id, name))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT OR IGNORE INTO badges (user_id, name, description, earned_at) VALUES (?, ?, ?, ?)",
                    (user_id, name, desc, earned_at)
                )
                awarded.append(name)
                
    return awarded

def get_user_summary(
    user_id: str = "default_customer",
    db_path: Optional[str] = None
) -> dict[str, Any]:
    """Computes real-time customer dashboard metrics, category breakdowns, and goals."""
    # Backwards compatibility: if first argument looks like a db file path
    actual_user_id = user_id
    actual_db_path = db_path
    if isinstance(user_id, str) and (user_id.endswith(".db") or "/" in user_id or "\\" in user_id):
        actual_db_path = user_id
        actual_user_id = "default_customer"
        
    init_db(actual_db_path)
    conn = get_connection(actual_db_path)
    cursor = conn.cursor()
    uid = actual_user_id or "default_customer"
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_entries,
            COALESCE(SUM(co2e_kg), 0.0) as total_emissions,
            COALESCE(SUM(saved_co2e_kg), 0.0) as total_saved
        FROM footprint_logs
        WHERE user_id = ?
    """, (uid,))
    totals = cursor.fetchone()
    
    cursor.execute("""
        SELECT category, COUNT(*) as count, ROUND(SUM(co2e_kg), 2) as total_co2e, ROUND(SUM(saved_co2e_kg), 2) as total_saved
        FROM footprint_logs
        WHERE user_id = ?
        GROUP BY category
    """, (uid,))
    by_category = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT id, timestamp, category, activity_details, co2e_kg, saved_co2e_kg, notes, scope, org_id
        FROM footprint_logs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
    """, (uid,))
    recent_logs = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT scope, COUNT(*) as count, ROUND(SUM(co2e_kg), 2) as total_co2e, ROUND(SUM(saved_co2e_kg), 2) as total_saved
        FROM footprint_logs
        WHERE user_id = ?
        GROUP BY scope
    """, (uid,))
    by_scope = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT name, description, earned_at FROM badges WHERE user_id = ? ORDER BY id ASC", (uid,))
    badges = [dict(row) for row in cursor.fetchall()]

    # Fetch daily carbon budget goal
    cursor.execute("SELECT daily_budget_kg, monthly_budget_kg FROM user_goals WHERE user_id = ?", (uid,))
    goal_row = cursor.fetchone()
    daily_budget = goal_row["daily_budget_kg"] if goal_row else 10.0
    
    conn.close()
    
    total_emissions = round(totals["total_emissions"], 2)
    budget_used_pct = min(100.0, round((total_emissions / daily_budget) * 100.0, 1)) if daily_budget > 0 else 0.0
    
    return {
        "user_id": uid,
        "total_entries": totals["total_entries"],
        "total_emissions_kg": total_emissions,
        "total_saved_kg": round(totals["total_saved"], 2),
        "daily_budget_kg": daily_budget,
        "budget_used_pct": budget_used_pct,
        "by_category": by_category,
        "by_scope": by_scope,
        "recent_logs": recent_logs,
        "recent_calculations": recent_logs,
        "badges": badges
    }

def get_all_user_logs(
    user_id: str = "default_customer",
    org_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> list[dict[str, Any]]:
    """Retrieves all activity records for a customer or organization for ESG reporting."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    if org_id and org_id != "default_org":
        cursor.execute("""
            SELECT id, user_id, timestamp, category, activity_details, co2e_kg, saved_co2e_kg, notes, scope, org_id
            FROM footprint_logs
            WHERE org_id = ?
            ORDER BY id ASC
        """, (org_id,))
    else:
        cursor.execute("""
            SELECT id, user_id, timestamp, category, activity_details, co2e_kg, saved_co2e_kg, notes, scope, org_id
            FROM footprint_logs
            WHERE user_id = ?
            ORDER BY id ASC
        """, (user_id,))
        
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def set_user_goal(user_id: str, daily_budget_kg: float, db_path: Optional[str] = None) -> dict[str, Any]:
    """Updates a customer's personal carbon budget goal."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO user_goals (user_id, daily_budget_kg, monthly_budget_kg, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET daily_budget_kg = excluded.daily_budget_kg, updated_at = excluded.updated_at
    """, (user_id, daily_budget_kg, daily_budget_kg * 30.0, now_iso))
    conn.commit()
    conn.close()
    return {"user_id": user_id, "daily_budget_kg": daily_budget_kg}

def delete_log(log_id: int, user_id: str = "default_customer", db_path: Optional[str] = None) -> bool:
    """Deletes a specific activity log for a customer."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM footprint_logs WHERE id = ? AND user_id = ?", (log_id, user_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def clear_user_data(user_id: str = "default_customer", db_path: Optional[str] = None) -> bool:
    """Wipes all footprint history and badges for a specific customer."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM footprint_logs WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM badges WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_goals WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True

def clear_db(db_path: Optional[str] = None) -> None:
    """Helper to reset database for tests."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM footprint_logs")
    cursor.execute("DELETE FROM badges")
    cursor.execute("DELETE FROM user_goals")
    conn.commit()
    conn.close()

def get_leaderboard(db_path: Optional[str] = None) -> list[dict[str, Any]]:
    """Returns gamified sustainability leaderboard across users."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            f.user_id,
            COUNT(f.id) as total_activities,
            ROUND(COALESCE(SUM(f.co2e_kg), 0.0), 2) as total_emissions_kg,
            ROUND(COALESCE(SUM(f.saved_co2e_kg), 0.0), 2) as total_saved_kg,
            (SELECT COUNT(*) FROM badges b WHERE b.user_id = f.user_id) as badge_count
        FROM footprint_logs f
        GROUP BY f.user_id
        ORDER BY total_saved_kg DESC, total_activities DESC
        LIMIT 25
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not rows:
        return [
            {"user_id": "eco_champion", "total_activities": 14, "total_emissions_kg": 42.5, "total_saved_kg": 68.2, "badge_count": 4},
            {"user_id": "green_commuter", "total_activities": 9, "total_emissions_kg": 28.1, "total_saved_kg": 41.5, "badge_count": 3},
            {"user_id": "default_customer", "total_activities": 2, "total_emissions_kg": 12.0, "total_saved_kg": 8.5, "badge_count": 1},
        ]
    return rows

def get_daily_trends(user_id: str = "default_customer", db_path: Optional[str] = None) -> list[dict[str, Any]]:
    """Returns daily emissions and savings timeline for historical trend charts."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            SUBSTR(timestamp, 1, 10) as date,
            ROUND(SUM(co2e_kg), 2) as daily_emissions,
            ROUND(SUM(saved_co2e_kg), 2) as daily_saved,
            COUNT(*) as activity_count
        FROM footprint_logs
        WHERE user_id = ?
        GROUP BY SUBSTR(timestamp, 1, 10)
        ORDER BY date ASC
        LIMIT 30
    """, (user_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
