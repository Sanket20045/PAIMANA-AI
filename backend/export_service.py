import io
import pandas as pd
from typing import List, Dict, Any

def export_projects_to_csv(projects: List[Dict[str, Any]]) -> bytes:
    flattened = []
    for p in projects:
        ind = p.get("derived_indicators", {})
        risk = p.get("risk_report", {})
        flattened.append({
            "Project ID": p.get("project_id"),
            "Project Name": p.get("project_name"),
            "Ministry": p.get("ministry"),
            "Sector": p.get("sector"),
            "State": p.get("state"),
            "Original Cost (₹ Cr)": p.get("original_cost"),
            "Revised Cost (₹ Cr)": p.get("revised_cost"),
            "Cost Variance (%)": ind.get("cost_variance_pct"),
            "Expenditure (₹ Cr)": p.get("expenditure"),
            "Expenditure Ratio": ind.get("expenditure_ratio"),
            "Physical Progress (%)": p.get("physical_progress"),
            "Financial Progress (%)": p.get("financial_progress"),
            "Progress Gap (%)": ind.get("progress_gap"),
            "Schedule Variance (Months)": ind.get("schedule_variance_months"),
            "Schedule Pressure": ind.get("schedule_pressure"),
            "Overall Risk Score": risk.get("overall_risk_score"),
            "Risk Category": risk.get("risk_category"),
            "Cost Risk": risk.get("cost_risk"),
            "Schedule Risk": risk.get("schedule_risk"),
            "Progress Risk": risk.get("progress_risk"),
            "Financial Risk": risk.get("financial_risk"),
            "Priority Score": p.get("priority_score"),
            "Priority Rank": p.get("priority_rank"),
            "Active Warnings": p.get("warning_count", 0),
            "Anomalies Flagged": p.get("anomaly_count", 0),
            "Data Source": p.get("data_source", "demo")
        })

    df = pd.DataFrame(flattened)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")

def export_projects_to_xlsx(projects: List[Dict[str, Any]]) -> bytes:
    flattened = []
    for p in projects:
        ind = p.get("derived_indicators", {})
        risk = p.get("risk_report", {})
        flattened.append({
            "Project ID": p.get("project_id"),
            "Project Name": p.get("project_name"),
            "Ministry": p.get("ministry"),
            "Sector": p.get("sector"),
            "State": p.get("state"),
            "Original Cost (₹ Cr)": p.get("original_cost"),
            "Revised Cost (₹ Cr)": p.get("revised_cost"),
            "Cost Variance (%)": ind.get("cost_variance_pct"),
            "Expenditure (₹ Cr)": p.get("expenditure"),
            "Expenditure Ratio": ind.get("expenditure_ratio"),
            "Physical Progress (%)": p.get("physical_progress"),
            "Financial Progress (%)": p.get("financial_progress"),
            "Progress Gap (%)": ind.get("progress_gap"),
            "Schedule Variance (Months)": ind.get("schedule_variance_months"),
            "Schedule Pressure": ind.get("schedule_pressure"),
            "Overall Risk Score": risk.get("overall_risk_score"),
            "Risk Category": risk.get("risk_category"),
            "Cost Risk": risk.get("cost_risk"),
            "Schedule Risk": risk.get("schedule_risk"),
            "Progress Risk": risk.get("progress_risk"),
            "Financial Risk": risk.get("financial_risk"),
            "Priority Score": p.get("priority_score"),
            "Priority Rank": p.get("priority_rank"),
            "Active Warnings": p.get("warning_count", 0),
            "Anomalies Flagged": p.get("anomaly_count", 0),
            "Data Source": p.get("data_source", "demo")
        })

    df = pd.DataFrame(flattened)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="PAIMANA_Risk_Analysis")
    return buffer.getvalue()
