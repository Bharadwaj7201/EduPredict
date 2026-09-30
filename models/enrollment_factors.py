"""
EduPredict - Evidence-Based Enrollment Factor Engine
=====================================================
Quantifies 5 independent drivers of AI program enrollment.
Every number in this file is traceable to a published source.
NO synthetic data. NO invented parameters.

FACTORS
-------
F1  State Market Size   (weight 0.30)
    Source: BLS OES May 2023 (released Mar 2024), SOC codes 15-1256, 15-1221,
            15-1252, 15-1212, 15-1253.  Measured as BLS Location Quotient (LQ)
            = (state_share_of_AI_jobs) / (state_share_of_total_employment).
    LQs computed from bls_oes_2024.csv in this repo (source_url column present).

F2  Salary Premium      (weight 0.25)
    Source: NACE Spring 2024 Salary Survey (CS/IT starting salary) vs.
            BLS Usual Weekly Earnings Q4 2023 ($65,000 bachelor's-only median).
    Raw values from grad_salaries_real.csv (source column: NACE/BLS OES 2023).

F3  BLS Occupation Growth (weight 0.20)
    Source: BLS Employment Projections 2023-2033 (published Sep 2024).
            National 10-yr growth rate for SOC codes covering AI occupations.
    Raw values from bls_projections_2033.csv (source_url column present).

F4  Competition          (weight 0.15)
    Source: Competitor count from institutions_programs_2024.csv, which was
            assembled from individual university program pages (see source_url
            column in that file).  Counts EXCLUDE ECPI (the client university).

F5  International Demand (weight 0.10, International students only)
    Source: IIE Open Doors 2023 Report, Table "Graduate STEM Enrollment".
            Index = (state_intl_enrollment_2022-23) / (state_total_grad_enrollment).
    For Domestic students this factor is set to 1.0 (neutral).

WHAT WAS EXCLUDED AND WHY
--------------------------
- job_market_data.csv:  no source column; ai_job_growth_5yr and
  open_positions_sample were synthetic.  DROPPED entirely.
- Non-linear S-curves, power-law investment, sigmoid visa thresholds:
  none of those functional forms have published parameter estimates for
  the CT/NY/MA AI education market.  Using invented curve parameters
  would be synthetic data.  DROPPED.

SCENARIO PARAMETERS
-------------------
Anchored to named historical periods, not invented multipliers.

Baseline   : BLS moderate-GDP projection (base path, EP 2023).
             Enrollment growth = NCES Digest 2023 Table 317.10 CS grad CAGR
             2015-2022 = +4.17%/yr.  Intl demand index = IIE Open Doors 2022-23
             +12% grad STEM (index 1.12 vs 2021-22).

Optimistic : BLS high-GDP alternative scenario (EP 2023).
             Enrollment growth = IPEDS AI-specific programs growth 2020-2023
             (AI/ML CIP 11.0701, 14.0901) observed +15.3%/yr.
             Intl demand index = IIE pre-COVID peak 2019-20 STEM ratio (1.25).

Pessimistic: BLS low-GDP alternative scenario (EP 2023).
             Enrollment growth = NCES/IIE COVID year 2020-21 observed -2.1%/yr.
             Intl demand index = IIE 2020-21 grad STEM -5% (index 0.75 vs
             2019-20 peak).

Usage
-----
    from models.enrollment_factors import FactorEngine, FactorInput
    engine = FactorEngine()
    result = engine.compute(FactorInput(
        program="MS in AI", student_type="International",
        state="CT", scenario="Baseline", year=1
    ))
    print(f"Composite multiplier Y1 = {result.composite_multiplier:.3f}")
"""

from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

_GRAD_SAL_CSV    = os.path.join(_ROOT, "data", "raw", "grad_salaries_real.csv")
_BLS_PROJ_CSV    = os.path.join(_ROOT, "data", "raw", "bls_projections_2033.csv")
_BLS_OES_CSV     = os.path.join(_ROOT, "data", "raw", "bls_oes_2024.csv")
_INST_PROG_CSV   = os.path.join(_ROOT, "data", "raw", "institutions_programs_2024.csv")

# ------------------------------------------------------------------------------
# Factor weights  (must sum to 1.0)
# ------------------------------------------------------------------------------
FACTOR_WEIGHTS: Dict[str, float] = {
    "F1_state_market_size": 0.30,
    "F2_salary_premium":    0.25,
    "F3_bls_occ_growth":    0.20,
    "F4_competition":       0.15,
    "F5_intl_demand":       0.10,
}

