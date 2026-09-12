from typing import List, Dict, Any
from backend.models import DerivedIndicators, RiskReport, Recommendation

RECOMMENDATION_DISCLAIMER = "Recommendations are decision-support suggestions for administrative review and do not assert conclusive causal determination of project delays."

def generate_recommendations(project: Dict[str, Any], indicators: DerivedIndicators, risk_report: RiskReport) -> List[Recommendation]:
    recs = []
    phys_prog = float(project.get("physical_progress", 0.0))

    # 1. Schedule Risk Driver Recommendation
    if risk_report.schedule_risk >= 60.0 or indicators.schedule_pressure >= 1.4:
        recs.append(Recommendation(
            rule_id="REC-SCHED-01",
            category="Schedule & Milestones",
            title="Prioritize Milestone & Critical-Path Review",
            action="Convene a joint coordination meeting between the Ministry project monitoring unit and executing contractors to re-baseline critical path milestones, assess work-front availability, and expedite pending right-of-way (RoW) clearances.",
            priority="High"
        ))

    # 2. Cost Escalation Driver Recommendation
    if risk_report.cost_risk >= 60.0 or indicators.cost_variance_pct >= 15.0:
        recs.append(Recommendation(
            rule_id="REC-COST-01",
            category="Financial & Cost Control",
            title="Review Current/Revised Cost and Major Cost Drivers",
            action="Conduct a detailed breakdown review of cost escalation components (land acquisition escalation, foreign exchange fluctuations, commodity price indexation, and engineering scope changes) through the Standing Finance Committee (SFC) / RCE mechanism.",
            priority="High"
        ))

    # 3. Progress Gap Driver Recommendation
    if indicators.progress_gap >= 15.0 or risk_report.financial_risk >= 60.0:
        recs.append(Recommendation(
            rule_id="REC-FIN-01",
            category="Expenditure Alignment",
            title="Review Alignment Between Expenditure and Reported Physical Progress",
            action="Perform physical milestone verification and reconciliation of contractor advance mobilization payments against verified on-ground construction logs before sanctioning additional quarterly financial allocations.",
            priority="High" if indicators.progress_gap >= 25.0 else "Medium"
        ))

    # 4. Low Physical Progress Driver Recommendation
    if phys_prog < 30.0 and indicators.time_elapsed_ratio > 0.4:
        recs.append(Recommendation(
            rule_id="REC-PROG-01",
            category="Ground Implementation",
            title="Review Milestone Status and Implementation Constraints",
            action="Depute an inter-departmental task force to inspect site constraints, assess contractor equipment mobilization levels, and address local administrative bottlenecks with the State administration.",
            priority="High"
        ))

    # 5. Routine Baseline Monitoring (for Low / Stable projects)
    if not recs:
        recs.append(Recommendation(
            rule_id="REC-BASE-01",
            category="Routine Governance",
            title="Maintain Standard Monthly Milestone Verification",
            action="Continue regular monthly progress reporting via the centralized portal, ensuring timely upload of contractor measurement certificates and physical site geotagged photos.",
            priority="Low"
        ))

    return recs
