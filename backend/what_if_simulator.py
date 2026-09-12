from typing import Dict, Any, Optional
from backend.models import WhatIfRequest, WhatIfResponse, RiskReport
from backend.feature_engineering import compute_derived_indicators
from backend.risk_engine import evaluate_project_risk
from backend.early_warning_engine import detect_early_warnings

SCENARIO_DISCLAIMER = "Results represent a mathematical simulation under hypothetical parameters. Scenario outputs are decision-support estimates and do not guarantee future outcomes or assert causality."

def simulate_project_scenario(original_project: Dict[str, Any], sim_request: WhatIfRequest) -> WhatIfResponse:
    # 1. Base Project Analysis
    base_indicators = compute_derived_indicators(original_project)
    base_risk = evaluate_project_risk(original_project, base_indicators)
    base_warnings = detect_early_warnings(original_project, base_indicators, base_risk)
    base_warning_ids = {w.warning_type for w in base_warnings}

    # 2. Simulated Project State
    simulated_project = dict(original_project)
    if sim_request.simulated_physical_progress is not None:
        simulated_project["physical_progress"] = float(sim_request.simulated_physical_progress)
    if sim_request.simulated_revised_cost is not None:
        simulated_project["revised_cost"] = float(sim_request.simulated_revised_cost)
    if sim_request.simulated_expected_completion is not None:
        simulated_project["expected_completion_date"] = sim_request.simulated_expected_completion
    if sim_request.simulated_expenditure is not None:
        simulated_project["expenditure"] = float(sim_request.simulated_expenditure)

    # 3. Simulated Analysis
    sim_indicators = compute_derived_indicators(simulated_project)
    sim_risk = evaluate_project_risk(simulated_project, sim_indicators)
    sim_warnings = detect_early_warnings(simulated_project, sim_indicators, sim_risk)
    sim_warning_ids = {w.warning_type for w in sim_warnings}

    # Compare warnings
    warnings_added = list(sim_warning_ids - base_warning_ids)
    warnings_resolved = list(base_warning_ids - sim_warning_ids)
    score_change = round(sim_risk.overall_risk_score - base_risk.overall_risk_score, 1)

    derived_changes = {
        "cost_variance_pct_delta": round(sim_indicators.cost_variance_pct - base_indicators.cost_variance_pct, 2),
        "schedule_pressure_delta": round(sim_indicators.schedule_pressure - base_indicators.schedule_pressure, 2),
        "progress_gap_delta": round(sim_indicators.progress_gap - base_indicators.progress_gap, 2),
        "new_overall_risk": sim_risk.overall_risk_score,
        "old_overall_risk": base_risk.overall_risk_score,
        "new_category": sim_risk.risk_category,
        "old_category": base_risk.risk_category
    }

    return WhatIfResponse(
        project_id=original_project["project_id"],
        original_risk=base_risk,
        simulated_risk=sim_risk,
        score_change=score_change,
        derived_changes=derived_changes,
        warnings_added=warnings_added,
        warnings_resolved=warnings_resolved,
        scenario_notes=SCENARIO_DISCLAIMER
    )
