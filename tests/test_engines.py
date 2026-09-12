import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import init_db, get_all_projects, clear_all_projects, save_project
from backend.feature_engineering import compute_derived_indicators
from backend.risk_engine import evaluate_project_risk
from backend.early_warning_engine import detect_early_warnings
from backend.anomaly_engine import detect_anomalies
from backend.recommendation_engine import generate_recommendations
from backend.priority_engine import compute_priority_score
from backend.ai_assistant import process_assistant_query
from backend.what_if_simulator import simulate_project_scenario
from backend.models import WhatIfRequest
from backend.data_service import seed_demo_data, get_all_analyzed_projects

def test_feature_engineering():
    sample_proj = {
        "project_id": "TEST-01",
        "project_name": "Test Highway",
        "ministry": "Ministry of Road Transport and Highways",
        "sector": "Roads & Highways",
        "state": "Maharashtra",
        "original_cost": 1000.0,
        "revised_cost": 1500.0,
        "expenditure": 1200.0,
        "start_date": "2022-01-01",
        "original_completion_date": "2025-01-01",
        "expected_completion_date": "2026-06-01",
        "physical_progress": 35.0,
        "financial_progress": 80.0
    }
    ind = compute_derived_indicators(sample_proj)
    assert ind.cost_variance_pct == 50.0
    assert ind.cost_overrun_amount == 500.0
    assert ind.expenditure_ratio == 0.8
    assert ind.progress_gap == 45.0
    assert ind.schedule_variance_months == 17.0
    assert ind.size_band == "Major (₹500 - ₹1,000 Cr)"

def test_risk_engine_and_categories():
    sample_crit_proj = {
        "project_id": "TEST-CRIT",
        "project_name": "Critical Rail Project",
        "ministry": "Ministry of Railways",
        "sector": "Railways",
        "state": "Bihar",
        "original_cost": 2000.0,
        "revised_cost": 3800.0,
        "expenditure": 3400.0,
        "start_date": "2019-01-01",
        "original_completion_date": "2023-12-31",
        "expected_completion_date": "2028-12-31",
        "physical_progress": 30.0,
        "financial_progress": 89.5
    }
    ind = compute_derived_indicators(sample_crit_proj)
    risk = evaluate_project_risk(sample_crit_proj, ind)
    assert 0 <= risk.overall_risk_score <= 100
    assert risk.risk_category in ["High", "Critical"]
    assert len(risk.top_factors) > 0
    assert len(risk.explanation) > 10

def test_early_warnings_and_anomalies():
    sample_proj = {
        "project_id": "TEST-ANOM",
        "project_name": "Stalled Hydro",
        "ministry": "Ministry of Power",
        "sector": "Power & Energy",
        "state": "Assam",
        "original_cost": 5000.0,
        "revised_cost": 12000.0,
        "expenditure": 6000.0,
        "start_date": "2018-01-01",
        "original_completion_date": "2022-12-31",
        "expected_completion_date": "2029-12-31",
        "physical_progress": 0.0,
        "financial_progress": 50.0
    }
    ind = compute_derived_indicators(sample_proj)
    risk = evaluate_project_risk(sample_proj, ind)
    warns = detect_early_warnings(sample_proj, ind, risk)
    anoms = detect_anomalies(sample_proj, ind)

    assert len(warns) > 0
    assert any(w.severity == "Critical" for w in warns)
    # Zero progress with spend should trigger anomaly
    assert len(anoms) > 0
    assert any("Zero Physical Progress" in a.anomaly_type for a in anoms)

def test_what_if_simulation():
    sample_proj = {
        "project_id": "TEST-WHATIF",
        "project_name": "Test Port",
        "ministry": "Ministry of Ports, Shipping and Waterways",
        "sector": "Ports & Shipping",
        "state": "Gujarat",
        "original_cost": 1000.0,
        "revised_cost": 1000.0,
        "expenditure": 400.0,
        "start_date": "2023-01-01",
        "original_completion_date": "2026-12-31",
        "expected_completion_date": "2026-12-31",
        "physical_progress": 40.0,
        "financial_progress": 40.0
    }
    sim_req = WhatIfRequest(
        project_id="TEST-WHATIF",
        simulated_physical_progress=85.0
    )
    sim_res = simulate_project_scenario(sample_proj, sim_req)
    assert sim_res.simulated_risk.overall_risk_score <= sim_res.original_risk.overall_risk_score
    assert sim_res.score_change <= 0.0

def test_ai_assistant_grounded_queries():
    seed_demo_data()
    projects = get_all_analyzed_projects()
    assert len(projects) >= 30

    res_crit = process_assistant_query("Show critical-risk projects", projects)
    assert "critical" in res_crit.answer.lower()
    assert len(res_crit.related_projects) > 0

    res_sec = process_assistant_query("Which sector has the highest average risk?", projects)
    assert "sector" in res_sec.answer.lower()

    res_att = process_assistant_query("Which projects require attention?", projects)
    assert "attention" in res_att.answer.lower()

if __name__ == "__main__":
    init_db()
    test_feature_engineering()
    print("[PASS] Feature engineering tests passed.")
    test_risk_engine_and_categories()
    print("[PASS] Risk engine tests passed.")
    test_early_warnings_and_anomalies()
    print("[PASS] Early warnings and anomaly detection tests passed.")
    test_what_if_simulation()
    print("[PASS] What-if simulation tests passed.")
    test_ai_assistant_grounded_queries()
    print("[PASS] AI assistant grounded queries tests passed.")
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")
