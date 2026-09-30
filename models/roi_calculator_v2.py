"""
EduPredict Pro — Student ROI Calculator v2
==========================================
Pure financial math. No ML, no synthetic data.
All salary inputs loaded from data/raw/bls_oes_2023_real.csv
and data/raw/grad_salaries_real.csv.

Usage:
    from models.roi_calculator_v2 import ROICalculatorV2, ROIInput
    calc = ROICalculatorV2()
    result = calc.calculate(ROIInput(...))
"""

from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_GRAD_SAL_PATH = os.path.join(_ROOT, "data", "raw", "grad_salaries_real.csv")
_BLS_OES_PATH  = os.path.join(_ROOT, "data", "raw", "bls_oes_2023_real.csv")

# Baseline for premium calculation — bachelor's-only median (BLS 2023)
# Source: BLS, Usual Weekly Earnings, Q4 2023 — bachelor's degree, full-time
BACHELORS_ONLY_BASELINE = 65_000  # annual, national median

# Salary growth rate assumed (conservative, matches BLS historical average)
ANNUAL_SALARY_GROWTH_RATE = 0.04  # 4% per year

# Standard federal loan repayment term
STANDARD_REPAYMENT_MONTHS = 120  # 10 years


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ROIInput:
    program: str          # "MS in AI" | "BS in AI" | "AI in Cybersecurity"
    state: str            # "CT" | "NY" | "MA"
    annual_tuition: float
    years_in_program: int
    living_costs_annual: float = 0.0
    loan_amount: float = 0.0
    loan_interest_rate: float = 0.065  # 6.5% — current federal grad PLUS rate


@dataclass
class ROIOutput:
    # Inputs echoed back
    program: str
    state: str
    annual_tuition: float
    years_in_program: int
    living_costs_annual: float
    loan_amount: float
    loan_interest_rate: float

    # Cost calculations
    total_tuition: float
    total_living_costs: float
    total_cost_of_degree: float

    # Salary data (sourced from real BLS / NACE data)
    expected_starting_salary: float
    p25_starting_salary: float
    p75_starting_salary: float
    salary_source: str

    # Loan repayment
    monthly_loan_payment: float
    total_loan_interest_paid: float
    total_loan_repayment: float

    # Break-even
    months_to_break_even: int
    years_to_break_even: float

    # Earnings trajectory (cumulative, pre-tax, after salary growth)
    earnings_at_5_years: float
    earnings_at_10_years: float

    # Premium vs. bachelor's-only baseline
    lifetime_premium_vs_bachelors_10yr: float
    lifetime_premium_vs_bachelors_5yr: float

    # Senior salary
    years_to_senior: int
    senior_median_salary: float

    # Metadata
    bachelors_only_baseline: float = BACHELORS_ONLY_BASELINE
    data_source_note: str = ""
    warnings: list = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Calculator
# ──────────────────────────────────────────────────────────────────────────────

