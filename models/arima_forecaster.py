"""
EduPredict Pro - ARIMA Enrollment Forecasting Engine (Phase 3)
==============================================================
Fits ARIMA time-series models on 11-year historical enrollment data
(2015-2025) for comparable AI/Cybersecurity programs in the Northeast,
then applies the 5-factor engine multiplier for state/scenario adjustments.

Historical data sources
-----------------------
2015-2019  NCES Digest 2023 Table 317.10 — CS grad enrollment CAGR +4.2%/yr
2020       IPEDS 2020-21 — national grad enrollment impact: −2.1%
2021       IIE Open Doors 2023 — post-COVID grad STEM recovery +8%
2022-2023  IPEDS CIP 11.0701/14.0901 AI programs 2020-2023 CAGR = +15.3%/yr
2024       IIE Open Doors 2023 — intl grad STEM +12% (2022-23 vs 2021-22)
2025       Early enrollment data + trend projection (current-year estimate)

Architecture
------------
Priority 1 (statsmodels available): ARIMA(p,d,q) with auto-order via AIC
Priority 2 (numpy only):            OLS log-linear trend with bootstrap CI
Priority 3 (pure Python):           CAGR-based exponential projection

In all cases the point forecast and confidence interval are adjusted by
the factor engine's relative multiplier:

    adj_ratio(year) = factor_composite(target state, scenario, year)
                    / factor_composite("CT", "Baseline", year)

This ensures state and scenario differences are preserved while the
time-series backbone drives the absolute enrollment level.
"""

from __future__ import annotations

import csv
import math
import os
import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

warnings.filterwarnings("ignore")

# ── Optional heavy dependencies ──────────────────────────────────────────────

try:
    import numpy as np
    _NP = True
except ImportError:
    np = None  # type: ignore
    _NP = False

try:
    from statsmodels.tsa.arima.model import ARIMA as _ARIMA
    _SM = _NP  # statsmodels useless without numpy
except ImportError:
    _ARIMA = None  # type: ignore
    _SM = False

# ── Paths ─────────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HIST_CSV = os.path.join(_ROOT, "data", "raw", "ipeds_enrollment_historical.csv")

# ── Historical enrollment constants (also embedded as fallback) ───────────────
# Source: ipeds_enrollment_historical.csv  (see that file for per-row citations)
# Columns correspond to academic years 2015 … 2025 (11 observations).

_BUILT_IN_SERIES: Dict[Tuple[str, str], List[int]] = {
    ("MS in AI",            "International"):  [20, 21, 22, 23, 24, 23, 25, 30, 36, 42, 45],
    ("MS in AI",            "Domestic"):       [15, 16, 17, 18, 18, 18, 19, 22, 26, 32, 35],
    ("BS in AI",            "International"):  [22, 23, 24, 25, 26, 25, 27, 33, 40, 47, 50],
    ("BS in AI",            "Domestic"):       [30, 32, 34, 36, 38, 37, 40, 47, 55, 58, 60],
    ("AI in Cybersecurity", "International"):  [18, 19, 20, 21, 22, 21, 23, 27, 32, 37, 40],
    ("AI in Cybersecurity", "Domestic"):       [22, 24, 25, 26, 27, 27, 29, 34, 39, 43, 45],
}

_HIST_YEARS = list(range(2015, 2026))  # 2015-2025

# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class ARIMAResult:
    """Three-year ARIMA enrollment forecast with 95 % confidence intervals."""
    # Point forecasts (pre-adjustment — CT/Baseline units)
    year1_base: float
    year2_base: float
    year3_base: float
    # 95 % CI bounds (pre-adjustment)
    year1_ci_low:  float
    year1_ci_high: float
    year3_ci_low:  float
    year3_ci_high: float
    # Diagnostics
    model_order:  Tuple[int, int, int]   # (p, d, q) used
    aic:          float
    n_obs:        int
    method:       str  # "arima" | "ols_log_linear" | "cagr"
    available:    bool

    # ── Derived helpers ───────────────────────────────────────────────────────

    @property
    def ci_width_ratio(self) -> float:
        """Width of Year-1 CI relative to point forecast (lower = more precise)."""
        span = self.year1_ci_high - self.year1_ci_low
        return span / max(self.year1_base, 1.0)

    def apply_adjustment(
        self,
        adj1: float,
        adj2: float,
        adj3: float,
        term_factor: float,
    ) -> Tuple[int, int, int, int, int, int, int]:
        """
        Return (y1, y2, y3, y1_low, y1_high, y3_low, y3_high)
        after applying per-year factor-engine ratios and term factor.
        """
        scale = term_factor
        y1     = max(0, int(self.year1_base  * adj1 * scale))
        y2     = max(0, int(self.year2_base  * adj2 * scale))
        y3     = max(0, int(self.year3_base  * adj3 * scale))
        y1_lo  = max(0, int(self.year1_ci_low  * adj1 * scale))
        y1_hi  = max(0, int(self.year1_ci_high * adj1 * scale))
        y3_lo  = max(0, int(self.year3_ci_low  * adj3 * scale))
        y3_hi  = max(0, int(self.year3_ci_high * adj3 * scale))
        return y1, y2, y3, y1_lo, y1_hi, y3_lo, y3_hi


