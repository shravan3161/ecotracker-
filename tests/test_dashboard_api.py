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

"""Integration tests for the EcoTracker Dashboard REST API."""

import os
import pytest
from starlette.testclient import TestClient
from app.dashboard import app
from app import db

TEST_USER = "test_customer_xyz"

@pytest.fixture(autouse=True)
def clean_user_data():
    db.init_db("ecotracker.db")
    db.clear_user_data(TEST_USER, db_path="ecotracker.db")
    yield
    db.clear_user_data(TEST_USER, db_path="ecotracker.db")

def test_dashboard_full_lifecycle():
    client = TestClient(app)

    # 1. Fetch initial summary
    res = client.get(f"/api/summary?user_id={TEST_USER}")
    assert res.status_code == 200
    data = res.json()
    assert data["total_entries"] == 0

    # 2. Log an entry via chat endpoint
    chat_payload = {
        "user_id": TEST_USER,
        "message": "I drove 40 km in a gasoline car, calculate carbon and log it to my profile"
    }
    chat_res = client.post("/api/chat", json=chat_payload)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "reply" in chat_data
    assert len(chat_data["reply"]) > 10

    # 3. Check updated summary
    summary_res = client.get(f"/api/summary?user_id={TEST_USER}")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_entries"] >= 1
    assert len(summary["recent_calculations"]) >= 1

    first_log_id = summary["recent_calculations"][0]["id"]

    # 4. Export CSV
    csv_res = client.get(f"/api/export-csv?user_id={TEST_USER}")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "Log ID,Timestamp,Category,Activity Details,Emissions (kg CO2e)" in csv_res.text

    # 5. Delete specific log entry
    del_res = client.delete(f"/api/log/{first_log_id}?user_id={TEST_USER}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "success"

    # Verify log is gone
    after_del_res = client.get(f"/api/summary?user_id={TEST_USER}")
    assert after_del_res.json()["total_entries"] == 0

    # 6. Insert another log and test clear all
    db.log_calculation(
        category="diet",
        activity_details="Plant burger lunch",
        co2e_kg=1.2,
        saved_co2e_kg=2.5,
        user_id=TEST_USER,
        db_path="ecotracker.db"
    )
    assert client.get(f"/api/summary?user_id={TEST_USER}").json()["total_entries"] == 1

    reset_res = client.delete(f"/api/logs/all?user_id={TEST_USER}")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"

    # Verify all records cleared
    final_summary = client.get(f"/api/summary?user_id={TEST_USER}").json()
    assert final_summary["total_entries"] == 0
