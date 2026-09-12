import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "paimana.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        project_name TEXT NOT NULL,
        ministry TEXT NOT NULL,
        sector TEXT NOT NULL,
        state TEXT NOT NULL,
        original_cost REAL NOT NULL,
        revised_cost REAL NOT NULL,
        expenditure REAL NOT NULL,
        start_date TEXT NOT NULL,
        original_completion_date TEXT NOT NULL,
        expected_completion_date TEXT NOT NULL,
        physical_progress REAL NOT NULL,
        financial_progress REAL NOT NULL,
        data_source TEXT DEFAULT 'demo',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_analysis_cache (
        project_id TEXT PRIMARY KEY,
        derived_indicators TEXT NOT NULL,
        risk_report TEXT NOT NULL,
        warnings TEXT NOT NULL,
        anomalies TEXT NOT NULL,
        recommendations TEXT NOT NULL,
        priority_score REAL NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def save_project(project_data: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO projects (
        project_id, project_name, ministry, sector, state,
        original_cost, revised_cost, expenditure,
        start_date, original_completion_date, expected_completion_date,
        physical_progress, financial_progress, data_source, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(project_id) DO UPDATE SET
        project_name = excluded.project_name,
        ministry = excluded.ministry,
        sector = excluded.sector,
        state = excluded.state,
        original_cost = excluded.original_cost,
        revised_cost = excluded.revised_cost,
        expenditure = excluded.expenditure,
        start_date = excluded.start_date,
        original_completion_date = excluded.original_completion_date,
        expected_completion_date = excluded.expected_completion_date,
        physical_progress = excluded.physical_progress,
        financial_progress = excluded.financial_progress,
        data_source = excluded.data_source,
        updated_at = CURRENT_TIMESTAMP
    """, (
        project_data["project_id"],
        project_data["project_name"],
        project_data["ministry"],
        project_data["sector"],
        project_data["state"],
        float(project_data["original_cost"]),
        float(project_data["revised_cost"]),
        float(project_data["expenditure"]),
        project_data["start_date"],
        project_data["original_completion_date"],
        project_data["expected_completion_date"],
        float(project_data["physical_progress"]),
        float(project_data["financial_progress"]),
        project_data.get("data_source", "demo")
    ))
    conn.commit()
    conn.close()

def get_all_projects() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY project_id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_project_by_id(project_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM project_analysis_cache WHERE project_id = ?", (project_id,))
    conn.commit()
    conn.close()

def clear_all_projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects")
    cursor.execute("DELETE FROM project_analysis_cache")
    conn.commit()
    conn.close()
