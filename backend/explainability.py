from typing import List, Dict, Any
from backend.models import DerivedIndicators, RiskReport

def generate_detailed_explanation(project: Dict[str, Any], indicators: DerivedIndicators, risk_report: RiskReport) -> str:
    """
    Generates human-readable, non-technical explanation for government officers.
    Example: 'High schedule risk is associated with low physical progress and significant schedule pressure.'
    """
    cat = risk_report.risk_category
    score = risk_report.overall_risk_score
    p_name = project.get("project_name", "Project")

    if cat == "Low":
        return (
            f"{p_name} is currently assessed at Low Risk ({score}/100). "
            f"Physical execution ({project.get('physical_progress')}%) remains aligned with timeline elapsed "
            f"and budget expenditure is within sanctioned limits."
        )

    statements = []
    # Check primary drivers
    if indicators.schedule_pressure >= 1.5:
        statements.append(f"significant schedule compression pressure ({indicators.schedule_pressure}x normal velocity needed)")
    
    if indicators.schedule_variance_months > 6:
        statements.append(f"a projected deadline slippage of {indicators.schedule_variance_months:.1f} months")

    if indicators.cost_variance_pct > 15:
        statements.append(f"cost escalation of {indicators.cost_variance_pct:.1f}% over initial approval")

    if indicators.progress_gap > 15:
        statements.append(f"an expenditure-progress gap where financial outlays exceed physical milestones by {indicators.progress_gap:.1f}%")

    if indicators.time_elapsed_ratio > 0.6 and float(project.get("physical_progress", 0)) < 35:
        statements.append(f"lagging physical progress ({project.get('physical_progress')}%) despite {indicators.time_elapsed_ratio*100:.0f}% of planned duration consumed")

    if not statements:
        statements.append("cumulative minor variances across multi-dimensional project tracking indicators")

    joined_reasons = "; ".join(statements)
    return (
        f"{cat} Risk ({score}/100): Associated with {joined_reasons}. "
        f"Targeted administrative intervention and review of implementation constraints is advised."
    )
