import io
import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple
from backend.db import get_all_projects, save_project, clear_all_projects
from backend.models import (
    ProjectBase, ProjectSummary, DerivedIndicators, RiskReport,
    EarlyWarning, Anomaly, Recommendation, ProjectDetailResponse,
    UploadPreviewResponse
)
from backend.feature_engineering import compute_derived_indicators
from backend.risk_engine import evaluate_project_risk
from backend.early_warning_engine import detect_early_warnings
from backend.anomaly_engine import detect_anomalies
from backend.recommendation_engine import generate_recommendations
from backend.priority_engine import compute_priority_score, rank_projects

STANDARD_COLUMNS = [
    "project_id", "project_name", "ministry", "sector", "state",
    "original_cost", "revised_cost", "expenditure",
    "start_date", "original_completion_date", "expected_completion_date",
    "physical_progress", "financial_progress"
]

SAMPLE_PROJECTS_SEEDS = [
    # 1. Critical Schedule & Cost Risk
    {
        "project_id": "PRJ-RLY-101",
        "project_name": "Udhampur-Srinagar-Baramulla Rail Link (Tunnel Section)",
        "ministry": "Ministry of Railways",
        "sector": "Railways",
        "state": "Jammu and Kashmir",
        "original_cost": 21614.0,
        "revised_cost": 37012.0,
        "expenditure": 34800.0,
        "start_date": "2018-04-01",
        "original_completion_date": "2023-12-31",
        "expected_completion_date": "2027-06-30",
        "physical_progress": 68.5,
        "financial_progress": 94.0,
        "data_source": "demo"
    },
    # 2. Critical Schedule Pressure & Stalled Progress
    {
        "project_id": "PRJ-HWY-202",
        "project_name": "Delhi-Dehradun Economic Corridor (Package 3 Expressway)",
        "ministry": "Ministry of Road Transport and Highways",
        "sector": "Roads & Highways",
        "state": "Uttarakhand",
        "original_cost": 4850.0,
        "revised_cost": 6420.0,
        "expenditure": 5100.0,
        "start_date": "2021-02-15",
        "original_completion_date": "2024-03-31",
        "expected_completion_date": "2027-12-31",
        "physical_progress": 38.0,
        "financial_progress": 79.4,
        "data_source": "demo"
    },
    # 3. Healthy / Low Risk Project
    {
        "project_id": "PRJ-PWR-303",
        "project_name": "Rewa Ultra Mega Solar Power Park Transmission Grid",
        "ministry": "Ministry of Power",
        "sector": "Power & Energy",
        "state": "Madhya Pradesh",
        "original_cost": 1250.0,
        "revised_cost": 1280.0,
        "expenditure": 1120.0,
        "start_date": "2023-01-10",
        "original_completion_date": "2027-03-31",
        "expected_completion_date": "2027-04-15",
        "physical_progress": 82.0,
        "financial_progress": 87.5,
        "data_source": "demo"
    },
    # 4. Expenditure-Progress Asymmetry (Anomaly)
    {
        "project_id": "PRJ-URB-404",
        "project_name": "Bengaluru Suburban Rail Project (Corridor 2 Chikkabanavara)",
        "ministry": "Ministry of Housing and Urban Affairs",
        "sector": "Urban Mass Transit",
        "state": "Karnataka",
        "original_cost": 15767.0,
        "revised_cost": 15767.0,
        "expenditure": 9800.0,
        "start_date": "2022-06-01",
        "original_completion_date": "2026-11-30",
        "expected_completion_date": "2028-10-31",
        "physical_progress": 22.0,
        "financial_progress": 62.2,
        "data_source": "demo"
    },
    # 5. High Cost Escalation Outlier
    {
        "project_id": "PRJ-PRT-505",
        "project_name": "Vadhavan Deep Draft Mega Port Connectivity Channel",
        "ministry": "Ministry of Ports, Shipping and Waterways",
        "sector": "Ports & Shipping",
        "state": "Maharashtra",
        "original_cost": 18200.0,
        "revised_cost": 38900.0,
        "expenditure": 14200.0,
        "start_date": "2021-08-01",
        "original_completion_date": "2027-12-31",
        "expected_completion_date": "2030-03-31",
        "physical_progress": 28.0,
        "financial_progress": 36.5,
        "data_source": "demo"
    },
    # 6. Moderate Risk / Balanced
    {
        "project_id": "PRJ-HWY-206",
        "project_name": "Varanasi-Kolkata Greenfield Expressway (Bihar Section)",
        "ministry": "Ministry of Road Transport and Highways",
        "sector": "Roads & Highways",
        "state": "Bihar",
        "original_cost": 7200.0,
        "revised_cost": 7850.0,
        "expenditure": 3400.0,
        "start_date": "2022-11-01",
        "original_completion_date": "2026-12-31",
        "expected_completion_date": "2027-09-30",
        "physical_progress": 46.0,
        "financial_progress": 43.3,
        "data_source": "demo"
    },
    # 7. Low Risk On Track
    {
        "project_id": "PRJ-RLY-107",
        "project_name": "Western Dedicated Freight Corridor (Dadri-Rewari Section)",
        "ministry": "Ministry of Railways",
        "sector": "Railways",
        "state": "Haryana",
        "original_cost": 8400.0,
        "revised_cost": 8600.0,
        "expenditure": 8100.0,
        "start_date": "2020-03-01",
        "original_completion_date": "2026-06-30",
        "expected_completion_date": "2026-08-31",
        "physical_progress": 91.5,
        "financial_progress": 94.2,
        "data_source": "demo"
    },
    # 8. High Progress Lag Anomaly (Zero physical with high spend)
    {
        "project_id": "PRJ-PWR-308",
        "project_name": "Dibang Multipurpose Hydropower Dam Project",
        "ministry": "Ministry of Power",
        "sector": "Power & Energy",
        "state": "Arunachal Pradesh",
        "original_cost": 28080.0,
        "revised_cost": 31900.0,
        "expenditure": 4200.0,
        "start_date": "2023-03-15",
        "original_completion_date": "2031-12-31",
        "expected_completion_date": "2033-12-31",
        "physical_progress": 0.0,
        "financial_progress": 13.2,
        "data_source": "demo"
    },
    # 9. Critical Metro Project
    {
        "project_id": "PRJ-URB-409",
        "project_name": "Patna Metro Rail Project Phase 1 (Danapur to Khemnichak)",
        "ministry": "Ministry of Housing and Urban Affairs",
        "sector": "Urban Mass Transit",
        "state": "Bihar",
        "original_cost": 13365.0,
        "revised_cost": 15890.0,
        "expenditure": 8900.0,
        "start_date": "2020-09-01",
        "original_completion_date": "2024-08-31",
        "expected_completion_date": "2027-10-31",
        "physical_progress": 42.0,
        "financial_progress": 56.0,
        "data_source": "demo"
    },
    # 10. Low Risk Waterways
    {
        "project_id": "PRJ-PRT-510",
        "project_name": "Jal Marg Vikas Project on National Waterway-1 (Ganga Multi-modal)",
        "ministry": "Ministry of Ports, Shipping and Waterways",
        "sector": "Ports & Shipping",
        "state": "Uttar Pradesh",
        "original_cost": 5369.0,
        "revised_cost": 5369.0,
        "expenditure": 4750.0,
        "start_date": "2018-05-01",
        "original_completion_date": "2026-12-31",
        "expected_completion_date": "2026-12-31",
        "physical_progress": 89.0,
        "financial_progress": 88.5,
        "data_source": "demo"
    }
]

