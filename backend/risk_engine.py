from typing import Dict, Any, Tuple
from backend.models import DerivedIndicators, RiskReport

def calculate_cost_risk(indicators: DerivedIndicators, project: Dict[str, Any]) -> Tuple[float, list]:
    factors = []
    score = 0.0
    cost_var = indicators.cost_variance_pct
    exp_ratio = indicators.expenditure_ratio
    phys_prog = float(project.get("physical_progress", 0.0))

    # Base cost variance risk
    if cost_var <= 0:
        score += 5.0
    elif cost_var < 10:
        score += 25.0
        factors.append(f"Mild budget revision (+{cost_var:.1f}%)")
    elif cost_var < 25:
        score += 55.0
        factors.append(f"Moderate cost escalation (+{cost_var:.1f}%)")
    elif cost_var < 50:
        score += 80.0
        factors.append(f"Severe cost overrun (+{cost_var:.1f}%)")
    else:
        score += 98.0
        factors.append(f"Extreme cost escalation exceeding +{cost_var:.1f}%")

    # Expenditure burn ahead of physical delivery
    if exp_ratio > 0.8 and phys_prog < 50.0:
        score = min(score + 15.0, 100.0)
        factors.append(f"High fund burn ({exp_ratio*100:.0f}%) with sub-50% physical completion")
    elif exp_ratio > 0.6 and phys_prog < 30.0:
        score = min(score + 10.0, 100.0)
        factors.append("Early expenditure outpacing on-ground milestone progress")

    return min(max(round(score, 1), 0.0), 100.0), factors

def calculate_schedule_risk(indicators: DerivedIndicators, project: Dict[str, Any]) -> Tuple[float, list]:
    factors = []
    score = 0.0
    sched_var = indicators.schedule_variance_months
    pressure = indicators.schedule_pressure
    time_elapsed = indicators.time_elapsed_ratio

    # Delay slippage risk
    if sched_var <= 0:
        score += 10.0
    elif sched_var <= 6:
        score += 35.0
        factors.append(f"Projected slippage of {sched_var:.1f} months")
    elif sched_var <= 18:
        score += 65.0
        factors.append(f"Significant schedule delay of {sched_var:.1f} months")
    elif sched_var <= 36:
        score += 85.0
        factors.append(f"Prolonged timeline slippage ({sched_var:.1f} months)")
    else:
        score += 98.0
        factors.append(f"Critical chronic delay ({sched_var:.1f} months past original target)")

    # Schedule pressure risk
    if pressure >= 2.0:
        score = min(score + 20.0, 100.0)
        factors.append(f"Severe schedule pressure ({pressure}x acceleration required)")
    elif pressure >= 1.4:
        score = min(score + 12.0, 100.0)
        factors.append(f"Elevated schedule compression ({pressure}x acceleration required)")
    
    # Overdue timeline check
    if time_elapsed > 1.0 and float(project.get("physical_progress", 0.0)) < 90.0:
        score = min(score + 15.0, 100.0)
        factors.append("Original planned project tenure exhausted without completion")

    return min(max(round(score, 1), 0.0), 100.0), factors

def calculate_progress_risk(indicators: DerivedIndicators, project: Dict[str, Any]) -> Tuple[float, list]:
    factors = []
    score = 0.0
    phys_prog = float(project.get("physical_progress", 0.0))
    time_elapsed = indicators.time_elapsed_ratio
    efficiency = indicators.progress_to_time_efficiency

    expected_progress = min(time_elapsed * 100.0, 100.0)
    gap = expected_progress - phys_prog

    if gap <= 0:
        score += 10.0
    elif gap < 15:
        score += 30.0
        factors.append(f"Minor progress lag ({gap:.1f}% behind expected trajectory)")
    elif gap < 35:
        score += 65.0
        factors.append(f"Substantial milestone lag ({gap:.1f}% behind trajectory)")
    else:
        score += 90.0
        factors.append(f"Severe milestone deficit ({gap:.1f}% behind schedule trajectory)")

    if efficiency < 0.4 and time_elapsed > 0.3:
        score = min(score + 15.0, 100.0)
        factors.append(f"Low progress-to-time efficiency ({efficiency})")

    return min(max(round(score, 1), 0.0), 100.0), factors