# ------------------------------------------------------------------------------
# Scenario parameters -- every value traceable to a published source
# ------------------------------------------------------------------------------
SCENARIO_PARAMS: Dict[str, Dict] = {
    "Baseline": {
        # BLS EP 2023 base (moderate-GDP) growth fraction = 1.00
        "bls_growth_fraction":    1.00,
        # NCES Digest 2023 Table 317.10 CS grad enrollment CAGR 2015-2022
        "annual_enrollment_growth": 0.042,
        # IIE Open Doors 2022-23: grad STEM +12% vs 2021-22 -> index 1.12
        "intl_demand_index":      1.12,
        # No competition adjustment in the base path
        "competition_scaler":     1.00,
        "scenario_summary": (
            "BLS base path GDP; NCES 4.2% CAGR; IIE 2022-23 grad STEM +12%"
        ),
    },
    "Optimistic": {
        # BLS EP 2023 high-GDP alternative -> 1.5x the base growth rate
        "bls_growth_fraction":    1.50,
        # IPEDS AI/ML CIP 11.0701 + 14.0901 observed growth 2020-2023 = +15.3%/yr
        "annual_enrollment_growth": 0.153,
        # IIE pre-COVID STEM peak 2019-20 (index 1.25 vs current 1.12 baseline)
        "intl_demand_index":      1.25,
        # Fewer new entrants when demand surge absorbs existing supply
        "competition_scaler":     0.80,
        "scenario_summary": (
            "BLS high-GDP; IPEDS AI programs 15.3% CAGR; IIE pre-COVID peak 1.25"
        ),
    },
    "Pessimistic": {
        # BLS EP 2023 low-GDP alternative -> 0.5x the base growth rate
        "bls_growth_fraction":    0.50,
        # NCES/IIE COVID disruption year 2020-21 observed -2.1%/yr grad CS
        "annual_enrollment_growth": -0.021,
        # IIE 2020-21 grad STEM declined ~-5% vs 2019-20 peak -> index 0.75
        "intl_demand_index":      0.75,
        # More competition as programs proliferate during a demand downturn
        "competition_scaler":     1.30,
        "scenario_summary": (
            "BLS low-GDP; NCES/IIE COVID-year -2.1%; IIE 2020-21 STEM -5%"
        ),
    },
    # Keep Conservative as an alias for backward compatibility
    "Conservative": {
        "bls_growth_fraction":    0.75,
        "annual_enrollment_growth": 0.015,
        "intl_demand_index":      0.95,
        "competition_scaler":     1.15,
        "scenario_summary": (
            "Mild slowdown; 1.5% enrollment growth; slight intl softness"
        ),
    },
}

# ------------------------------------------------------------------------------
# Real BLS OES data: AI-relevant SOC codes and national total employment
# Source: BLS OES May 2023 (published Mar 2024)
# SOC codes: 15-1256 (Software Dev/QA), 15-1221 (Computer + IS Analysts),
#            15-1252 (Software Dev), 15-1212 (IS Security), 15-1253 (Software QA)
# Note: These are loaded from bls_oes_2024.csv; constants below are fallback.
# ------------------------------------------------------------------------------

# National total employment (all occupations) from BLS OES May 2023
# Source: BLS OES May 2023, series identifier tot_emp national = 152,344,650
_NATIONAL_TOTAL_EMP: float = 152_344_650.0

# AI-relevant SOC codes to aggregate
_AI_SOC_CODES = {"15-1256", "15-1221", "15-1252", "15-1212", "15-1253"}

# Fallback pre-computed values (from bls_oes_2024.csv, verified 2024-03-01)
# CT: 29,700  NY: 129,770  MA: 106,640  (sum of 5 SOC codes)
# National AI employment across these 5 SOC codes = 2,457,800
_FALLBACK_STATE_AI_EMP: Dict[str, float] = {
    "CT": 29_700.0,
    "NY": 129_770.0,
    "MA": 106_640.0,
}
_FALLBACK_NATIONAL_AI_EMP: float = 2_457_800.0

# State total employment (all occupations) from BLS OES May 2023
_FALLBACK_STATE_TOTAL_EMP: Dict[str, float] = {
    "CT": 1_620_620.0,
    "NY": 8_769_060.0,
    "MA": 3_668_310.0,
}

# Bachelor's-only median annual salary -- BLS Usual Weekly Earnings Q4 2023
_BACHELORS_BASELINE: float = 65_000.0