# Additional 35+ realistic projects generated programmatically to form a 45+ robust dataset
EXTRA_PROJECT_TEMPLATES = [
    ("PRJ-HWY-211", "Mumbai-Goa NH-66 4-Laning (Kashedi Tunnel Section)", "Ministry of Road Transport and Highways", "Roads & Highways", "Maharashtra", 3200, 4900, 4100, "2019-01-01", "2022-12-31", "2027-03-31", 62.0, 83.7),
    ("PRJ-HWY-212", "Amritsar-Jamnagar Economic Corridor (Rajasthan Package)", "Ministry of Road Transport and Highways", "Roads & Highways", "Rajasthan", 6800, 6950, 6100, "2021-04-01", "2026-10-31", "2026-11-30", 86.0, 87.8),
    ("PRJ-HWY-213", "Chennai-Bengaluru Expressway Package II", "Ministry of Road Transport and Highways", "Roads & Highways", "Tamil Nadu", 4200, 4450, 3100, "2022-02-01", "2026-06-30", "2026-09-30", 71.0, 69.7),
    ("PRJ-HWY-214", "Zojila Tunnel Strategic Highway Link", "Ministry of Road Transport and Highways", "Roads & Highways", "Ladakh", 6808, 9300, 6200, "2020-10-15", "2026-11-30", "2028-12-31", 49.0, 66.7),
    ("PRJ-HWY-215", "Raipur-Visakhapatnam Greenfield Corridor (Odisha Stretch)", "Ministry of Road Transport and Highways", "Roads & Highways", "Odisha", 5600, 5800, 3900, "2022-05-01", "2026-12-31", "2027-04-30", 63.0, 67.2),
    ("PRJ-HWY-216", "Srinagar Ring Road 4-Laning Phase II", "Ministry of Road Transport and Highways", "Roads & Highways", "Jammu and Kashmir", 2100, 2950, 2400, "2019-06-01", "2023-03-31", "2027-08-31", 54.0, 81.4),
    ("PRJ-HWY-217", "Hyderabad Regional Ring Road (Northern Part)", "Ministry of Road Transport and Highways", "Roads & Highways", "Telangana", 9500, 11200, 3100, "2023-01-01", "2028-06-30", "2028-12-31", 24.0, 27.7),
    ("PRJ-HWY-218", "Guwahati Ring Road and Brahmaputra Bridge", "Ministry of Road Transport and Highways", "Roads & Highways", "Assam", 5729, 5729, 1400, "2024-02-01", "2029-01-31", "2029-01-31", 18.0, 24.4),
    ("PRJ-RLY-119", "Mumbai-Ahmedabad High Speed Rail (Gujarat Viaduct)", "Ministry of Railways", "Railways", "Gujarat", 63000, 72000, 56000, "2019-08-01", "2024-12-31", "2027-12-31", 69.0, 77.8),
    ("PRJ-RLY-120", "Mumbai-Ahmedabad High Speed Rail (Maharashtra Undersea Tunnel)", "Ministry of Railways", "Railways", "Maharashtra", 45000, 56000, 18500, "2021-01-01", "2025-12-31", "2029-03-31", 29.0, 33.0),
    ("PRJ-RLY-121", "Rishikesh-Karnaprayag Rail Link", "Ministry of Railways", "Railways", "Uttarakhand", 16216, 24650, 19800, "2019-03-01", "2024-12-31", "2027-06-30", 58.0, 80.3),
    ("PRJ-RLY-122", "Bairabi-Sairang New Broad Gauge Railway Line", "Ministry of Railways", "Railways", "Mizoram", 5021, 8213, 7600, "2015-09-01", "2020-03-31", "2026-12-31", 89.0, 92.5),
    ("PRJ-RLY-123", "Sealdah-Ranaghat-Gede 3rd Line Doubling", "Ministry of Railways", "Railways", "West Bengal", 1450, 1600, 1380, "2020-01-01", "2024-06-30", "2026-09-30", 81.0, 86.3),
    ("PRJ-RLY-124", "Jiribam-Imphal Rail Line Connecting Manipur Capital", "Ministry of Railways", "Railways", "Manipur", 13809, 14322, 12900, "2017-04-01", "2022-03-31", "2026-11-30", 91.0, 90.1),
    ("PRJ-RLY-125", "Sonu-Dhanbad 4th Railway Coal Corridor", "Ministry of Railways", "Railways", "Jharkhand", 2800, 3100, 2200, "2021-07-01", "2026-03-31", "2026-12-31", 72.0, 71.0),
    ("PRJ-PWR-326", "Pakal Dul Hydroelectric Power Project (1000 MW)", "Ministry of Power", "Power & Energy", "Jammu and Kashmir", 8112, 12450, 9100, "2018-06-01", "2024-04-30", "2028-06-30", 52.0, 73.1),
    ("PRJ-PWR-327", "Subansiri Lower Hydro Electric Project (2000 MW)", "Ministry of Power", "Power & Energy", "Assam", 6285, 21247, 19800, "2014-01-01", "2018-12-31", "2026-10-31", 93.0, 93.2),
    ("PRJ-PWR-328", "Green Energy Corridor Phase-II Inter-State Transmission (Gujarat)", "Ministry of Power", "Power & Energy", "Gujarat", 4800, 4800, 3200, "2022-08-01", "2026-12-31", "2026-12-31", 64.0, 66.7),
    ("PRJ-PWR-329", "Khavda Renewable Energy Park 765kV High Voltage Evacuation", "Ministry of Power", "Power & Energy", "Gujarat", 12300, 12300, 7400, "2023-02-01", "2027-03-31", "2027-05-31", 58.0, 60.2),
    ("PRJ-PWR-330", "Bhadla Solar Park Phase IV Expansion Grid", "Ministry of Power", "Power & Energy", "Rajasthan", 950, 950, 890, "2022-01-01", "2025-06-30", "2025-07-31", 98.0, 93.7),
    ("PRJ-URB-431", "Mumbai Metro Line 3 (Aqua Line Underground Colaba-SEEPZ)", "Ministry of Housing and Urban Affairs", "Urban Mass Transit", "Maharashtra", 23136, 37276, 34200, "2016-08-01", "2021-12-31", "2026-11-30", 94.0, 91.7),
    ("PRJ-URB-432", "Agra Metro Rail Project Priority Corridor", "Ministry of Housing and Urban Affairs", "Urban Mass Transit", "Uttar Pradesh", 8379, 8379, 5800, "2020-12-01", "2026-03-31", "2026-06-30", 72.0, 69.2),
    ("PRJ-URB-433", "Bhopal Metro Rail System Priority Section", "Ministry of Housing and Urban Affairs", "Urban Mass Transit", "Madhya Pradesh", 6941, 7450, 4100, "2019-10-01", "2024-09-30", "2027-03-31", 56.0, 55.0),
    ("PRJ-URB-434", "Kochi Water Metro Phase II Integrated Feeder", "Ministry of Housing and Urban Affairs", "Urban Mass Transit", "Kerala", 819, 819, 690, "2021-03-01", "2025-12-31", "2026-04-30", 87.0, 84.2),
    ("PRJ-URB-435", "Surat Metro Phase 1 (Sarthana to Dream City)", "Ministry of Housing and Urban Affairs", "Urban Mass Transit", "Gujarat", 12020, 12020, 4900, "2021-06-01", "2027-03-31", "2027-06-30", 41.0, 40.8),
    ("PRJ-PRT-536", "Vizhinjam International Deepwater Multipurpose Seaport Rail Link", "Ministry of Ports, Shipping and Waterways", "Ports & Shipping", "Kerala", 7700, 8867, 7200, "2017-09-01", "2023-05-31", "2026-12-31", 88.0, 81.2),
    ("PRJ-PRT-537", "Paradip Port Western Dock Mechanization & Deepening", "Ministry of Ports, Shipping and Waterways", "Ports & Shipping", "Odisha", 3004, 3004, 2150, "2022-04-01", "2026-10-31", "2026-10-31", 73.0, 71.6),
    ("PRJ-PRT-538", "Kolkata Syama Prasad Mookerjee Port Container Terminal Automation", "Ministry of Ports, Shipping and Waterways", "Ports & Shipping", "West Bengal", 980, 1150, 620, "2022-10-01", "2026-08-31", "2027-02-28", 51.0, 53.9),
    ("PRJ-PRT-539", "Deendayal Port Kandla Oil Jetty No. 9 Construction", "Ministry of Ports, Shipping and Waterways", "Ports & Shipping", "Gujarat", 495, 510, 470, "2023-01-15", "2026-06-30", "2026-07-31", 92.0, 92.2),
    ("PRJ-HWY-240", "Nagpur-Vijayawada Economic Corridor (Package 1 Telangana)", "Ministry of Road Transport and Highways", "Roads & Highways", "Telangana", 4100, 4100, 1600, "2023-06-01", "2027-05-31", "2027-05-31", 38.0, 39.0)
]

