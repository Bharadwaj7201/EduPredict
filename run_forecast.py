"""
EduPredict - Full Forecast Runner
==================================
Runs the 11-factor enrollment engine across EVERY combination of:
  Program × Student Type × State × Term × Scenario (Pessimistic / Baseline / Optimistic)

Output sections
---------------
  1.  Factor detail table  - per-factor multipliers for one representative case
  2.  Scenario comparison  - Pessimistic vs Baseline vs Optimistic for every combo
  3.  3-year projections   - Year 1 / Year 2 / Year 3 per scenario
  4.  Top drivers & risks  - which factors move the needle most

Run:
    python run_forecast.py
    python run_forecast.py --state CT --program "MS in AI" --student International
"""

from __future__ import annotations

import argparse
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.enrollment_factors import (
    FactorEngine,
    FactorInput,
    SCENARIO_PARAMS,
    compute_three_scenarios,
)
from models.forecasting import EnrollmentForecaster, ForecastInput

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

PROGRAMS      = ["MS in AI", "BS in AI", "AI in Cybersecurity"]
STUDENT_TYPES = ["International", "Domestic"]
STATES        = ["CT", "NY", "MA"]
TERMS         = ["FA26", "SP27", "FA28"]
SCENARIOS     = ["Pessimistic", "Baseline", "Optimistic"]

STATE_NAMES   = {"CT": "Connecticut", "NY": "New York", "MA": "Massachusetts"}
TERM_LABELS   = {"FA26": "Fall 2026", "SP27": "Spring 2027", "FA28": "Fall 2028"}

# Separator widths
W_WIDE  = 110
W_MID   = 80

# ──────────────────────────────────────────────────────────────────────────────
# Formatting helpers
# ──────────────────────────────────────────────────────────────────────────────

def _bar(multiplier: float, width: int = 20) -> str:
    """ASCII progress bar centred on 1.0."""
    norm = (multiplier - 0.40) / (2.10 - 0.40)   # map [0.40, 2.10] -> [0, 1]
    filled = int(norm * width)
    bar = ("#" * filled).ljust(width)
    return f"[{bar}] {multiplier:.3f}"


def _scenario_badge(sc: str) -> str:
    badges = {
        "Optimistic":  "^ OPTIMISTIC",
        "Baseline":    "o BASELINE  ",
        "Pessimistic": "v PESSIMISTIC",
        "Conservative":"d CONSERVATIVE",
    }
    return badges.get(sc, sc)


def _risk_emoji(risk: str) -> str:
    return {"low": "[G]", "medium": "[Y]", "high": "[R]"}.get(risk, "[?]")


# ──────────────────────────────────────────────────────────────────────────────
# Section 1 - Factor deep-dive for one combination
# ──────────────────────────────────────────────────────────────────────────────

def print_factor_detail(
    engine: FactorEngine,
    program: str,
    student_type: str,
    state: str,
    year: int = 1,
) -> None:
    print()
    print("=" * W_WIDE)
    print(f"  FACTOR ENGINE DETAIL BREAKDOWN")
    print(f"  Program: {program}  |  Student: {student_type}  |  "
          f"State: {STATE_NAMES[state]}  |  Year: {year}")
    print("=" * W_WIDE)

    header = (
        f"  {'Factor':<22} {'ID':<22} {'Raw Value':>12} "
        f"{'Multiplier':>12} {'Weight':>7} {'Contribution':>14}  {'Explanation'}"
    )
    print(header)
    print("-" * W_WIDE)

    for sc in SCENARIOS:
        result = engine.compute(FactorInput(program, student_type, state, sc, year))
        print(f"\n  {_scenario_badge(sc)}  -  composite = {result.composite_multiplier:.4f}")
        print(f"  {result.scenario_summary}")
        print()

        for d in result.factors:
            bar_str = _bar(d.multiplier, 16)
            contrib_str = f"{d.contribution:+.4f}"
            print(
                f"  {d.name:<22} {d.factor_id:<22} {d.raw_value:>12.2f} "
                f"  {bar_str}  {d.weight:>6.2f}  {contrib_str:>14}  "
                f"{d.note[:55]}"
            )

        print(f"\n  Top growth driver : {result.top_driver}")
        print(f"  Top risk factor   : {result.top_risk}")
        print("-" * W_WIDE)


