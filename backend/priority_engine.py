import math
from typing import List, Dict, Any

PRIORITY_DISCLAIMER = "Priority score is calculated using an analytical prototype formula combining composite risk, warning severity density, and capital exposure. This is a prototype decision-support mechanism, not an official government prioritization standard."

def compute_priority_score(project: Dict[str, Any], risk_report_dict: Dict[str, Any], warnings_count: int, critical_warnings_count: int) -> float:
    """
    Combines:
    - Overall Risk Score (50% weight)
    - Warning Severity Impact (30% weight)
    - Capital Exposure / Size Scale (20% weight, log-scaled)
    """
    overall_risk = float(risk_report_dict.get("overall_risk_score", 0.0))
    
    # Warnings penalty
    warning_score = min((critical_warnings_count * 30.0 + warnings_count * 10.0), 100.0)
    
    # Capital exposure factor: log10 scale
    rev_cost = max(float(project.get("revised_cost", 100.0)), 10.0)
    # E.g. ₹500 Cr -> log10 is 2.7; ₹50,000 Cr -> log10 is 4.7
    cost_factor = min(max((math.log10(rev_cost) - 1.0) / 3.7 * 100.0, 0.0), 100.0)

    priority_score = (0.50 * overall_risk) + (0.30 * warning_score) + (0.20 * cost_factor)
    return round(min(max(priority_score, 0.0), 100.0), 1)

def rank_projects(project_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks projects by priority_score descending and assigns priority_rank (1, 2, 3...)
    """
    sorted_projects = sorted(project_items, key=lambda x: x.get("priority_score", 0.0), reverse=True)
    for idx, item in enumerate(sorted_projects, start=1):
        item["priority_rank"] = idx
    return sorted_projects
