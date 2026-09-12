import math
from typing import List, Dict, Any
from backend.models import DerivedIndicators, Anomaly

ANOMALY_DISCLAIMER = "Anomaly indicates an unusual pattern requiring review; it does not establish wrongdoing or data error."

def detect_anomalies(project: Dict[str, Any], indicators: DerivedIndicators) -> List[Anomaly]:
    anomalies = []
    pid = project.get("project_id", "PROJ")
    pname = project.get("project_name", "Unknown")
    orig_cost = float(project.get("original_cost", 0.0))
    rev_cost = float(project.get("revised_cost", orig_cost))
    expenditure = float(project.get("expenditure", 0.0))
    phys_prog = float(project.get("physical_progress", 0.0))
    fin_prog = float(project.get("financial_progress", 0.0))

    # 1. Zero Physical Progress after Substantial Expenditure
    if phys_prog == 0.0 and (expenditure > 50.0 or (rev_cost > 0 and expenditure / rev_cost > 0.15)):
        anomalies.append(Anomaly(
            anomaly_id=f"ANOM-ZERO-PHYS-{pid}",
            project_id=pid,
            project_name=pname,
            anomaly_type="Zero Physical Progress with Significant Capital Spend",
            severity="High",
            trigger_indicator=f"Expenditure = ₹{expenditure:,.2f} Cr, Physical Progress = 0.0%",
            description=f"Significant funds have been disbursed ({expenditure/rev_cost*100:.1f}% of budget) while recorded on-ground physical delivery remains at 0.0%. {ANOMALY_DISCLAIMER}",
            recommended_check="Verify if recorded expenditure represents advance payments, land compensation, or pending physical milestone certification."
        ))

    # 2. Progress Inversion / Divergence (> 40% gap)
    if indicators.progress_gap >= 40.0:
        anomalies.append(Anomaly(
            anomaly_id=f"ANOM-INVERT-{pid}",
            project_id=pid,
            project_name=pname,
            anomaly_type="Extreme Progress-Disbursement Asymmetry",
            severity="Critical",
            trigger_indicator=f"Financial Progress: {fin_prog:.1f}% vs Physical Progress: {phys_prog:.1f}% (Gap: +{indicators.progress_gap:.1f}%)",
            description=f"Statistical anomaly: financial release leads physical achievement by {indicators.progress_gap:.1f} percentage points, falling outside standard project variance corridors. {ANOMALY_DISCLAIMER}",
            recommended_check="Cross-reference financial release ledger with engineer-in-charge measurement books (MB) and site inspection reports."
        ))

    # 3. High Physical Progress with Negligible Expenditure
    if phys_prog >= 60.0 and fin_prog < 10.0 and expenditure < (0.10 * rev_cost):
        anomalies.append(Anomaly(
            anomaly_id=f"ANOM-LOW-EXP-{pid}",
            project_id=pid,
            project_name=pname,
            anomaly_type="Physical Milestones Preceding Financial Recording",
            severity="Medium",
            trigger_indicator=f"Physical Progress = {phys_prog:.1f}%, Financial Progress = {fin_prog:.1f}%",
            description=f"Advanced physical progress reported with minimal financial expenditure recorded in the system. {ANOMALY_DISCLAIMER}",
            recommended_check="Check for unprocessed contractor billing claims, pending state treasury releases, or PPP equity contribution accounting."
        ))

    # 4. Hyper Cost Escalation (> 100% budget increase)
    if indicators.cost_variance_pct >= 100.0:
        anomalies.append(Anomaly(
            anomaly_id=f"ANOM-HYPER-COST-{pid}",
            project_id=pid,
            project_name=pname,
            anomaly_type="Hyper Cost Escalation (>100% Budget Expansion)",
            severity="Critical",
            trigger_indicator=f"Cost Variance = +{indicators.cost_variance_pct:.1f}% (Revised: ₹{rev_cost:,.2f} Cr vs Orig: ₹{orig_cost:,.2f} Cr)",
            description=f"Project budget has more than doubled relative to initial Cabinet approval. {ANOMALY_DISCLAIMER}",
            recommended_check="Examine major scope alterations, route realignment, geological/technical surprises, and land compensation award revisions."
        ))

    # 5. Elapsed Schedule Stagnation (Time 100% consumed, Progress < 20%)
    if indicators.time_elapsed_ratio >= 1.0 and phys_prog < 20.0:
        anomalies.append(Anomaly(
            anomaly_id=f"ANOM-STAGNATION-{pid}",
            project_id=pid,
            project_name=pname,
            anomaly_type="Severe Tenure Stagnation",
            severity="High",
            trigger_indicator=f"100% Planned Time Elapsed, Only {phys_prog:.1f}% Progress Achieved",
            description=f"Full original planned project duration has elapsed, yet physical execution remains under 20%. {ANOMALY_DISCLAIMER}",
            recommended_check="Review whether project execution was formally stayed, halted by litigation, or pending fundamental environmental clearances."
        ))

    return anomalies