# ──────────────────────────────────────────────────────────────────────────────
# Section 2 - Scenario comparison table (all combos)
# ──────────────────────────────────────────────────────────────────────────────

def print_scenario_comparison(forecaster: EnrollmentForecaster) -> None:
    print()
    print("=" * W_WIDE)
    print("  SCENARIO COMPARISON - Year-1 Enrollment Projections (all combinations)")
    print("=" * W_WIDE)

    hdr = (
        f"  {'Program':<22} {'Type':<14} {'State':<5} {'Term':<6}"
        f"  {'Pessimistic':>12}  {'Baseline':>9}  {'Optimistic':>10}"
        f"  {'Upside':>7}  {'Downside':>8}"
    )
    print(hdr)
    print("-" * W_WIDE)

    for prog in PROGRAMS:
        for st in STUDENT_TYPES:
            for state in STATES:
                for term in TERMS:
                    row: dict[str, int] = {}
                    for sc in SCENARIOS:
                        fi = ForecastInput(
                            program_type=prog,
                            student_type=st,
                            start_term=term,
                            scenario=sc,
                            state=state,
                        )
                        out = forecaster.forecast(fi)
                        row[sc] = out.year1_enrollment

                    base     = row["Baseline"]
                    upside   = row["Optimistic"] - base
                    downside = base - row["Pessimistic"]

                    print(
                        f"  {prog:<22} {st:<14} {state:<5} {term:<6}"
                        f"  {row['Pessimistic']:>12}  {base:>9}  {row['Optimistic']:>10}"
                        f"  +{upside:>5}  -{downside:>6}"
                    )
            print()   # blank line between programs × states


# ──────────────────────────────────────────────────────────────────────────────
# Section 3 - 3-year projections for every scenario
# ──────────────────────────────────────────────────────────────────────────────

def print_three_year_projections(forecaster: EnrollmentForecaster) -> None:
    print()
    print("=" * W_WIDE)
    print("  3-YEAR ENROLLMENT PROJECTIONS BY SCENARIO")
    print("  (Term = FA26, showing all Program × State × Student Type)")
    print("=" * W_WIDE)

    term = "FA26"

    for sc in SCENARIOS:
        print(f"\n  {_scenario_badge(sc)}")
        print(f"  {SCENARIO_PARAMS[sc]['scenario_summary'] if 'scenario_summary' in SCENARIO_PARAMS[sc] else ''}")

        hdr = (
            f"  {'Program':<22} {'Type':<14} {'State':<6}"
            f"  {'Y1':>6}  {'Y2':>6}  {'Y3':>6}  {'3yr Pool':>9}"
            f"  {'CAGR':>6}  {'Confidence':>11}  {'Risk':<8}"
        )
        print(hdr)
        print("  " + "-" * (W_WIDE - 4))

        for prog in PROGRAMS:
            for st in STUDENT_TYPES:
                for state in STATES:
                    fi  = ForecastInput(prog, st, term, sc, state)
                    out = forecaster.forecast(fi)
                    cagr = (out.year3_enrollment / max(out.year1_enrollment, 1)) ** 0.5 - 1
                    risk_badge = _risk_emoji(out.risk_level) + " " + out.risk_level.upper()
                    print(
                        f"  {prog:<22} {st:<14} {state:<6}"
                        f"  {out.year1_enrollment:>6}  {out.year2_enrollment:>6}"
                        f"  {out.year3_enrollment:>6}  {out.projected_pool:>9}"
                        f"  {cagr:>5.1%}  {out.confidence_score:>10.0%}  {risk_badge}"
                    )
            print()
    print("-" * W_WIDE)