# ── Main forecasting class ────────────────────────────────────────────────────

class ARIMAForecaster:
    """
    Fits per-(program, student_type) ARIMA models and returns 3-year forecasts.

    Results are cached after the first call — the class is cheap to construct.
    """

    def __init__(self) -> None:
        self._series: Dict[Tuple[str, str], List[int]] = {}
        self._cache:  Dict[Tuple[str, str], ARIMAResult] = {}
        self._load_csv()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_csv(self) -> None:
        """Load historical data from CSV; fall back to built-in constants."""
        if not os.path.exists(_HIST_CSV):
            self._series = dict(_BUILT_IN_SERIES)
            return

        raw: Dict[Tuple[str, str], Dict[int, int]] = {}
        try:
            with open(_HIST_CSV, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    prog  = row["program"].strip()
                    stype = row["student_type"].strip()
                    yr    = int(row["year"])
                    val   = int(row["annual_fa_cohort"])
                    key   = (prog, stype)
                    raw.setdefault(key, {})[yr] = val
        except Exception:
            self._series = dict(_BUILT_IN_SERIES)
            return

        for key, yr_map in raw.items():
            ordered = [yr_map[y] for y in sorted(yr_map)]
            if len(ordered) >= 5:
                self._series[key] = ordered

        # Merge any missing keys from built-in
        for key, vals in _BUILT_IN_SERIES.items():
            if key not in self._series:
                self._series[key] = vals

    # ── Public interface ──────────────────────────────────────────────────────

    def forecast(self, program: str, student_type: str) -> ARIMAResult:
        """Return cached ARIMA forecast for the given program + student type."""
        key = (program, student_type)
        if key in self._cache:
            return self._cache[key]

        series = self._series.get(key, _BUILT_IN_SERIES.get(key, [20, 22, 25, 30, 36, 42, 45]))
        result = self._fit(series)
        self._cache[key] = result
        return result

    def historical_series(self, program: str, student_type: str) -> List[int]:
        """Return raw historical enrollment series for the given combination."""
        key = (program, student_type)
        return list(self._series.get(key, _BUILT_IN_SERIES.get(key, [])))

    # ── Model fitting ─────────────────────────────────────────────────────────

    def _fit(self, series: List[int]) -> ARIMAResult:
        """Select and run the best available fitting method."""
        if _SM:
            result = self._fit_statsmodels(series)
            if result.available:
                return result
        if _NP:
            return self._fit_ols_log_linear(series)
        return self._fit_cagr(series)

    # ── Method 1: statsmodels ARIMA ───────────────────────────────────────────

    def _fit_statsmodels(self, series: List[int]) -> ARIMAResult:
        """Auto-select ARIMA(p,d,q) by AIC; forecast 3 steps ahead."""
        y = np.array(series, dtype=float)

        # Candidate orders — intentionally conservative for small samples
        _ORDERS = [(1, 1, 1), (0, 1, 1), (1, 1, 0), (2, 1, 1), (0, 1, 2)]
        best_fit = None
        best_aic = float("inf")
        best_ord = (1, 1, 1)

        for order in _ORDERS:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    mdl = _ARIMA(y, order=order)
                    fit = mdl.fit(method_kwargs={"warn_convergence": False})
                if fit.aic < best_aic:
                    best_aic = fit.aic
                    best_fit = fit
                    best_ord = order
            except Exception:
                continue

        if best_fit is None:
            return ARIMAResult(
                year1_base=0, year2_base=0, year3_base=0,
                year1_ci_low=0, year1_ci_high=0,
                year3_ci_low=0, year3_ci_high=0,
                model_order=(1, 1, 1), aic=0.0,
                n_obs=len(series), method="arima", available=False,
            )

        try:
            fc   = best_fit.get_forecast(steps=3)
            mean = fc.predicted_mean   # numpy array or pandas Series
            ci   = fc.conf_int(alpha=0.05)  # numpy array shape (3,2) OR DataFrame

            def _mean(i: int) -> float:
                try:
                    return float(mean[i])
                except Exception:
                    return 0.0

            def _ci_val(row: int, col: int) -> float:
                try:
                    # numpy ndarray path
                    if hasattr(ci, "iloc"):
                        return float(ci.iloc[row, col])
                    else:
                        return float(ci[row, col])
                except Exception:
                    return _mean(row)

            return ARIMAResult(
                year1_base=max(0.0, _mean(0)),
                year2_base=max(0.0, _mean(1)),
                year3_base=max(0.0, _mean(2)),
                year1_ci_low=max(0.0, _ci_val(0, 0)),
                year1_ci_high=max(0.0, _ci_val(0, 1)),
                year3_ci_low=max(0.0, _ci_val(2, 0)),
                year3_ci_high=max(0.0, _ci_val(2, 1)),
                model_order=best_ord,
                aic=round(best_aic, 2),
                n_obs=len(series),
                method="arima",
                available=True,
            )
        except Exception:
            return ARIMAResult(
                year1_base=0, year2_base=0, year3_base=0,
                year1_ci_low=0, year1_ci_high=0,
                year3_ci_low=0, year3_ci_high=0,
                model_order=best_ord, aic=0.0,
                n_obs=len(series), method="arima", available=False,
            )

    # ── Method 2: OLS log-linear trend (numpy) ────────────────────────────────

    def _fit_ols_log_linear(self, series: List[int]) -> ARIMAResult:
        """
        Fit log(y) = a + b*t by OLS; extrapolate 3 periods.
        Prediction intervals use the OLS standard-error formula.
        """
        y = np.array(series, dtype=float)
        n = len(y)
        t = np.arange(n, dtype=float)

        log_y = np.log(np.maximum(y, 1.0))
        t_bar = t.mean()
        y_bar = log_y.mean()
        Stt   = ((t - t_bar) ** 2).sum()
        b     = ((t - t_bar) * (log_y - y_bar)).sum() / max(Stt, 1e-12)
        a     = y_bar - b * t_bar

        fitted   = a + b * t
        resid    = log_y - fitted
        sigma    = resid.std(ddof=2) if n > 2 else 0.15
        t_crit   = 1.96  # ~95 % for large n; acceptable approximation

        forecasts = []
        for step in range(1, 4):
            t_pred   = n - 1 + step
            log_pred = a + b * t_pred
            se       = sigma * math.sqrt(
                1 + 1 / n + (t_pred - t_bar) ** 2 / max(Stt, 1e-12)
            )
            half = t_crit * se
            forecasts.append((
                math.exp(log_pred),
                math.exp(max(log_pred - half, 0.0)),
                math.exp(log_pred + half),
            ))

        return ARIMAResult(
            year1_base=forecasts[0][0],
            year2_base=forecasts[1][0],
            year3_base=forecasts[2][0],
            year1_ci_low=forecasts[0][1],
            year1_ci_high=forecasts[0][2],
            year3_ci_low=forecasts[2][1],
            year3_ci_high=forecasts[2][2],
            model_order=(1, 1, 0),   # descriptive label
            aic=0.0,
            n_obs=n,
            method="ols_log_linear",
            available=True,
        )

    # ── Method 3: CAGR fallback (pure Python) ────────────────────────────────

    def _fit_cagr(self, series: List[int]) -> ARIMAResult:
        """
        Pure-Python exponential projection from CAGR.
        Uses last-3 observations to mitigate early-period drag.
        """
        tail  = series[-3:] if len(series) >= 3 else series
        first = tail[0]
        last  = tail[-1]
        steps = len(tail) - 1

        cagr = ((last / max(first, 1)) ** (1.0 / max(steps, 1))) - 1.0
        # Decelerate slightly over the forecast horizon
        y1 = last  * (1 + cagr)
        y2 = y1    * (1 + cagr * 0.90)
        y3 = y2    * (1 + cagr * 0.80)

        # Heuristic CI: ±20 % Year-1, ±35 % Year-3
        return ARIMAResult(
            year1_base=y1,
            year2_base=y2,
            year3_base=y3,
            year1_ci_low=max(0.0, y1 * 0.80),
            year1_ci_high=y1 * 1.20,
            year3_ci_low=max(0.0, y3 * 0.65),
            year3_ci_high=y3 * 1.35,
            model_order=(0, 1, 0),
            aic=0.0,
            n_obs=len(series),
            method="cagr",
            available=True,
        )


# ── Confidence score from ARIMA result ───────────────────────────────────────

def arima_confidence(result: ARIMAResult, scenario: str, term: str) -> float:
    """
    Convert ARIMA model diagnostics into a [0.30, 0.95] confidence score.

    The CI width ratio is the primary signal:
      • 0.0 = perfect certainty → 0.92
      • 2.0 = CI is ±100 % of forecast → 0.40

    Scenario and term penalties match the legacy engine's logic so that
    cross-combination comparisons remain consistent.
    """
    # Base: derived from CI width (narrower = more confident)
    base = max(0.40, min(0.92, 1.0 - result.ci_width_ratio / 3.0))

    # ARIMA method penalty (statsmodels > OLS > CAGR)
    if result.method == "arima":
        pass              # no penalty
    elif result.method == "ols_log_linear":
        base -= 0.05
    else:
        base -= 0.12

    # Scenario adjustment
    if scenario == "Conservative":
        base += 0.04
    elif scenario == "Optimistic":
        base -= 0.08

    # Term adjustment
    if term.startswith("SP"):
        base -= 0.05
    elif term.startswith("SU"):
        base -= 0.15

    return round(min(max(base, 0.30), 0.95), 2)


# ── Quick helper ──────────────────────────────────────────────────────────────

_GLOBAL_FORECASTER: Optional[ARIMAForecaster] = None


def get_forecaster() -> ARIMAForecaster:
    """Return a module-level singleton ARIMAForecaster (lazy-init)."""
    global _GLOBAL_FORECASTER
    if _GLOBAL_FORECASTER is None:
        _GLOBAL_FORECASTER = ARIMAForecaster()
    return _GLOBAL_FORECASTER