def generate_full_synthetic_dataset() -> List[Dict[str, Any]]:
    projects = list(SAMPLE_PROJECTS_SEEDS)
    for t in EXTRA_PROJECT_TEMPLATES:
        projects.append({
            "project_id": t[0],
            "project_name": t[1],
            "ministry": t[2],
            "sector": t[3],
            "state": t[4],
            "original_cost": float(t[5]),
            "revised_cost": float(t[6]),
            "expenditure": float(t[7]),
            "start_date": t[8],
            "original_completion_date": t[9],
            "expected_completion_date": t[10],
            "physical_progress": float(t[11]),
            "financial_progress": float(t[12]),
            "data_source": "demo"
        })
    return projects

def seed_demo_data():
    clear_all_projects()
    demo_projects = generate_full_synthetic_dataset()
    for p in demo_projects:
        save_project(p)

def analyze_project(project_dict: Dict[str, Any]) -> ProjectDetailResponse:
    indicators = compute_derived_indicators(project_dict)
    risk_report = evaluate_project_risk(project_dict, indicators)
    warnings = detect_early_warnings(project_dict, indicators, risk_report)
    anomalies = detect_anomalies(project_dict, indicators)
    recommendations = generate_recommendations(project_dict, indicators, risk_report)

    crit_warns = sum(1 for w in warnings if w.severity == "Critical")
    priority_score = compute_priority_score(project_dict, risk_report.model_dump(), len(warnings), crit_warns)

    return ProjectDetailResponse(
        project=ProjectBase(**project_dict),
        derived_indicators=indicators,
        risk_report=risk_report,
        warnings=warnings,
        anomalies=anomalies,
        recommendations=recommendations,
        priority_score=priority_score,
        priority_rank=0  # Assigned after whole-batch sorting
    )

