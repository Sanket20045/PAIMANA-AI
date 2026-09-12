from typing import List, Dict, Any
from backend.models import DerivedIndicators, RiskReport, EarlyWarning

def detect_early_warnings(project: Dict[str, Any], indicators: DerivedIndicators, risk_report: RiskReport) -> List[EarlyWarning]:
    warnings = []
    pid = project.get("project_id", "PROJ")
    pname = project.get("project_name", "Unknown Project")
    phys_prog = float(project.get("physical_progress", 0.0))
    fin_prog = float(project.get("financial_progress", 0.0))

    # 1. High Schedule Pressure Warning
    if indicators.schedule_pressure >= 2.0:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-SCHED-CRIT-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="High Schedule Pressure",
            severity="Critical",
            triggering_indicator=f"Schedule Pressure = {indicators.schedule_pressure}x",
            explanation=f"Required execution velocity is {indicators.schedule_pressure}x original planned rate to meet target date.",
            recommended_review_action="Convene emergency project monitoring review with executing agencies; examine critical path activities and work-front availability.",
            status="Active"
        ))
    elif indicators.schedule_pressure >= 1.4:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-SCHED-HIGH-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="Elevated Schedule Pressure",
            severity="High",
            triggering_indicator=f"Schedule Pressure = {indicators.schedule_pressure}x",
            explanation="Schedule compression detected; project timeline is compressing relative to remaining physical deliverables.",
            recommended_review_action="Audit milestone timelines and review equipment/manpower deployment on site.",
            status="Active"
        ))

    # 2. Cost Escalation Warning
    if indicators.cost_variance_pct >= 35.0:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-COST-CRIT-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="Critical Cost Overrun",
            severity="Critical",
            triggering_indicator=f"Cost Variance = +{indicators.cost_variance_pct:.1f}% (+₹{indicators.cost_overrun_amount:,.2f} Cr)",
            explanation=f"Approved cost exceeded by +{indicators.cost_variance_pct:.1f}%. High risk of funding shortfall and scope escalation.",
            recommended_review_action="Initiate comprehensive Revised Cost Estimate (RCE) scrutiny and financial audit of scope revisions.",
            status="Active"
        ))
    elif indicators.cost_variance_pct >= 15.0:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-COST-HIGH-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="High Cost Escalation",
            severity="High",
            triggering_indicator=f"Cost Variance = +{indicators.cost_variance_pct:.1f}%",
            explanation="Cost revisions exceed 15% of original Cabinet/Ministry sanction threshold.",
            recommended_review_action="Review contract price escalation clauses, raw material indices, and land acquisition payouts.",
            status="Active"
        ))

    # 3. Expenditure-Progress Mismatch
    if indicators.progress_gap >= 25.0:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-GAP-CRIT-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="Severe Expenditure-Progress Mismatch",
            severity="Critical",
            triggering_indicator=f"Financial Progress ({fin_prog:.1f}%) - Physical Progress ({phys_prog:.1f}%) = +{indicators.progress_gap:.1f}%",
            explanation="Cumulative disbursement significantly leads verified physical execution on ground, posing risk of unbacked expenditure.",
            recommended_review_action="Conduct on-site third-party quality and physical measurement audit prior to releasing subsequent tranches.",
            status="Active"
        ))
    elif indicators.progress_gap >= 15.0:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-GAP-MED-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="Expenditure-Progress Gap",
            severity="Medium",
            triggering_indicator=f"Progress Gap = +{indicators.progress_gap:.1f}%",
            explanation="Disbursements run ahead of reported milestones. May reflect advance procurement or mobilization outlays.",
            recommended_review_action="Verify physical conversion of equipment mobilization and material advances into completed works.",
            status="Active"
        ))

    # 4. Low Physical Progress with High Time Elapsed
    if indicators.time_elapsed_ratio >= 0.50 and phys_prog < 25.0:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-PROG-HIGH-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="Stalled Physical Progress",
            severity="High",
            triggering_indicator=f"Physical Progress = {phys_prog:.1f}% with {indicators.time_elapsed_ratio*100:.0f}% Time Elapsed",
            explanation="Project has consumed over half of planned timeline while executing less than a quarter of physical scope.",
            recommended_review_action="Examine land acquisition, statutory/environmental clearances, utility shifting, and contractor dispute status.",
            status="Active"
        ))

    # 5. Overdue Completion Date Slippage
    if indicators.schedule_variance_months >= 24.0:
        warnings.append(EarlyWarning(
            warning_id=f"WARN-SLIP-CRIT-{pid}",
            project_id=pid,
            project_name=pname,
            warning_type="Chronic Completion Delay",
            severity="Critical",
            triggering_indicator=f"Projected Delay = {indicators.schedule_variance_months:.1f} Months",
            explanation="Projected commissioning date has slipped by more than two years beyond original approved timeline.",
            recommended_review_action="Escalate to Committee of Secretaries / Project Monitoring Group (PMG) for inter-ministerial resolution.",
            status="Active"
        ))

    return warnings
