import re
from typing import List, Dict, Any
from backend.models import ChatQueryRequest, ChatQueryResponse

def process_assistant_query(query_text: str, projects_summary: List[Dict[str, Any]]) -> ChatQueryResponse:
    q = query_text.strip().lower()
    intent = "general_query"
    related = []
    actions = []
    answer = ""

    if not projects_summary:
        return ChatQueryResponse(
            query=query_text,
            answer="No project records currently loaded in the database. Please load demo data or upload a dataset.",
            intent="empty_db",
            related_projects=[],
            suggested_actions=["Load Demo Dataset", "Upload CSV/XLSX"]
        )

    # 1. "Critical risk" / "Show critical projects"
    if "critical" in q or "highest risk" in q or "red" in q:
        intent = "critical_projects"
        criticals = [p for p in projects_summary if p["risk_report"]["risk_category"] == "Critical"]
        # Sort by overall risk score descending
        criticals.sort(key=lambda x: x["risk_report"]["overall_risk_score"], reverse=True)
        count = len(criticals)
        related = [{
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "sector": p["sector"],
            "state": p["state"],
            "risk_score": p["risk_report"]["overall_risk_score"],
            "risk_category": p["risk_report"]["risk_category"],
            "cost_crores": p["revised_cost"]
        } for p in criticals[:8]]

        answer = (
            f"Currently, there are **{count} projects** classified under **Critical Risk** (Score 81–100).\n\n"
            f"The top critical projects by composite risk score are:\n"
        )
        for idx, cp in enumerate(criticals[:5], start=1):
            answer += f"{idx}. **{cp['project_name']}** ({cp['project_id']}) — Risk Score: **{cp['risk_report']['overall_risk_score']}/100** | Sector: {cp['sector']} | Cost: ₹{cp['revised_cost']:,.0f} Cr\n"
        answer += "\n*Recommended Action: Review these projects immediately in the Project Explorer or Early Warning Center.*"
        actions = ["Filter by Critical Risk", "Export Critical Projects CSV", "Review Early Warning Center"]

    # 2. "Which sector has the highest average risk?" / "Sector risk"
    elif "sector" in q and ("highest" in q or "average" in q or "compare" in q or "risk" in q):
        intent = "sector_risk_comparison"
        sector_map: Dict[str, List[float]] = {}
        for p in projects_summary:
            sec = p.get("sector", "Other")
            score = p["risk_report"]["overall_risk_score"]
            sector_map.setdefault(sec, []).append(score)

        sector_stats = []
        for sec, scores in sector_map.items():
            avg_s = sum(scores) / len(scores)
            sector_stats.append((sec, round(avg_s, 1), len(scores)))
        sector_stats.sort(key=lambda x: x[1], reverse=True)

        highest_sec = sector_stats[0]
        answer = (
            f"Sectoral Risk Analysis across {len(projects_summary)} monitored projects:\n\n"
            f"• **Highest Average Risk Sector:** **{highest_sec[0]}** with an average risk score of **{highest_sec[1]} / 100** (across {highest_sec[2]} projects).\n\n"
            f"**Sector Breakdown (Ranked by Risk):**\n"
        )
        for rank, (sec, avg_s, cnt) in enumerate(sector_stats, start=1):
            answer += f"{rank}. **{sec}**: Average Risk **{avg_s}/100** ({cnt} projects)\n"
        
        # Add top projects in highest sector
        top_sec_projects = [p for p in projects_summary if p["sector"] == highest_sec[0]]
        top_sec_projects.sort(key=lambda x: x["risk_report"]["overall_risk_score"], reverse=True)
        related = [{
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "sector": p["sector"],
            "state": p["state"],
            "risk_score": p["risk_report"]["overall_risk_score"],
            "risk_category": p["risk_report"]["risk_category"]
        } for p in top_sec_projects[:5]]
        actions = [f"Filter by Sector: {highest_sec[0]}", "View Sector Analytics"]

    # 3. "Why is Project [X] high risk?" / "Explain Project [X]"
    elif "why" in q or "explain" in q or any(p["project_id"].lower() in q for p in projects_summary):
        intent = "project_explanation"
        matched_proj = None
        for p in projects_summary:
            if p["project_id"].lower() in q or p["project_name"].lower() in q:
                matched_proj = p
                break
        
        if not matched_proj:
            # Pick highest risk project to demonstrate
            sorted_all = sorted(projects_summary, key=lambda x: x["risk_report"]["overall_risk_score"], reverse=True)
            matched_proj = sorted_all[0]

        pid = matched_proj["project_id"]
        pname = matched_proj["project_name"]
        score = matched_proj["risk_report"]["overall_risk_score"]
        cat = matched_proj["risk_report"]["risk_category"]
        indicators = matched_proj["derived_indicators"]
        exp = matched_proj["risk_report"]["explanation"]
        top_factors = matched_proj["risk_report"]["top_factors"]

        answer = (
            f"### Analytical Assessment: {pname} ({pid})\n\n"
            f"• **Risk Classification:** **{cat} Risk** ({score} / 100)\n"
            f"• **Ministry:** {matched_proj['ministry']} | **Sector:** {matched_proj['sector']} | **State:** {matched_proj['state']}\n"
            f"• **Cost Escalation:** Approved ₹{matched_proj['original_cost']:,.0f} Cr $\\rightarrow$ Current ₹{matched_proj['revised_cost']:,.0f} Cr (+{indicators['cost_variance_pct']}%\n"
            f"• **Physical Progress:** {matched_proj['physical_progress']}% | **Financial Progress:** {matched_proj['financial_progress']}%\n"
            f"• **Schedule Pressure:** {indicators['schedule_pressure']}x standard execution speed\n\n"
            f"**Key Risk Drivers:**\n"
        )
        for f in top_factors:
            answer += f"- **{f['dimension']}**: {f['factor']}\n"
        answer += f"\n**Summary Narrative:** {exp}\n"

        related = [{
            "project_id": pid,
            "project_name": pname,
            "sector": matched_proj["sector"],
            "state": matched_proj["state"],
            "risk_score": score,
            "risk_category": cat
        }]
        actions = [f"Open {pid} Drill-Down", "Run What-If Simulation on this Project"]

    # 4. "Show projects above ₹1,000 crore with schedule risk" / "1000 crore"
    elif "1000" in q or "1,000" in q or "crore" in q or "cost" in q:
        intent = "high_value_schedule_risk"
        filtered = [
            p for p in projects_summary 
            if p["revised_cost"] >= 1000.0 and p["risk_report"]["schedule_risk"] >= 50.0
        ]
        filtered.sort(key=lambda x: x["revised_cost"], reverse=True)
        count = len(filtered)
        answer = (
            f"Identified **{count} mega/major projects** with sanctioned cost $\\ge$ ₹1,000 Crore exhibiting elevated schedule risk (Schedule Risk $\\ge$ 50):\n\n"
        )
        for idx, p in enumerate(filtered[:6], start=1):
            answer += (
                f"{idx}. **{p['project_name']}** — ₹{p['revised_cost']:,.0f} Cr | "
                f"Schedule Risk: **{p['risk_report']['schedule_risk']}/100** | "
                f"Physical Progress: {p['physical_progress']}% | State: {p['state']}\n"
            )
        related = [{
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "sector": p["sector"],
            "state": p["state"],
            "risk_score": p["risk_report"]["overall_risk_score"],
            "risk_category": p["risk_report"]["risk_category"],
            "cost_crores": p["revised_cost"]
        } for p in filtered[:8]]
        actions = ["Filter Mega Projects (> ₹1,000 Cr)", "View Cost vs Progress Chart"]

    # 5. "Which projects require attention?" / "Attention queue"
    elif "attention" in q or "priority" in q or "urgent" in q or "requiring attention" in q:
        intent = "attention_queue"
        attention_list = sorted(projects_summary, key=lambda x: x.get("priority_score", 0.0), reverse=True)
        count = len(attention_list)
        answer = (
            f"**Projects Requiring Immediate Attention (Priority Triage Queue)**\n\n"
            f"The system has prioritized projects combining high composite risk, warning severity density, and public capital exposure:\n\n"
        )
        for idx, p in enumerate(attention_list[:6], start=1):
            answer += (
                f"**Rank #{p.get('priority_rank', idx)}**: **{p['project_name']}** ({p['project_id']})\n"
                f"   • Priority Score: **{p.get('priority_score')}/100** | Risk Category: **{p['risk_report']['risk_category']}** ({p['risk_report']['overall_risk_score']}/100)\n"
                f"   • Ministry: {p['ministry']} | Cost: ₹{p['revised_cost']:,.0f} Cr | Warnings: {p.get('warning_count', 0)}\n\n"
            )
        related = [{
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "sector": p["sector"],
            "state": p["state"],
            "risk_score": p["risk_report"]["overall_risk_score"],
            "risk_category": p["risk_report"]["risk_category"],
            "priority_score": p.get("priority_score")
        } for p in attention_list[:6]]
        actions = ["View Projects Requiring Attention Table", "Export Priority List"]

    # Default fallback
    else:
        intent = "summary_overview"
        total = len(projects_summary)
        crit_cnt = sum(1 for p in projects_summary if p["risk_report"]["risk_category"] == "Critical")
        high_cnt = sum(1 for p in projects_summary if p["risk_report"]["risk_category"] == "High")
        avg_risk = round(sum(p["risk_report"]["overall_risk_score"] for p in projects_summary) / total, 1)

        answer = (
            f"**NIRIKSHAN Project Intelligence Overview:**\n\n"
            f"• **Monitored Projects:** {total} infrastructure assets across Indian states.\n"
            f"• **Portfolio Average Risk:** **{avg_risk} / 100**\n"
            f"• **Critical Risk Projects:** **{crit_cnt}** | **High Risk Projects:** **{high_cnt}**\n\n"
            f"You can ask specific queries such as:\n"
            f"1. *“Show critical-risk projects.”*\n"
            f"2. *“Which sector has the highest average risk?”*\n"
            f"3. *“Why is Project ABC high risk?”*\n"
            f"4. *“Show projects above ₹1,000 crore with schedule risk.”*\n"
            f"5. *“Which projects require attention?”*"
        )
        actions = ["Show Critical Projects", "Sector Risk Analysis", "Projects Requiring Attention"]

    return ChatQueryResponse(
        query=query_text,
        answer=answer,
        intent=intent,
        related_projects=related,
        suggested_actions=actions
    )
