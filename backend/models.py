from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProjectBase(BaseModel):
    project_id: str
    project_name: str
    ministry: str
    sector: str
    state: str
    original_cost: float = Field(..., description="Original Approved Cost in ₹ Crores")
    revised_cost: float = Field(..., description="Current/Revised Cost in ₹ Crores")
    expenditure: float = Field(..., description="Cumulative Expenditure in ₹ Crores")
    start_date: str = Field(..., description="Format: YYYY-MM-DD")
    original_completion_date: str = Field(..., description="Format: YYYY-MM-DD")
    expected_completion_date: str = Field(..., description="Format: YYYY-MM-DD")
    physical_progress: float = Field(..., ge=0.0, le=100.0, description="Physical Progress %")
    financial_progress: float = Field(..., ge=0.0, le=100.0, description="Financial Progress %")
    data_source: Optional[str] = "demo"  # 'demo', 'manual', 'uploaded'

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    ministry: Optional[str] = None
    sector: Optional[str] = None
    state: Optional[str] = None
    original_cost: Optional[float] = None
    revised_cost: Optional[float] = None
    expenditure: Optional[float] = None
    start_date: Optional[str] = None
    original_completion_date: Optional[str] = None
    expected_completion_date: Optional[str] = None
    physical_progress: Optional[float] = None
    financial_progress: Optional[float] = None

class DerivedIndicators(BaseModel):
    cost_variance_pct: float
    cost_overrun_amount: float
    expenditure_ratio: float
    progress_gap: float
    schedule_variance_months: float
    schedule_pressure: float
    project_age_months: float
    planned_duration_months: float
    revised_duration_months: float
    time_elapsed_ratio: float
    progress_to_time_efficiency: float
    size_band: str

class RiskReport(BaseModel):
    cost_risk: float
    schedule_risk: float
    progress_risk: float
    financial_risk: float
    overall_risk_score: float
    risk_category: str  # Low (0-30), Medium (31-60), High (61-80), Critical (81-100)
    top_factors: List[Dict[str, Any]]
    explanation: str

class EarlyWarning(BaseModel):
    warning_id: str
    project_id: str
    project_name: str
    warning_type: str
    severity: str  # Low, Medium, High, Critical
    triggering_indicator: str
    explanation: str
    recommended_review_action: str
    status: str = "Active"

class Anomaly(BaseModel):
    anomaly_id: str
    project_id: str
    project_name: str
    anomaly_type: str
    severity: str
    trigger_indicator: str
    description: str
    recommended_check: str

class Recommendation(BaseModel):
    rule_id: str
    category: str
    title: str
    action: str
    priority: str

class ProjectSummary(ProjectBase):
    derived_indicators: DerivedIndicators
    risk_report: RiskReport
    priority_score: float
    priority_rank: int
    warning_count: int
    anomaly_count: int

class ProjectDetailResponse(BaseModel):
    project: ProjectBase
    derived_indicators: DerivedIndicators
    risk_report: RiskReport
    warnings: List[EarlyWarning]
    anomalies: List[Anomaly]
    recommendations: List[Recommendation]
    priority_score: float
    priority_rank: int

class DashboardKPIs(BaseModel):
    total_projects: int
    critical_risk_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_warnings: int
    total_anomalies: int
    projects_requiring_attention: int
    total_original_cost: float
    total_revised_cost: float
    total_expenditure: float
    avg_risk_score: float
    data_mode: str  # 'demo', 'manual', 'uploaded', 'mixed'
    demo_disclaimer: str

class WhatIfRequest(BaseModel):
    project_id: str
    simulated_physical_progress: Optional[float] = None
    simulated_revised_cost: Optional[float] = None
    simulated_expected_completion: Optional[str] = None
    simulated_expenditure: Optional[float] = None

class WhatIfResponse(BaseModel):
    project_id: str
    original_risk: RiskReport
    simulated_risk: RiskReport
    score_change: float
    derived_changes: Dict[str, Any]
    warnings_added: List[str]
    warnings_resolved: List[str]
    scenario_notes: str

class ChatQueryRequest(BaseModel):
    query: str

class ChatQueryResponse(BaseModel):
    query: str
    answer: str
    intent: str
    related_projects: List[Dict[str, Any]]
    suggested_actions: List[str]

class ColumnMappingRequest(BaseModel):
    filename: str
    mappings: Dict[str, str]

class UploadPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    detected_columns: List[str]
    recommended_mappings: Dict[str, str]
    preview_rows: List[Dict[str, Any]]
    quality_score: float
    issues_detected: List[str]