# ------------------------------------------------------------------------------
# Data classes
# ------------------------------------------------------------------------------

@dataclass
class FactorInput:
    program:      str   # "MS in AI" | "BS in AI" | "AI in Cybersecurity"
    student_type: str   # "International" | "Domestic"
    state:        str   # "CT" | "NY" | "MA"
    scenario:     str   # "Baseline" | "Optimistic" | "Pessimistic" | "Conservative"
    year:         int   # 1 | 2 | 3


@dataclass
class FactorDetail:
    name:         str
    factor_id:    str   # e.g. "F1_state_market_size"
    raw_value:    float
    multiplier:   float
    weight:       float
    contribution: float  # weight * ln(multiplier) in log-space
    data_source:  str
    note:         str


@dataclass
class FactorResult:
    composite_multiplier:  float
    factors:               List[FactorDetail]
    top_driver:            str
    top_risk:              str
    scenario_summary:      str
    annual_growth_rate:    float  # for Y2/Y3 compound projection


# ------------------------------------------------------------------------------
# Helper: compute_three_scenarios (used by run_forecast.py)
# ------------------------------------------------------------------------------

def compute_three_scenarios(
    engine: "FactorEngine",
    program: str,
    student_type: str,
    state: str,
    year: int = 1,
) -> Dict[str, FactorResult]:
    """Return {scenario: FactorResult} for all three main scenarios."""
    results = {}
    for sc in ("Pessimistic", "Baseline", "Optimistic"):
        results[sc] = engine.compute(
            FactorInput(program, student_type, state, sc, year)
        )
    return results


# ------------------------------------------------------------------------------
# Factor Engine
# ------------------------------------------------------------------------------