def calculate_financial_risk(indicators: DerivedIndicators, project: Dict[str, Any]) -> Tuple[float, list]:
    factors = []
    score = 0.0
    prog_gap = indicators.progress_gap  # Financial% - Physical%
    fin_prog = float(project.get("financial_progress", 0.0))
    phys_prog = float(project.get("physical_progress", 0.0))

    if prog_gap <= 5:
        score += 10.0
    elif prog_gap <= 15:
        score += 35.0
        factors.append(f"Financial progress leads physical progress by {prog_gap:.1f}%")
    elif prog_gap <= 30:
        score += 65.0
        factors.append(f"Significant progress-expenditure gap (+{prog_gap:.1f}%)")
    else:
        score += 92.0
        factors.append(f"Critical progress-expenditure distortion (+{prog_gap:.1f}%)")

    if fin_prog > 75.0 and phys_prog < 50.0:
        score = min(score + 15.0, 100.0)
        factors.append("Premature budget exhaustion risk (>75% funds spent vs <50% work done)")

    return min(max(round(score, 1), 0.0), 100.0), factors

def get_risk_category(score: float) -> str:
    """0-30: Low, 31-60: Medium, 61-80: High, 81-100: Critical"""
    if score <= 30.0:
        return "Low"
    elif score <= 60.0:
        return "Medium"
    elif score <= 80.0:
        return "High"
    else:
        return "Critical"

def evaluate_project_risk(project: Dict[str, Any], indicators: DerivedIndicators) -> RiskReport:
    cost_risk, cost_factors = calculate_cost_risk(indicators, project)
    schedule_risk, sched_factors = calculate_schedule_risk(indicators, project)
    progress_risk, prog_factors = calculate_progress_risk(indicators, project)
    financial_risk, fin_factors = calculate_financial_risk(indicators, project)

    # Configurable Prototype Weights
    # 25% Cost, 30% Schedule, 25% Progress, 20% Financial
    overall = (
        0.25 * cost_risk +
        0.30 * schedule_risk +
        0.25 * progress_risk +
        0.20 * financial_risk
    )
    overall_score = round(min(max(overall, 0.0), 100.0), 1)
    category = get_risk_category(overall_score)

    # Compile all contributing factors with weights
    all_factors = []
    for f in sched_factors:
        all_factors.append({"factor": f, "dimension": "Schedule", "weight": 0.30, "risk_level": schedule_risk})
    for f in cost_factors:
        all_factors.append({"factor": f, "dimension": "Cost", "weight": 0.25, "risk_level": cost_risk})
    for f in prog_factors:
        all_factors.append({"factor": f, "dimension": "Progress", "weight": 0.25, "risk_level": progress_risk})
    for f in fin_factors:
        all_factors.append({"factor": f, "dimension": "Financial", "weight": 0.20, "risk_level": financial_risk})

    # Sort factors by underlying dimension risk
    all_factors.sort(key=lambda x: x["risk_level"], reverse=True)
    top_factors = all_factors[:4]

    # Generate non-technical executive explanation
    if overall_score <= 30:
        explanation = "Project trajectory is within normal variance thresholds across cost, schedule, and milestone delivery parameters."
    else:
        top_driver_names = [f["factor"] for f in top_factors[:2]]
        if top_driver_names:
            explanation = f"{category} project risk is primarily associated with {', '.join(top_driver_names).lower()}."
        else:
            explanation = f"Project exhibits elevated {category.lower()} composite risk based on aggregate operational indicators."

    return RiskReport(
        cost_risk=cost_risk,
        schedule_risk=schedule_risk,
        progress_risk=progress_risk,
        financial_risk=financial_risk,
        overall_risk_score=overall_score,
        risk_category=category,
        top_factors=top_factors,
        explanation=explanation
    )