class ROICalculatorV2:
    """
    Student ROI calculator backed by real BLS OES 2023 salary data
    and NACE 2024 new-grad benchmarks.
    """

    def __init__(self) -> None:
        self._grad_salaries: Dict[Tuple[str, str], dict] = {}
        self._load_grad_salaries()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_grad_salaries(self) -> None:
        """Load grad_salaries_real.csv keyed by (program, state)."""
        if not os.path.exists(_GRAD_SAL_PATH):
            return
        with open(_GRAD_SAL_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["program"].strip(), row["state"].strip())
                self._grad_salaries[key] = {
                    "median_starting":  float(row["median_starting_salary"]),
                    "p25":              float(row["p25_salary"]),
                    "p75":              float(row["p75_salary"]),
                    "years_to_senior":  int(row["years_to_senior"]),
                    "senior_median":    float(row["senior_median_salary"]),
                    "source":           row["source"],
                }

    def _get_salary_data(
        self, program: str, state: str
    ) -> Tuple[float, float, float, int, float, str]:
        """
        Return (median_starting, p25, p75, years_to_senior, senior_median, source).
        Raises ValueError if not found.
        """
        key = (program, state)
        if key not in self._grad_salaries:
            available = list(self._grad_salaries.keys())
            raise ValueError(
                f"No salary data for program='{program}', state='{state}'. "
                f"Available: {available}. "
                f"Run: python data/fetch_real_data.py"
            )
        d = self._grad_salaries[key]
        return (
            d["median_starting"],
            d["p25"],
            d["p75"],
            d["years_to_senior"],
            d["senior_median"],
            d["source"],
        )

    # ── Financial math ────────────────────────────────────────────────────────

    @staticmethod
    def _monthly_payment(
        principal: float, annual_rate: float, n_months: int
    ) -> float:
        """Standard amortizing loan monthly payment (M = P·r·(1+r)^n / ((1+r)^n − 1))."""
        if principal <= 0:
            return 0.0
        if annual_rate <= 0:
            return principal / n_months
        r = annual_rate / 12
        return principal * r * (1 + r) ** n_months / ((1 + r) ** n_months - 1)

    @staticmethod
    def _cumulative_earnings(
        starting_salary: float,
        growth_rate: float,
        n_years: int,
    ) -> float:
        """
        Sum of salaries over n_years with annual growth_rate.
        Year k salary = starting * (1 + growth_rate)^(k-1)
        """
        total = 0.0
        for k in range(1, n_years + 1):
            total += starting_salary * (1 + growth_rate) ** (k - 1)
        return total

    @staticmethod
    def _months_to_break_even(
        total_cost: float,
        monthly_starting_salary: float,
        monthly_loan_payment: float,
        annual_growth: float,
    ) -> int:
        """
        How many months until cumulative net income covers total_cost?
        Net income = monthly salary − monthly loan payment.
        Salary grows monthly at annual_growth/12.
        Cap at 600 months (50 years) to avoid infinite loops.
        """
        cumulative = 0.0
        monthly_growth = (1 + annual_growth) ** (1 / 12) - 1
        salary = monthly_starting_salary
        for month in range(1, 601):
            net = salary - monthly_loan_payment
            cumulative += max(net, 0)
            if cumulative >= total_cost:
                return month
            salary *= (1 + monthly_growth)
        return 600  # effectively never

    # ── Public API ────────────────────────────────────────────────────────────

    def calculate(self, inp: ROIInput) -> ROIOutput:
        warnings: list = []

        # 1. Salary data
        (
            median_start, p25, p75, years_to_senior, senior_median, sal_source
        ) = self._get_salary_data(inp.program, inp.state)

        # 2. Degree costs
        total_tuition      = inp.annual_tuition * inp.years_in_program
        total_living       = inp.living_costs_annual * inp.years_in_program
        total_cost_degree  = total_tuition + total_living

        # 3. Loan payments
        monthly_pmt = self._monthly_payment(
            inp.loan_amount, inp.loan_interest_rate, STANDARD_REPAYMENT_MONTHS
        )
        total_repayment       = monthly_pmt * STANDARD_REPAYMENT_MONTHS
        total_interest_paid   = max(total_repayment - inp.loan_amount, 0)

        if inp.loan_amount > total_cost_degree:
            warnings.append(
                "Loan amount exceeds total degree cost — double-check inputs."
            )

        # 4. Break-even
        monthly_salary = median_start / 12
        months_be = self._months_to_break_even(
            total_cost_degree, monthly_salary, monthly_pmt,
            ANNUAL_SALARY_GROWTH_RATE
        )
        years_be = round(months_be / 12, 1)

        # 5. Earnings trajectory (cumulative, post-graduation)
        earn_5yr  = self._cumulative_earnings(median_start, ANNUAL_SALARY_GROWTH_RATE, 5)
        earn_10yr = self._cumulative_earnings(median_start, ANNUAL_SALARY_GROWTH_RATE, 10)

        # 6. Bachelor's-only baseline trajectory
        bach_5yr  = self._cumulative_earnings(
            BACHELORS_ONLY_BASELINE, ANNUAL_SALARY_GROWTH_RATE, 5
        )
        bach_10yr = self._cumulative_earnings(
            BACHELORS_ONLY_BASELINE, ANNUAL_SALARY_GROWTH_RATE, 10
        )

        premium_5yr  = earn_5yr  - bach_5yr
        premium_10yr = earn_10yr - bach_10yr

        # 7. Tuition ROI check
        if total_tuition > earn_10yr * 0.5:
            warnings.append(
                "Tuition exceeds 50% of projected 10-year earnings — high cost scenario."
            )

        data_note = (
            f"Salary: {sal_source}. "
            f"Bachelor's baseline ${BACHELORS_ONLY_BASELINE:,} from BLS Usual Weekly Earnings Q4 2023. "
            f"Salary growth {ANNUAL_SALARY_GROWTH_RATE*100:.0f}%/yr (BLS historical avg). "
            f"Loan rate {inp.loan_interest_rate*100:.2f}% standard federal grad PLUS."
        )

        return ROIOutput(
            program=inp.program,
            state=inp.state,
            annual_tuition=inp.annual_tuition,
            years_in_program=inp.years_in_program,
            living_costs_annual=inp.living_costs_annual,
            loan_amount=inp.loan_amount,
            loan_interest_rate=inp.loan_interest_rate,
            total_tuition=total_tuition,
            total_living_costs=total_living,
            total_cost_of_degree=total_cost_degree,
            expected_starting_salary=median_start,
            p25_starting_salary=p25,
            p75_starting_salary=p75,
            salary_source=sal_source,
            monthly_loan_payment=monthly_pmt,
            total_loan_interest_paid=total_interest_paid,
            total_loan_repayment=total_repayment,
            months_to_break_even=months_be,
            years_to_break_even=years_be,
            earnings_at_5_years=earn_5yr,
            earnings_at_10_years=earn_10yr,
            lifetime_premium_vs_bachelors_5yr=premium_5yr,
            lifetime_premium_vs_bachelors_10yr=premium_10yr,
            years_to_senior=years_to_senior,
            senior_median_salary=senior_median,
            data_source_note=data_note,
            warnings=warnings,
        )

    def available_combinations(self) -> list:
        """Return list of (program, state) tuples with data."""
        return list(self._grad_salaries.keys())
