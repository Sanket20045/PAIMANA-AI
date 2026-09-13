import os
import io
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from backend.db import init_db, get_project_by_id, delete_project_by_id
from backend.models import (
    ProjectCreate, ProjectUpdate, ProjectDetailResponse,
    DashboardKPIs, WhatIfRequest, WhatIfResponse,
    ChatQueryRequest, ChatQueryResponse, UploadPreviewResponse
)
from backend.data_service import (
    seed_demo_data, get_all_analyzed_projects,
    analyze_project, save_project,
    parse_uploaded_file_preview, commit_uploaded_dataset
)
from backend.what_if_simulator import simulate_project_scenario
from backend.ai_assistant import process_assistant_query
from backend.export_service import export_projects_to_csv, export_projects_to_xlsx

app = FastAPI(
    title="NIRIKSHAN AI - Intelligent Infrastructure Monitoring & Analytics",
    description="Prototype API for SIH 2026",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for pending upload previews
PENDING_UPLOADS: Dict[str, bytes] = {}

@app.on_event("startup")
def on_startup():
    init_db()
    # Check if empty, seed demo data if needed
    projects = get_all_analyzed_projects()

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "NIRIKSHAN AI Decision Support System",
        "mode": "Prototype Functional Demo"
    }

@app.get("/api/dashboard/kpis")
def get_dashboard_kpis():
    projects = get_all_analyzed_projects()
    total = len(projects)
    crit = sum(1 for p in projects if p["risk_report"]["risk_category"] == "Critical")
    high = sum(1 for p in projects if p["risk_report"]["risk_category"] == "High")
    med = sum(1 for p in projects if p["risk_report"]["risk_category"] == "Medium")
    low = sum(1 for p in projects if p["risk_report"]["risk_category"] == "Low")

    total_warns = sum(p.get("warning_count", 0) for p in projects)
    total_anoms = sum(p.get("anomaly_count", 0) for p in projects)
    requiring_attention = sum(1 for p in projects if p["risk_report"]["overall_risk_score"] >= 61.0 or p.get("warning_count", 0) >= 2)

    total_orig = sum(p["original_cost"] for p in projects)
    total_rev = sum(p["revised_cost"] for p in projects)
    total_exp = sum(p["expenditure"] for p in projects)
    avg_risk = round(sum(p["risk_report"]["overall_risk_score"] for p in projects) / total, 1) if total > 0 else 0.0

    sources = set(p.get("data_source", "demo") for p in projects)
    mode = "demo" if sources == {"demo"} else ("uploaded" if sources == {"uploaded"} else "mixed")

    return DashboardKPIs(
        total_projects=total,
        critical_risk_count=crit,
        high_risk_count=high,
        medium_risk_count=med,
        low_risk_count=low,
        total_warnings=total_warns,
        total_anomalies=total_anoms,
        projects_requiring_attention=requiring_attention,
        total_original_cost=round(total_orig, 2),
        total_revised_cost=round(total_rev, 2),
        total_expenditure=round(total_exp, 2),
        avg_risk_score=avg_risk,
        data_mode=mode,
        demo_disclaimer="Prototype Demo Data – Not Official Government Data"
    )

@app.get("/api/dashboard/charts")
def get_dashboard_charts():
    projects = get_all_analyzed_projects()

    # 1. Risk Distribution
    risk_dist = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for p in projects:
        cat = p["risk_report"]["risk_category"]
        risk_dist[cat] = risk_dist.get(cat, 0) + 1

    # 2. Risk by Sector
    sector_map = {}
    for p in projects:
        s = p["sector"]
        sector_map.setdefault(s, []).append(p["risk_report"]["overall_risk_score"])
    
    sector_chart = []
    for s, scores in sector_map.items():
        sector_chart.append({
            "sector": s,
            "avg_risk": round(sum(scores) / len(scores), 1),
            "project_count": len(scores)
        })
    sector_chart.sort(key=lambda x: x["avg_risk"], reverse=True)

    # 3. State-wise Risk
    state_map = {}
    for p in projects:
        st = p["state"]
        state_map.setdefault(st, []).append(p["risk_report"]["overall_risk_score"])
    
    state_chart = []
    for st, scores in state_map.items():
        state_chart.append({
            "state": st,
            "avg_risk": round(sum(scores) / len(scores), 1),
            "count": len(scores)
        })
    state_chart.sort(key=lambda x: x["avg_risk"], reverse=True)

    # 4. Ministry-wise Risk
    min_map = {}
    for p in projects:
        m = p["ministry"]
        min_map.setdefault(m, []).append(p["risk_report"]["overall_risk_score"])
    
    min_chart = []
    for m, scores in min_map.items():
        min_chart.append({
            "ministry": m,
            "avg_risk": round(sum(scores) / len(scores), 1),
            "count": len(scores)
        })
    min_chart.sort(key=lambda x: x["avg_risk"], reverse=True)

    # 5. Cost vs Physical Progress Scatter
    scatter = []
    for p in projects:
        scatter.append({
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "cost": p["revised_cost"],
            "physical_progress": p["physical_progress"],
            "financial_progress": p["financial_progress"],
            "risk_score": p["risk_report"]["overall_risk_score"],
            "risk_category": p["risk_report"]["risk_category"],
            "sector": p["sector"]
        })

    return {
        "risk_distribution": risk_dist,
        "sector_risk": sector_chart,
        "state_risk": state_chart,
        "ministry_risk": min_chart,
        "cost_vs_progress": scatter
    }

