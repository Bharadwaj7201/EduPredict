"""
EduPredict Pro — BI Dashboard
==============================
Run:  python app_dashboard.py
Open: http://localhost:5050
"""

from __future__ import annotations

import csv
import json
import os
import sys
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from models.roi_calculator_v2 import ROICalculatorV2, ROIInput
from models.forecasting import quick_forecast
from models.enrollment_factors import FactorEngine, FactorInput

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

# ── File paths (all resolved from config) ─────────────────────────────────────
RAW          = os.path.join(os.path.dirname(__file__), "data", "raw")

def _p(filename: str) -> str:
    return os.path.join(RAW, filename)

BLS_OES_PATH    = _p("bls_oes_2024.csv")
BLS_PROJ_PATH   = _p("bls_projections_2033.csv")
EMPLOYERS_PATH  = _p("employers_2024.csv")
GRAD_SAL_PATH   = _p("grad_salaries_2024.csv")
IPEDS_PATH      = _p("ipeds_institutions.csv")
INST_PROG_PATH  = _p("institutions_programs_2024.csv")

# Legacy fallbacks (Phase 1 files)
BLS_OES_LEGACY   = _p("bls_oes_2023_real.csv")
GRAD_SAL_LEGACY  = _p("grad_salaries_real.csv")
EMP_LEGACY       = _p("employers_real.csv")


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _read_csv(path: str, fallback: Optional[str] = None) -> List[Dict[str, str]]:
    """Read a CSV, falling back to legacy path if primary is absent."""
    for p in [path, fallback]:
        if p and os.path.exists(p):
            with open(p, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            if rows:
                return rows
    return []


def _f(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _i(val: Any, default: int = 0) -> int:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return default


def _pending(val: str) -> bool:
    return not val or val.strip().upper() in ("", "PENDING", "NULL", "NONE")


# ══════════════════════════════════════════════════════════════════════════════
# Data loading
# ══════════════════════════════════════════════════════════════════════════════

def load_all_data() -> dict:
    oes_rows   = _read_csv(BLS_OES_PATH, BLS_OES_LEGACY)
    proj_rows  = _read_csv(BLS_PROJ_PATH)
    emp_rows   = _read_csv(EMPLOYERS_PATH, EMP_LEGACY)
    sal_rows   = _read_csv(GRAD_SAL_PATH, GRAD_SAL_LEGACY)
    inst_rows  = _read_csv(IPEDS_PATH)
    prog_rows  = _read_csv(INST_PROG_PATH)

    missing = [
        label for label, path in [
            ("BLS OES 2024",             BLS_OES_PATH),
            ("BLS Projections 2033",     BLS_PROJ_PATH),
            ("Employer directory 2024",  EMPLOYERS_PATH),
            ("Grad salaries 2024",       GRAD_SAL_PATH),
            ("Institution programs",     INST_PROG_PATH),
        ]
        if not os.path.exists(path)
    ]

    # ── HERO STATS ────────────────────────────────────────────────────────────
    # Tri-state share of national computer & math employment ≈ 8% (BLS OES 2023)
    TRI_STATE_SHARE = 0.08
    total_openings_nat = sum(_i(r.get("openings_annual", 0)) for r in proj_rows)
    total_openings     = int(total_openings_nat * TRI_STATE_SHARE)

    AI_SOCS    = {"15-1252", "15-1256", "15-1221", "15-1253"}
    CYBER_SOCS = {"15-1212"}

    ms_ai_sals = [
        _f(r.get("median_starting") or r.get("median_starting_salary", 0))
        for r in sal_rows
        if r.get("program", "").strip() == "MS in AI"
    ]
    median_ms_ai = int(sum(ms_ai_sals) / len(ms_ai_sals)) if ms_ai_sals else 0

    ai_proj = [r for r in proj_rows if r.get("soc_code", "").strip() in AI_SOCS]
    emp23   = sum(_i(r.get("emp_2023", 0)) for r in ai_proj)
    emp33   = sum(_i(r.get("emp_2033", 0)) for r in ai_proj)
    pct_growth = round((emp33 - emp23) / emp23 * 100, 1) if emp23 else 0

    num_inst = len(inst_rows)

    hero = {
        "total_openings_tristate": total_openings,
        "median_ms_ai_salary":     median_ms_ai,
        "pct_growth_ai":           pct_growth,
        "num_institutions":        num_inst,
        "tristate_share_note":     (
            f"CT+NY+MA approx. 8% of national Computer & Math employment — "
            f"{config.BLS_SOURCE}"
        ),
    }

    # ── JOB MARKET ────────────────────────────────────────────────────────────
    state_emp: Dict[str, Dict[str, int]] = {
        s: {"ai": 0, "cyber": 0} for s in ["CT", "NY", "MA"]
    }
    for r in oes_rows:
        st  = r.get("state", "").strip()
        soc = r.get("soc_code", "").strip()
        emp = _i(r.get("tot_emp", 0))
        if st in state_emp:
            if soc in AI_SOCS:
                state_emp[st]["ai"] += emp
            if soc in CYBER_SOCS:
                state_emp[st]["cyber"] += emp

    # salary by SOC — keyed by soc_code
    salary_by_soc: Dict[str, dict] = {}
    for r in oes_rows:
        soc   = r.get("soc_code", "").strip()
        st    = r.get("state", "").strip()
        med   = _f(r.get("a_median", 0))
        name  = r.get("occupation_title") or r.get("occupation_name", soc)
        short = r.get("short_label", name[:16])
        if soc not in salary_by_soc:
            salary_by_soc[soc] = {"name": name, "short": short,
                                   "CT": 0, "NY": 0, "MA": 0}
        salary_by_soc[soc][st] = med

    # ── SALARY DEEP DIVE ──────────────────────────────────────────────────────
    salary_table = []
    for soc, d in sorted(salary_by_soc.items(), key=lambda x: -x[1].get("NY", 0)):
        proj = next(
            (r for r in proj_rows if r.get("soc_code", "").strip() == soc), {}
        )
        salary_table.append({
            "soc_code":   soc,
            "role":       d["name"],
            "short":      d["short"],
            "ct_median":  int(d.get("CT", 0)),
            "ny_median":  int(d.get("NY", 0)),
            "ma_median":  int(d.get("MA", 0)),
            "growth_pct": _f(proj.get("change_pct", 0)),
            "new_jobs":   _i(proj.get("change_num", 0)),
        })

    # ── EMPLOYERS ─────────────────────────────────────────────────────────────
    employers_json = []
    for r in emp_rows:
        # support both 'lon' (legacy) and 'lng' (new schema)
        lng = _f(r.get("lng") or r.get("lon", 0))
        employers_json.append({
            "company_name":             r.get("company_name", ""),
            "state":                    r.get("state", ""),
            "city":                     r.get("city", ""),
            "lat":                      _f(r.get("lat", 0)),
            "lng":                      lng,
            "sector":                   r.get("sector", ""),
            "company_type":             r.get("company_type", ""),
            "hires_new_grads":          r.get("hires_new_grads", ""),
            "approx_annual_new_grad_hires": r.get("approx_annual_new_grad_hires", ""),
            "careers_url":              r.get("careers_url", ""),
            "founded_year":             r.get("founded_year", ""),
            "hq_address":               r.get("hq_address_approx", ""),
        })

    # Sort employers by annual new grad hires descending (numeric lower bound)
    def _hire_lower(emp: dict) -> int:
        val = emp.get("approx_annual_new_grad_hires", "") or ""
        if not val or val.strip() == "":
            return 0
        try:
            return int(str(val).split("-")[0].strip())
        except ValueError:
            return 0

    employers_json.sort(key=_hire_lower, reverse=True)

    # ── INSTITUTIONS ──────────────────────────────────────────────────────────
    institutions_json = []
    for r in inst_rows:
        institutions_json.append({
            "unitid":           r.get("unitid", ""),
            "institution_name": r.get("institution_name", ""),
            "state":            r.get("state", ""),
            "institution_type": r.get("institution_type", ""),
            "sector":           r.get("sector", ""),
        })

    # Merge program info into institutions_json
    prog_by_name = {r.get("institution_name", "").strip(): r for r in prog_rows}
    for inst in institutions_json:
        prog = prog_by_name.get(inst["institution_name"].strip(), {})
        inst["has_ms_ai"]           = prog.get("has_ms_ai", "PENDING")
        inst["has_bs_ai"]           = prog.get("has_bs_ai", "PENDING")
        inst["has_ai_cyber"]        = prog.get("has_ai_cybersecurity", "PENDING")
        inst["ai_program_name"]     = prog.get("ai_program_name", "PENDING")
        inst["program_url"]         = prog.get("program_url", "")
        inst["tuition_per_credit"]  = prog.get("tuition_per_credit_grad", "PENDING")
        inst["total_ms_credits"]    = prog.get("total_ms_credits", "PENDING")
        inst["program_launched"]    = prog.get("program_launched_year", "PENDING")
        inst["notable_feature"]     = prog.get("notable_feature", "")
        inst["is_home_institution"] = prog.get("is_home_institution", "False") == "True"

    # ── GRAD SALARIES (for ROI tab) ────────────────────────────────────────────
    grad_salaries_json = []
    for r in sal_rows:
        grad_salaries_json.append({
            "program":          r.get("program", ""),
            "state":            r.get("state", ""),
            "median_starting":  _f(r.get("median_starting") or r.get("median_starting_salary", 0)),
            "p25":              _f(r.get("p25_starting") or r.get("p25_salary", 0)),
            "p75":              _f(r.get("p75_starting") or r.get("p75_salary", 0)),
            "median_5yr":       _f(r.get("median_5yr") or r.get("senior_median_salary", 0)),
            "source":           r.get("source", ""),
        })

    # ── DISPLAY METADATA ──────────────────────────────────────────────────────
    meta = {
        "data_year":       config.DATA_YEAR,
        "bls_source":      config.BLS_SOURCE,
        "bls_proj_source": config.BLS_PROJ_SOURCE,
        "nace_source":     config.NACE_SOURCE,
        "employer_date":   config.EMPLOYER_DATA_DATE,
        "last_updated":    config.LAST_UPDATED,
    }

    return {
        "hero":          hero,
        "job_market":    {"state_employment": state_emp, "salary_by_soc": salary_by_soc},
        "salary_deep":   {"salary_table": salary_table, "grad_salaries": grad_salaries_json},
        "employers":     employers_json,
        "institutions":  institutions_json,
        "missing_data":  missing,
        "data_loaded":   len(missing) == 0,
        "meta":          meta,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def dashboard():
    data      = load_all_data()
    data_json = json.dumps(data, ensure_ascii=False)
    return render_template("dashboard.html", data_json=data_json, data=data)


@app.route("/api/roi", methods=["POST"])
def api_roi():
    body = request.get_json(force=True)
    try:
        inp = ROIInput(
            program=body["program"],
            state=body["state"],
            annual_tuition=float(body["annual_tuition"]),
            years_in_program=int(body["years_in_program"]),
            living_costs_annual=float(body.get("living_costs_annual", 0)),
            loan_amount=float(body.get("loan_amount", 0)),
            loan_interest_rate=float(body.get("loan_interest_rate", 0.065)),
        )
        calc = ROICalculatorV2()
        out  = calc.calculate(inp)
        return jsonify({
            "ok": True,
            "total_tuition":            out.total_tuition,
            "total_living_costs":       out.total_living_costs,
            "total_cost_of_degree":     out.total_cost_of_degree,
            "expected_starting_salary": out.expected_starting_salary,
            "p25_starting_salary":      out.p25_starting_salary,
            "p75_starting_salary":      out.p75_starting_salary,
            "monthly_loan_payment":     round(out.monthly_loan_payment, 2),
            "total_loan_interest":      round(out.total_loan_interest_paid, 2),
            "months_to_break_even":     out.months_to_break_even,
            "years_to_break_even":      out.years_to_break_even,
            "earnings_at_5_years":      round(out.earnings_at_5_years, 0),
            "earnings_at_10_years":     round(out.earnings_at_10_years, 0),
            "premium_5yr":              round(out.lifetime_premium_vs_bachelors_5yr, 0),
            "premium_10yr":             round(out.lifetime_premium_vs_bachelors_10yr, 0),
            "years_to_senior":          out.years_to_senior,
            "senior_median_salary":     out.senior_median_salary,
            "salary_5yr":               round(out.expected_starting_salary * (1.06 ** 5), 0),
            "salary_10yr":              round(out.expected_starting_salary * (1.06 ** 10), 0),
            "salary_source":            out.salary_source,
            "data_source_note":         out.data_source_note,
            "warnings":                 out.warnings,
        })
    except (KeyError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/light")
def dashboard_light():
    data      = load_all_data()
    data_json = json.dumps(data, ensure_ascii=False)
    return render_template("dashboard_light.html", data_json=data_json, data=data)


@app.route("/api/enroll-forecast", methods=["POST"])
def api_enroll_forecast():
    """ARIMA enrollment forecast with 3-scenario comparison and 5-factor breakdown."""
    body = request.get_json(force=True)
    program      = body.get("program", "MS in AI")
    student_type = body.get("student_type", "International")
    term         = body.get("term", "FA26")
    scenario     = body.get("scenario", "Baseline")
    state        = body.get("state", "CT")

    try:
        f = quick_forecast(program, student_type, term, scenario, state)

        # Factor breakdown for selected scenario (Year 1)
        engine = FactorEngine()
        fr = engine.compute(FactorInput(program, student_type, state, scenario, 1))

        # All 3 scenarios for comparison
        scenarios_out = []
        for sc in ("Pessimistic", "Baseline", "Optimistic"):
            sf = quick_forecast(program, student_type, term, sc, state)
            scenarios_out.append({
                "scenario":   sc,
                "year1":      sf.year1_enrollment,
                "year2":      sf.year2_enrollment,
                "year3":      sf.year3_enrollment,
                "pool":       sf.projected_pool,
                "confidence": round(sf.confidence_score, 2),
                "year1_low":  sf.year1_low,
                "year1_high": sf.year1_high,
            })

        return jsonify({
            "ok": True,
            "forecast": {
                "year1":          f.year1_enrollment,
                "year2":          f.year2_enrollment,
                "year3":          f.year3_enrollment,
                "year1_low":      f.year1_low,
                "year1_high":     f.year1_high,
                "pool":           f.projected_pool,
                "confidence":     f.confidence_score,
                "confidence_pct": int(f.confidence_score * 100),
                "risk_level":     f.risk_level,
                "growth_rate":    round(f.growth_rate * 100, 1),
                "warning_flags":  f.warning_flags,
            },
            "factors": [
                {
                    "name":             fd.name,
                    "multiplier":       round(fd.multiplier, 3),
                    "weight":           round(fd.weight, 2),
                    "contribution_pct": round(fd.contribution * 100, 2),
                    "source":           fd.data_source,
                    "note":             fd.note,
                }
                for fd in fr.factors
            ],
            "top_driver":       fr.top_driver,
            "top_risk":         fr.top_risk,
            "scenario_summary": fr.scenario_summary,
            "scenarios":        scenarios_out,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/data")
def api_data():
    return jsonify(load_all_data())


if __name__ == "__main__":
    print(f"EduPredict Pro Dashboard — http://localhost:5050")
    print(f"Data year: {config.DATA_YEAR} | Source: {config.BLS_SOURCE}")
    missing = [f for f in [BLS_OES_PATH, BLS_PROJ_PATH, EMPLOYERS_PATH] if not os.path.exists(f)]
    if missing:
        print(f"WARNING: Missing data files: {missing}")
        print("Run:  python data/fetch_real_data.py")
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False)
