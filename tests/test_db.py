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

"""Unit tests for the EcoTracker SQLite Persistence Layer."""

import os
import pytest
from app import db

TEST_DB = "test_ecotracker.db"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    db.init_db(TEST_DB)
    db.clear_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_log_calculation_and_summary():
    rec1 = db.log_calculation(
        category="transportation",
        activity_details="50 km gasoline car drive",
        co2e_kg=9.6,
        saved_co2e_kg=7.55,
        notes="Swapped for train",
        db_path=TEST_DB
    )
    assert rec1["id"] == 1
    assert "First Step" in rec1["new_badges"]

    summary = db.get_user_summary(TEST_DB)
    assert summary["total_entries"] == 1
    assert summary["total_emissions_kg"] == 9.6
    assert summary["total_saved_kg"] == 7.55
    assert len(summary["by_category"]) == 1
    assert summary["by_category"][0]["category"] == "transportation"
    assert len(summary["badges"]) >= 1

def test_milestone_badges():
    # Log 5 calculations with cumulative savings > 10 kg to trigger badges
    for i in range(5):
        db.log_calculation(
            category="diet",
            activity_details=f"Plant-based meal #{i+1}",
            co2e_kg=1.5,
            saved_co2e_kg=3.0,
            db_path=TEST_DB
        )

    summary = db.get_user_summary(TEST_DB)
    assert summary["total_entries"] == 5
    assert summary["total_saved_kg"] == 15.0

    badge_names = [b["name"] for b in summary["badges"]]
    assert "First Step" in badge_names
    assert "Eco Habit" in badge_names
    assert "Carbon Saver" in badge_names

def test_delete_log_and_clear_user_data():
    # Insert 2 logs for user_a and 1 for user_b
    rec1 = db.log_calculation(
        category="transportation",
        activity_details="Commute A1",
        co2e_kg=5.0,
        saved_co2e_kg=2.0,
        user_id="user_a",
        db_path=TEST_DB
    )
    rec2 = db.log_calculation(
        category="diet",
        activity_details="Meal A2",
        co2e_kg=2.0,
        saved_co2e_kg=1.0,
        user_id="user_a",
        db_path=TEST_DB
    )
    rec3 = db.log_calculation(
        category="energy",
        activity_details="Power B1",
        co2e_kg=10.0,
        saved_co2e_kg=0.0,
        user_id="user_b",
        db_path=TEST_DB
    )

    summary_a = db.get_user_summary(user_id="user_a", db_path=TEST_DB)
    assert summary_a["total_entries"] == 2

    # Delete rec1 for user_a
    deleted = db.delete_log(log_id=rec1["id"], user_id="user_a", db_path=TEST_DB)
    assert deleted is True

    # Attempting to delete someone else's log should return False
    cross_delete = db.delete_log(log_id=rec3["id"], user_id="user_a", db_path=TEST_DB)
    assert cross_delete is False

    summary_a_after = db.get_user_summary(user_id="user_a", db_path=TEST_DB)
    assert summary_a_after["total_entries"] == 1
    assert summary_a_after["recent_calculations"][0]["id"] == rec2["id"]

    # Clear all user_a data
    cleared = db.clear_user_data(user_id="user_a", db_path=TEST_DB)
    assert cleared is True

    summary_a_empty = db.get_user_summary(user_id="user_a", db_path=TEST_DB)
    assert summary_a_empty["total_entries"] == 0

    # User B data remains intact
    summary_b = db.get_user_summary(user_id="user_b", db_path=TEST_DB)
    assert summary_b["total_entries"] == 1