# ──────────────────────────────────────────────────────────────────────────────
# Section 4 - Top drivers and risks ranked across all combos
# ──────────────────────────────────────────────────────────────────────────────

def print_driver_risk_analysis(engine: FactorEngine) -> None:
    print()
    print("=" * W_WIDE)
    print("  FACTOR INFLUENCE ANALYSIS - Which factors move enrollment the most?")
    print("  (Showing Year-1 factor composites across all combos, FA26)")
    print("=" * W_WIDE)

    from collections import defaultdict
    driver_count: dict[str, int] = defaultdict(int)
    risk_count:   dict[str, int] = defaultdict(int)

    # Aggregate across all combos
    rows = []
    for prog in PROGRAMS:
        for st in STUDENT_TYPES:
            for state in STATES:
                for sc in SCENARIOS:
                    res = engine.compute(FactorInput(prog, st, state, sc, 1))
                    driver_count[res.top_driver] += 1
                    risk_count[res.top_risk]     += 1
                    rows.append((prog, st, state, sc, res))

    # Sort by composite
    rows.sort(key=lambda r: r[4].composite_multiplier, reverse=True)

    print(f"\n  TOP-10 HIGHEST COMPOSITE MULTIPLIERS (Year 1)")
    print(f"  {'Program':<22} {'Type':<14} {'State':<5} {'Scenario':<14} "
          f"{'Composite':>10}  {'Top Driver':<22}  {'Top Risk'}")
    print("  " + "-" * 95)
    for prog, st, state, sc, res in rows[:10]:
        print(
            f"  {prog:<22} {st:<14} {state:<5} {sc:<14} "
            f"{res.composite_multiplier:>10.4f}  {res.top_driver:<22}  {res.top_risk}"
        )

    print(f"\n  BOTTOM-10 LOWEST COMPOSITE MULTIPLIERS (Year 1)")
    print(f"  {'Program':<22} {'Type':<14} {'State':<5} {'Scenario':<14} "
          f"{'Composite':>10}  {'Top Driver':<22}  {'Top Risk'}")
    print("  " + "-" * 95)
    for prog, st, state, sc, res in rows[-10:]:
        print(
            f"  {prog:<22} {st:<14} {state:<5} {sc:<14} "
            f"{res.composite_multiplier:>10.4f}  {res.top_driver:<22}  {res.top_risk}"
        )

    print(f"\n  FACTOR FREQUENCY AS TOP GROWTH DRIVER (Year 1, all combos):")
    for name, cnt in sorted(driver_count.items(), key=lambda x: -x[1]):
        bar = "#" * cnt
        print(f"    {name:<24} {bar} ({cnt})")

    print(f"\n  FACTOR FREQUENCY AS TOP RISK (Year 1, all combos):")
    for name, cnt in sorted(risk_count.items(), key=lambda x: -x[1]):
        bar = "#" * cnt
        print(f"    {name:<24} {bar} ({cnt})")


# ──────────────────────────────────────────────────────────────────────────────
# Section 5 - International vs Domestic visa sensitivity analysis
# ──────────────────────────────────────────────────────────────────────────────