@app.get("/api/projects")
def list_projects(
    search: Optional[str] = None,
    ministry: Optional[str] = None,
    sector: Optional[str] = None,
    state: Optional[str] = None,
    risk_category: Optional[str] = None,
    min_cost: Optional[float] = None,
    max_cost: Optional[float] = None,
    sort_by: Optional[str] = "priority_rank"
):
    projects = get_all_analyzed_projects()

    if search:
        s = search.lower()
        projects = [
            p for p in projects 
            if s in p["project_name"].lower() or s in p["project_id"].lower() or s in p["state"].lower() or s in p["sector"].lower()
        ]

    if ministry and ministry != "All":
        projects = [p for p in projects if p["ministry"] == ministry]

    if sector and sector != "All":
        projects = [p for p in projects if p["sector"] == sector]

    if state and state != "All":
        projects = [p for p in projects if p["state"] == state]

    if risk_category and risk_category != "All":
        projects = [p for p in projects if p["risk_report"]["risk_category"] == risk_category]

    if min_cost is not None:
        projects = [p for p in projects if p["revised_cost"] >= min_cost]

    if max_cost is not None:
        projects = [p for p in projects if p["revised_cost"] <= max_cost]

    # Sorting
    if sort_by == "priority_rank":
        projects.sort(key=lambda x: x.get("priority_rank", 999))
    elif sort_by == "risk_score_desc":
        projects.sort(key=lambda x: x["risk_report"]["overall_risk_score"], reverse=True)
    elif sort_by == "risk_score_asc":
        projects.sort(key=lambda x: x["risk_report"]["overall_risk_score"])
    elif sort_by == "cost_desc":
        projects.sort(key=lambda x: x["revised_cost"], reverse=True)
    elif sort_by == "progress_asc":
        projects.sort(key=lambda x: x["physical_progress"])
    elif sort_by == "progress_desc":
        projects.sort(key=lambda x: x["physical_progress"], reverse=True)

    return projects

@app.get("/api/projects/{project_id}")
def get_project_detail(project_id: str):
    p = get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    detail = analyze_project(p)
    return detail

@app.post("/api/projects")
def create_project(project: ProjectCreate):
    p_dict = project.model_dump()
    save_project(p_dict)
    detail = analyze_project(p_dict)
    return {"message": "Project created successfully", "project": detail}

@app.put("/api/projects/{project_id}")
def update_project(project_id: str, updates: ProjectUpdate):
    existing = get_project_by_id(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            existing[k] = v
    existing["data_source"] = "manual"
    save_project(existing)
    detail = analyze_project(existing)
    return {"message": "Project updated successfully", "project": detail}

@app.delete("/api/projects/{project_id}")
def remove_project(project_id: str):
    delete_project_by_id(project_id)
    return {"message": f"Project {project_id} deleted successfully"}

@app.post("/api/projects/reset-demo")
def reset_demo():
    seed_demo_data()
    return {"message": "Database reset to prototype demo data successfully."}

@app.get("/api/warnings")
def list_warnings(severity: Optional[str] = None):
    projects = get_all_analyzed_projects()
    all_warnings = []
    for p in projects:
        for w in p.get("warnings", []):
            w["ministry"] = p["ministry"]
            w["sector"] = p["sector"]
            w["state"] = p["state"]
            w["cost"] = p["revised_cost"]
            all_warnings.append(w)

    if severity and severity != "All":
        all_warnings = [w for w in all_warnings if w["severity"].lower() == severity.lower()]

    severity_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    all_warnings.sort(key=lambda x: severity_order.get(x["severity"], 9))
    return all_warnings

@app.get("/api/anomalies")
def list_anomalies():
    projects = get_all_analyzed_projects()
    all_anomalies = []
    for p in projects:
        for a in p.get("anomalies", []):
            a["ministry"] = p["ministry"]
            a["sector"] = p["sector"]
            a["state"] = p["state"]
            a["cost"] = p["revised_cost"]
            all_anomalies.append(a)

    return all_anomalies

@app.get("/api/priority-queue")
def get_priority_queue(limit: int = 15):
    projects = get_all_analyzed_projects()
    queue = sorted(projects, key=lambda x: x.get("priority_score", 0), reverse=True)
    return queue[:limit]

@app.post("/api/what-if")
def what_if_simulation(request: WhatIfRequest):
    project = get_project_by_id(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = simulate_project_scenario(project, request)
    return result

@app.post("/api/assistant/chat")
def assistant_chat(request: ChatQueryRequest):
    projects = get_all_analyzed_projects()
    response = process_assistant_query(request.query, projects)
    return response

@app.post("/api/upload/preview")
async def upload_preview(file: UploadFile = File(...)):
    contents = await file.read()
    PENDING_UPLOADS[file.filename] = contents
    try:
        preview = parse_uploaded_file_preview(contents, file.filename)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/upload/commit")
async def upload_commit(filename: str = Form(...), mapping: str = Form(...)):
    if filename not in PENDING_UPLOADS:
        raise HTTPException(status_code=404, detail="Uploaded file session expired or not found. Please re-upload.")
    
    contents = PENDING_UPLOADS[filename]
    try:
        custom_mapping = json.loads(mapping)
    except Exception:
        custom_mapping = {}

    count = commit_uploaded_dataset(contents, filename, custom_mapping)
    del PENDING_UPLOADS[filename]
    return {"message": f"Successfully ingested and evaluated {count} projects.", "count": count}

@app.get("/api/export/csv")
def export_csv():
    projects = get_all_analyzed_projects()
    csv_bytes = export_projects_to_csv(projects)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=NIRIKSHAN_Infrastructure_Risk_Export.csv"}
    )

@app.get("/api/export/xlsx")
def export_xlsx():
    projects = get_all_analyzed_projects()
    xlsx_bytes = export_projects_to_xlsx(projects)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=NIRIKSHAN_Infrastructure_Risk_Export.xlsx"}
    )

# Serve Frontend static assets
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