def get_all_analyzed_projects() -> List[Dict[str, Any]]:
    raw_projects = get_all_projects()
    if not raw_projects:
        seed_demo_data()
        raw_projects = get_all_projects()

    analyzed = []
    for p in raw_projects:
        detail = analyze_project(p)
        item = detail.project.model_dump()
        item["derived_indicators"] = detail.derived_indicators.model_dump()
        item["risk_report"] = detail.risk_report.model_dump()
        item["warnings"] = [w.model_dump() for w in detail.warnings]
        item["anomalies"] = [a.model_dump() for a in detail.anomalies]
        item["recommendations"] = [r.model_dump() for r in detail.recommendations]
        item["priority_score"] = detail.priority_score
        item["warning_count"] = len(detail.warnings)
        item["anomaly_count"] = len(detail.anomalies)
        analyzed.append(item)

    # Rank projects
    ranked = rank_projects(analyzed)
    return ranked

def parse_uploaded_file_preview(contents: bytes, filename: str) -> UploadPreviewResponse:
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise ValueError("Unsupported file format. Please upload CSV or XLSX.")
    except Exception as e:
        raise ValueError(f"Could not parse file: {str(e)}")

    total_rows = len(df)
    detected_columns = list(df.columns)
    
    # Fuzzy column mapping
    mapping = {}
    issues = []
    for col in detected_columns:
        norm = col.strip().lower().replace(" ", "_").replace("-", "_").replace("%", "pct")
        if "id" in norm and "project" in norm:
            mapping[col] = "project_id"
        elif "id" == norm:
            mapping[col] = "project_id"
        elif "name" in norm:
            mapping[col] = "project_name"
        elif "ministry" in norm or "dept" in norm:
            mapping[col] = "ministry"
        elif "sector" in norm:
            mapping[col] = "sector"
        elif "state" in norm or "location" in norm:
            mapping[col] = "state"
        elif "original_cost" in norm or ("cost" in norm and "orig" in norm):
            mapping[col] = "original_cost"
        elif "revised_cost" in norm or "current_cost" in norm or ("cost" in norm and "rev" in norm):
            mapping[col] = "revised_cost"
        elif "expenditure" in norm or "spend" in norm:
            mapping[col] = "expenditure"
        elif "start" in norm and "date" in norm:
            mapping[col] = "start_date"
        elif "orig" in norm and "comp" in norm:
            mapping[col] = "original_completion_date"
        elif ("exp" in norm or "rev" in norm) and "comp" in norm:
            mapping[col] = "expected_completion_date"
        elif "phys" in norm:
            mapping[col] = "physical_progress"
        elif "fin" in norm:
            mapping[col] = "financial_progress"

    # Assess quality
    missing_critical = []
    for req in ["project_id", "project_name", "original_cost", "physical_progress"]:
        if req not in mapping.values():
            missing_critical.append(req)

    missing_cells = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    if missing_cells > 0:
        issues.append(f"{missing_cells} empty/missing cells detected in uploaded data.")
    if duplicate_rows > 0:
        issues.append(f"{duplicate_rows} duplicate rows detected.")
    if missing_critical:
        issues.append(f"Unmapped required fields: {', '.join(missing_critical)}.")

    # Quality score out of 100
    penalty = len(missing_critical) * 20 + min(duplicate_rows * 5, 20) + min(missing_cells * 2, 20)
    quality_score = max(100 - penalty, 10)

    # Preview rows
    preview_df = df.head(5).fillna("")
    preview_rows = preview_df.to_dict(orient="records")

    return UploadPreviewResponse(
        filename=filename,
        total_rows=total_rows,
        detected_columns=detected_columns,
        recommended_mappings=mapping,
        preview_rows=preview_rows,
        quality_score=float(quality_score),
        issues_detected=issues
    )