def print_visa_analysis(engine: FactorEngine, forecaster: EnrollmentForecaster) -> None:
    print()
    print("=" * W_WIDE)
    print("  VISA / IMMIGRATION POLICY IMPACT (International vs Domestic, Year 1)")
    print("=" * W_WIDE)

    term = "FA26"
    hdr = (
        f"  {'Program':<22} {'State':<6} {'Scenario':<14}"
        f"  {'Intl Y1':>8}  {'Dom Y1':>7}  {'Intl/Dom':>8}  {'Visa mult':>9}"
    )
    print(hdr)
    print("  " + "-" * 80)

    for sc in SCENARIOS:
        for prog in PROGRAMS:
            for state in STATES:
                fi_i = ForecastInput(prog, "International", term, sc, state)
                fi_d = ForecastInput(prog, "Domestic",      term, sc, state)
                oi   = forecaster.forecast(fi_i)
                od   = forecaster.forecast(fi_d)

                ri   = engine.compute(FactorInput(prog, "International", state, sc, 1))
                visa_factor = next(
                    (f.multiplier for f in ri.factors if "Intl" in f.name), 1.0
                )
                ratio = oi.year1_enrollment / max(od.year1_enrollment, 1)

                print(
                    f"  {prog:<22} {state:<6} {sc:<14}"
                    f"  {oi.year1_enrollment:>8}  {od.year1_enrollment:>7}"
                    f"  {ratio:>8.2f}x  {visa_factor:>9.3f}"
                )
        print()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="EduPredict full forecast runner")
    parser.add_argument("--state",   default=None, help="Filter to one state (CT/NY/MA)")
    parser.add_argument("--program", default=None, help='Filter to one program')
    parser.add_argument("--student", default=None, help="International or Domestic")
    parser.add_argument("--section", default="all",
                        help="all | detail | compare | years | drivers | visa")
    args = parser.parse_args()

    print()
    print("+" + "=" * (W_WIDE - 2) + "+")
    print("|" + "  EduPredict Pro - Multi-Factor Enrollment Forecasting Engine".center(W_WIDE - 2) + "|")
    print("|" + "  5 Evidence-Based Factors  |  3 Scenarios  |  Zero Synthetic Data".center(W_WIDE - 2) + "|")
    print("+" + "=" * (W_WIDE - 2) + "+")
    print()
    print("  EVIDENCE-BASED FACTORS (every number traceable to a published source)")
    print("    F1  State Market Size  - BLS Location Quotient (BLS OES May 2023)")
    print("                            SOC 15-1256/15-1221/15-1252/15-1212/15-1253")
    print("    F2  Salary Premium     - NACE Spring 2024 vs $65k BLS Q4-2023 baseline")
    print("    F3  BLS Occ. Growth    - BLS Employment Projections 2023-2033 (Sep 2024)")
    print("                            SW Dev +25%  |  IS Analysts +32%  (national)")
    print("    F4  Competition        - Count from institutions_programs_2024.csv")
    print("                            CT: 1 MS-AI  |  NY: 5 MS-AI  |  MA: 5 MS-AI")
    print("    F5  Intl. Demand       - IIE Open Doors 2023, grad STEM table")
    print("                            International only; Domestic = 1.0 (neutral)")
    print()
    print("  SCENARIOS (anchored to named historical periods)")
    print("    Pessimistic  - BLS low-GDP alt; NCES/IIE COVID yr -2.1%/yr; IIE STEM idx 0.75")
    print("    Baseline     - BLS base path; NCES CS grad CAGR 4.2%; IIE 2022-23 STEM 1.12")
    print("    Optimistic   - BLS high-GDP alt; IPEDS AI 15.3%/yr; IIE pre-COVID STEM 1.25")
    print()

    engine     = FactorEngine()
    forecaster = EnrollmentForecaster()

    # Apply CLI filters
    programs = [args.program] if args.program else PROGRAMS
    states   = [args.state]   if args.state   else STATES
    students = [args.student] if args.student else STUDENT_TYPES

    s = args.section.lower()

    # Detail view defaults to MS in AI / International / CT
    detail_prog = programs[0]
    detail_st   = students[0]
    detail_state = states[0]

    if s in ("all", "detail"):
        print_factor_detail(engine, detail_prog, detail_st, detail_state, year=1)

    if s in ("all", "compare"):
        print_scenario_comparison(forecaster)

    if s in ("all", "years"):
        print_three_year_projections(forecaster)

    if s in ("all", "drivers"):
        print_driver_risk_analysis(engine)

    if s in ("all", "visa"):
        print_visa_analysis(engine, forecaster)

    print()
    print("=" * W_WIDE)
    print("  Run complete. All projections saved to screen.")
    print("  To filter: python run_forecast.py --state CT --program 'MS in AI'")
    print("=" * W_WIDE)
    print()


if __name__ == "__main__":
    main()
