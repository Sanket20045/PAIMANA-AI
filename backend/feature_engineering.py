from datetime import datetime
from typing import Dict, Any
from backend.models import DerivedIndicators

def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        # Fallback to current year parsing if partial
        try:
            return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.now()

def diff_months(d1: datetime, d2: datetime) -> float:
    """Return difference in months between d2 and d1 (d2 - d1)"""
    return (d2.year - d1.year) * 12.0 + (d2.month - d1.month) + (d2.day - d1.day) / 30.0

def compute_derived_indicators(project: Dict[str, Any], reference_date: datetime = None) -> DerivedIndicators:
    if reference_date is None:
        # Reference date set to current evaluation snapshot date (e.g. 2026-09-01)
        reference_date = datetime(2026, 9, 1)

    orig_cost = float(project.get("original_cost", 0.0))
    rev_cost = float(project.get("revised_cost", orig_cost))
    expenditure = float(project.get("expenditure", 0.0))
    phys_prog = float(project.get("physical_progress", 0.0))
    fin_prog = float(project.get("financial_progress", 0.0))

    start_d = parse_date(str(project.get("start_date", "2023-01-01")))
    orig_comp_d = parse_date(str(project.get("original_completion_date", "2026-12-31")))
    exp_comp_d = parse_date(str(project.get("expected_completion_date", orig_comp_d.strftime("%Y-%m-%d"))))

    # 1. Cost Variance % & Amount
    cost_overrun_amt = rev_cost - orig_cost
    cost_var_pct = (cost_overrun_amt / orig_cost * 100.0) if orig_cost > 0 else 0.0

    # 2. Expenditure Ratio
    exp_ratio = (expenditure / rev_cost) if rev_cost > 0 else 0.0

    # 3. Progress Gap (Financial vs Physical Progress)
    progress_gap = fin_prog - phys_prog

    # 4. Schedule Durations & Variances
    planned_duration_months = max(diff_months(start_d, orig_comp_d), 1.0)
    revised_duration_months = max(diff_months(start_d, exp_comp_d), 1.0)
    schedule_variance_months = diff_months(orig_comp_d, exp_comp_d)

    # 5. Project Age & Time Elapsed Ratio
    project_age_months = max(diff_months(start_d, reference_date), 0.0)
    time_elapsed_ratio = min(project_age_months / planned_duration_months, 3.0)

    # 6. Schedule Pressure:
    # Ratio of remaining work to remaining time available until expected completion
    remaining_work = max(100.0 - phys_prog, 0.0)
    remaining_months = diff_months(reference_date, exp_comp_d)

    if remaining_work <= 0:
        schedule_pressure = 0.0
    elif remaining_months <= 0:
        # Deadline passed or is now, but work remaining!
        schedule_pressure = 3.0
    else:
        # Standard required velocity (% per month) vs original planned velocity
        planned_velocity = 100.0 / planned_duration_months
        required_velocity = remaining_work / remaining_months
        schedule_pressure = round(required_velocity / planned_velocity, 2)
        schedule_pressure = min(max(schedule_pressure, 0.0), 5.0)

    # 7. Progress-to-time efficiency
    # How much progress achieved per unit of time elapsed
    expected_progress_so_far = min(time_elapsed_ratio * 100.0, 100.0)
    if expected_progress_so_far > 0:
        progress_to_time_efficiency = round(phys_prog / expected_progress_so_far, 2)
    else:
        progress_to_time_efficiency = 1.0

    # 8. Project Size Band
    if orig_cost < 500:
        size_band = "Medium (< ₹500 Cr)"
    elif orig_cost <= 1000:
        size_band = "Major (₹500 - ₹1,000 Cr)"
    elif orig_cost <= 5000:
        size_band = "Mega (₹1,000 - ₹5,000 Cr)"
    else:
        size_band = "Ultra Mega (> ₹5,000 Cr)"

    return DerivedIndicators(
        cost_variance_pct=round(cost_var_pct, 2),
        cost_overrun_amount=round(cost_overrun_amt, 2),
        expenditure_ratio=round(exp_ratio, 3),
        progress_gap=round(progress_gap, 2),
        schedule_variance_months=round(schedule_variance_months, 1),
        schedule_pressure=round(schedule_pressure, 2),
        project_age_months=round(project_age_months, 1),
        planned_duration_months=round(planned_duration_months, 1),
        revised_duration_months=round(revised_duration_months, 1),
        time_elapsed_ratio=round(time_elapsed_ratio, 2),
        progress_to_time_efficiency=round(progress_to_time_efficiency, 2),
        size_band=size_band
    )