def commit_uploaded_dataset(contents: bytes, filename: str, custom_mapping: Dict[str, str]) -> int:
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        df = pd.read_excel(io.BytesIO(contents))

    # Invert mapping: schema_col -> source_col
    inverted = {v: k for k, v in custom_mapping.items() if v in STANDARD_COLUMNS}
    
    saved_count = 0
    for _, row in df.iterrows():
        try:
            pid = str(row.get(inverted.get("project_id", ""), f"UP-PRJ-{saved_count+1}")).strip()
            pname = str(row.get(inverted.get("project_name", ""), f"Uploaded Project {saved_count+1}")).strip()
            ministry = str(row.get(inverted.get("ministry", ""), "MoSPI / Line Ministry")).strip()
            sector = str(row.get(inverted.get("sector", ""), "General Infrastructure")).strip()
            state = str(row.get(inverted.get("state", ""), "National / Multi-State")).strip()

            orig_cost = float(row.get(inverted.get("original_cost", 1000.0), 1000.0))
            rev_cost = float(row.get(inverted.get("revised_cost", orig_cost), orig_cost))
            expenditure = float(row.get(inverted.get("expenditure", 0.0), 0.0))

            s_date = str(row.get(inverted.get("start_date", "2023-01-01"), "2023-01-01"))[:10]
            o_date = str(row.get(inverted.get("original_completion_date", "2026-12-31"), "2026-12-31"))[:10]
            e_date = str(row.get(inverted.get("expected_completion_date", o_date), o_date))[:10]

            phys_p = float(row.get(inverted.get("physical_progress", 0.0), 0.0))
            fin_p = float(row.get(inverted.get("financial_progress", 0.0), 0.0))

            project_record = {
                "project_id": pid,
                "project_name": pname,
                "ministry": ministry,
                "sector": sector,
                "state": state,
                "original_cost": orig_cost,
                "revised_cost": rev_cost,
                "expenditure": expenditure,
                "start_date": s_date,
                "original_completion_date": o_date,
                "expected_completion_date": e_date,
                "physical_progress": phys_p,
                "financial_progress": fin_p,
                "data_source": "uploaded"
            }
            save_project(project_record)
            saved_count += 1
        except Exception:
            continue

    return saved_count