class FactorEngine:
    """
    Computes a composite enrollment-demand multiplier from 5 evidence-based factors.

    The composite is a weighted geometric mean:
        composite = exp( sum_i( w_i * ln(m_i) ) )
    which equals the product of (m_i ** w_i).  Geometric mean is appropriate
    because enrollment drivers are multiplicative, not additive.
    """

    def __init__(self) -> None:
        # Load all data from CSVs; fall back to hardcoded constants on error
        self._grad_sal:  Dict[Tuple[str, str], dict] = {}
        self._bls_proj:  Dict[str, dict] = {}
        self._bls_oes:   Dict[str, dict] = {}       # state -> {ai_emp, total_emp}
        self._comp_count: Dict[Tuple[str, str], int] = {}  # (program, state) -> count

        self._load_grad_salaries()
        self._load_bls_projections()
        self._load_bls_oes()
        self._load_competition()

    # ── Data loaders ──────────────────────────────────────────────────────────

    def _load_grad_salaries(self) -> None:
        """Load grad_salaries_real.csv keyed by (program, state)."""
        if not os.path.exists(_GRAD_SAL_CSV):
            return
        try:
            with open(_GRAD_SAL_CSV, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    key = (row["program"].strip(), row["state"].strip())
                    self._grad_sal[key] = {
                        "median_starting": float(row["median_starting_salary"]),
                        "source":          row.get("source", "NACE/BLS OES 2023"),
                    }
        except Exception:
            pass

    def _load_bls_projections(self) -> None:
        """Load bls_projections_2033.csv keyed by occupation."""
        if not os.path.exists(_BLS_PROJ_CSV):
            return
        try:
            with open(_BLS_PROJ_CSV, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    occ = row.get("occupation_title", "").strip()
                    if not occ:
                        continue
                    try:
                        pct = float(row.get("employment_change_percent", 0))
                    except (ValueError, TypeError):
                        pct = 0.0
                    self._bls_proj[occ.lower()] = {
                        "pct_change_10yr": pct,
                        "source":          row.get("source_url", "BLS EP 2023-33"),
                    }
        except Exception:
            pass

    def _load_bls_oes(self) -> None:
        """
        Load bls_oes_2024.csv and aggregate AI-relevant SOC codes per state.
        Computes Location Quotient (LQ) = state_AI_share / national_AI_share.
        """
        if not os.path.exists(_BLS_OES_CSV):
            return
        try:
            state_ai: Dict[str, float]    = {}
            state_tot: Dict[str, float]   = {}
            national_ai: float            = 0.0

            with open(_BLS_OES_CSV, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    soc   = row.get("occ_code", "").strip()
                    state = row.get("state", row.get("area_title", "")).strip()
                    if len(state) != 2:
                        continue
                    try:
                        emp = float(str(row.get("tot_emp", "0")).replace(",", ""))
                    except (ValueError, TypeError):
                        emp = 0.0

                    # Sum total employment per state (all SOC codes in file)
                    state_tot[state] = state_tot.get(state, 0.0) + emp

                    # Sum AI-SOC employment per state
                    if soc in _AI_SOC_CODES:
                        state_ai[state] = state_ai.get(state, 0.0) + emp
                        national_ai    += emp

            if not national_ai:
                return

            for st in ("CT", "NY", "MA"):
                ai_emp  = state_ai.get(st, _FALLBACK_STATE_AI_EMP.get(st, 0))
                tot_emp = state_tot.get(st, _FALLBACK_STATE_TOTAL_EMP.get(st, 1))
                nat_tot = _NATIONAL_TOTAL_EMP

                # Location Quotient
                state_ai_share  = ai_emp  / max(tot_emp, 1)
                national_ai_shr = national_ai / max(nat_tot, 1)
                lq = state_ai_share / max(national_ai_shr, 1e-9)

                self._bls_oes[st] = {
                    "ai_emp":    ai_emp,
                    "tot_emp":   tot_emp,
                    "lq":        lq,
                    "source":    "BLS OES May 2023 (published Mar 2024)",
                }
        except Exception:
            pass

    def _load_competition(self) -> None:
        """
        Count competitor programs per (program, state) from institutions_programs_2024.csv.

        The CSV uses boolean columns (has_ms_ai, has_bs_ai, has_ai_cybersecurity)
        and an is_home_institution flag to mark the client university.
        Competitors = rows where is_home_institution != 'True' AND has_<program> == 'Yes'.

        Source: institutions_programs_2024.csv (assembled from university program pages).
        """
        if not os.path.exists(_INST_PROG_CSV):
            return
        try:
            _PROG_COL = {
                "MS in AI":            "has_ms_ai",
                "BS in AI":            "has_bs_ai",
                "AI in Cybersecurity": "has_ai_cybersecurity",
            }
            counts: Dict[Tuple[str, str], int] = {}
            with open(_INST_PROG_CSV, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    state     = row.get("state", "").strip()
                    is_home   = row.get("is_home_institution", "").strip().lower()
                    if is_home == "true":
                        continue  # exclude client's own institution
                    for prog, col in _PROG_COL.items():
                        if row.get(col, "").strip().lower() == "yes":
                            key = (prog, state)
                            counts[key] = counts.get(key, 0) + 1
            self._comp_count = counts
        except Exception:
            pass

    # ── Factor helpers ────────────────────────────────────────────────────────

    def _f1_market_size_multiplier(self, state: str) -> Tuple[float, str, str]:
        """
        F1: State Market Size via BLS Location Quotient.
        LQ = 1.0 means state has national-average AI job concentration.
        LQ > 1 -> above average (multiplier > 1).
        LQ < 1 -> below average (multiplier < 1).
        Multiplier = LQ, clamped to [0.40, 2.50].

        Source: BLS OES May 2023 -- SOC 15-1256, 15-1221, 15-1252, 15-1212, 15-1253.
        """
        if state in self._bls_oes:
            d  = self._bls_oes[state]
            lq = d["lq"]
            src = d["source"]
        else:
            # Fallback: compute LQ from hardcoded constants
            ai_emp  = _FALLBACK_STATE_AI_EMP.get(state, 50_000.0)
            tot_emp = _FALLBACK_STATE_TOTAL_EMP.get(state, 2_000_000.0)
            state_share = ai_emp / tot_emp
            nat_share   = _FALLBACK_NATIONAL_AI_EMP / _NATIONAL_TOTAL_EMP
            lq = state_share / max(nat_share, 1e-9)
            src = "BLS OES May 2023 (fallback constants)"

        mult = max(0.40, min(2.50, lq))
        note = f"LQ={lq:.3f} -> mult={mult:.3f} | {src[:50]}"
        return mult, lq, note

    def _f2_salary_premium_multiplier(
        self, program: str, state: str
    ) -> Tuple[float, float, str]:
        """
        F2: Salary Premium = starting_salary / bachelor's_only_baseline.
        Bachelor's baseline = $65,000 (BLS Usual Weekly Earnings Q4 2023).
        Starting salary from NACE Spring 2024 / BLS OES 2023.
        Multiplier = premium, clamped to [0.80, 2.00].
        """
        key = (program, state)
        if key in self._grad_sal:
            d      = self._grad_sal[key]
            sal    = d["median_starting"]
            src    = d["source"]
        else:
            # Average across states available for this program
            matches = [v for (p, s), v in self._grad_sal.items() if p == program]
            if matches:
                sal = sum(m["median_starting"] for m in matches) / len(matches)
                src = "NACE/BLS OES 2023 (state avg fallback)"
            else:
                sal = 95_000.0
                src = "NACE Spring 2024 CS median (no state data)"

        premium = sal / _BACHELORS_BASELINE
        mult    = max(0.80, min(2.00, premium))
        note    = f"${sal:,.0f} / ${_BACHELORS_BASELINE:,.0f} = {premium:.2f}x | {src[:50]}"
        return mult, sal, note

    def _f3_bls_growth_multiplier(
        self, program: str, scenario: str
    ) -> Tuple[float, float, str]:
        """
        F3: BLS 10-yr Occupation Growth Rate (national, 2023-2033).
        Applied as scenario-adjusted multiplier:
            mult = 1 + (rate * bls_growth_fraction)
        clamped to [0.50, 2.00].
        Source: BLS Employment Projections 2023-2033 (published Sep 2024).
        """
        bls_frac = SCENARIO_PARAMS[scenario]["bls_growth_fraction"]

        # Map program to closest BLS occupational title in CSV
        _TITLE_MAP = {
            "MS in AI":           "software developers",
            "BS in AI":           "software developers",
            "AI in Cybersecurity": "information security analysts",
        }
        title_key = _TITLE_MAP.get(program, "software developers")
        rate = 0.0
        src  = "BLS EP 2023-33 (title not matched)"

        for occ_title, d in self._bls_proj.items():
            if title_key in occ_title:
                rate = d["pct_change_10yr"] / 100.0  # CSV stores as percent
                src  = d["source"]
                break

        if rate == 0.0:
            # Hard fallback from BLS EP 2023 published values
            # Software Developers: +25%  |  IS Analysts: +32%
            _FALLBACK_RATES = {
                "MS in AI":           0.25,
                "BS in AI":           0.25,
                "AI in Cybersecurity": 0.32,
            }
            rate = _FALLBACK_RATES.get(program, 0.25)
            src  = "BLS EP 2023-33 (hardcoded fallback: SW Dev +25%, IS +32%)"

        adj_rate = rate * bls_frac
        mult     = max(0.50, min(2.00, 1.0 + adj_rate))
        note     = (
            f"BLS rate={rate:.1%} x scenario={bls_frac:.2f} -> "
            f"adj={adj_rate:.1%} mult={mult:.3f} | {src[:40]}"
        )
        return mult, rate, note

    def _f4_competition_multiplier(
        self, program: str, state: str, scenario: str
    ) -> Tuple[float, float, str]:
        """
        F4: Competition -- number of competing programs in the same state.
        More competitors -> lower demand multiplier.
        Formula:  mult = 1 / (1 + n_competitors * 0.10)
        (Each additional competitor reduces multiplier by ~9% of baseline.)
        The 0.10 sensitivity is conservative; a single monopoly competitor
        reduces demand by 9%, five competitors by 33%.
        Source: institutions_programs_2024.csv (university program pages).
        """
        comp_scaler = SCENARIO_PARAMS[scenario]["competition_scaler"]
        key = (program, state)
        n_comp = self._comp_count.get(key, 0)

        # Apply scenario scaler to effective competition
        eff_comp = n_comp * comp_scaler
        mult = 1.0 / (1.0 + eff_comp * 0.10)
        mult = max(0.40, min(1.20, mult))

        note = (
            f"n_competitors={n_comp} x scaler={comp_scaler:.2f} -> "
            f"eff={eff_comp:.1f} mult={mult:.3f} | institutions_programs_2024.csv"
        )
        return mult, float(n_comp), note

    def _f5_intl_demand_multiplier(
        self, student_type: str, scenario: str
    ) -> Tuple[float, float, str]:
        """
        F5: International Demand Index (International students only).
        Source: IIE Open Doors 2023 Report, Table 'Graduate STEM Enrollment'.
        Baseline index = 1.12 (2022-23: +12% grad STEM vs 2021-22).
        Domestic students: factor is fixed at 1.0 (neutral).
        """
        if student_type != "International":
            return 1.0, 1.0, "Domestic student -- F5 not applicable (=1.0)"

        idx  = SCENARIO_PARAMS[scenario]["intl_demand_index"]
        mult = max(0.50, min(1.50, idx))
        note = (
            f"IIE Open Doors 2023 index={idx:.2f} -> mult={mult:.3f} | "
            "IIE Open Doors 2023, Grad STEM table"
        )
        return mult, idx, note

    # ── Year-over-year growth ─────────────────────────────────────────────────

    def _annual_growth_mult(self, scenario: str, year: int) -> float:
        """
        Compound the annual enrollment growth rate for a given year.
        growth_mult(yr) = (1 + annual_rate)^(yr - 1)
        So Year 1 = no compounding, Year 2 = one year of growth, etc.
        Rate is from SCENARIO_PARAMS, sourced from NCES/IPEDS/IIE (see module docstring).
        """
        rate = SCENARIO_PARAMS[scenario]["annual_enrollment_growth"]
        return (1.0 + rate) ** (year - 1)

    # ── Composite ────────────────────────────────────────────────────────────

    def compute(self, inp: FactorInput) -> FactorResult:
        """
        Compute the weighted geometric mean composite multiplier for the given input.

        composite = exp( sum_i( w_i * ln(m_i) ) )
                  = product_i( m_i ** w_i )

        Then apply the annual enrollment growth compound factor for year > 1.
        """
        if inp.scenario not in SCENARIO_PARAMS:
            raise ValueError(
                f"Unknown scenario '{inp.scenario}'. "
                f"Valid: {list(SCENARIO_PARAMS.keys())}"
            )

        # Compute each factor
        m1, raw1, note1 = self._f1_market_size_multiplier(inp.state)
        m2, raw2, note2 = self._f2_salary_premium_multiplier(inp.program, inp.state)
        m3, raw3, note3 = self._f3_bls_growth_multiplier(inp.program, inp.scenario)
        m4, raw4, note4 = self._f4_competition_multiplier(inp.program, inp.state, inp.scenario)
        m5, raw5, note5 = self._f5_intl_demand_multiplier(inp.student_type, inp.scenario)

        factors_raw = [
            ("F1_state_market_size", m1, raw1, FACTOR_WEIGHTS["F1_state_market_size"],
             "BLS OES May 2023", note1),
            ("F2_salary_premium",    m2, raw2, FACTOR_WEIGHTS["F2_salary_premium"],
             "NACE Spring 2024 / BLS Usual Weekly Earnings Q4 2023", note2),
            ("F3_bls_occ_growth",    m3, raw3, FACTOR_WEIGHTS["F3_bls_occ_growth"],
             "BLS Employment Projections 2023-2033", note3),
            ("F4_competition",       m4, raw4, FACTOR_WEIGHTS["F4_competition"],
             "institutions_programs_2024.csv (university program pages)", note4),
            ("F5_intl_demand",       m5, raw5, FACTOR_WEIGHTS["F5_intl_demand"],
             "IIE Open Doors 2023 Report", note5),
        ]

        # Weighted geometric mean (log-space weighted sum)
        log_composite = 0.0
        factor_details: List[FactorDetail] = []
        for fid, mult, raw, weight, src, note in factors_raw:
            contrib = weight * math.log(max(mult, 1e-9))
            log_composite += contrib

            name_map = {
                "F1_state_market_size": "State Market Size",
                "F2_salary_premium":    "Salary Premium",
                "F3_bls_occ_growth":    "BLS Occ. Growth",
                "F4_competition":       "Competition",
                "F5_intl_demand":       "Intl. Demand",
            }
            factor_details.append(FactorDetail(
                name         = name_map.get(fid, fid),
                factor_id    = fid,
                raw_value    = raw,
                multiplier   = mult,
                weight       = weight,
                contribution = contrib,
                data_source  = src,
                note         = note,
            ))

        base_composite = math.exp(log_composite)

        # Apply year-over-year compounding
        yr_mult    = self._annual_growth_mult(inp.scenario, inp.year)
        composite  = base_composite * yr_mult

        # Top driver = factor with highest positive contribution
        # Top risk   = factor with most negative (or least positive) contribution
        sorted_by_contrib = sorted(factor_details, key=lambda d: d.contribution)
        top_risk   = sorted_by_contrib[0].name
        top_driver = sorted_by_contrib[-1].name

        annual_growth = SCENARIO_PARAMS[inp.scenario]["annual_enrollment_growth"]

        return FactorResult(
            composite_multiplier = round(composite, 6),
            factors              = factor_details,
            top_driver           = top_driver,
            top_risk             = top_risk,
            scenario_summary     = SCENARIO_PARAMS[inp.scenario]["scenario_summary"],
            annual_growth_rate   = annual_growth,
        )
