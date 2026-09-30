"""
EduPredict MVP Models
Forecasting, ROI, and job market analysis modules.
"""

from .forecasting import (
    ForecastInput,
    ForecastOutput,
    EnrollmentForecaster,
    quick_forecast
)

from .roi_calculator import (
    ROIInput,
    ROIOutput,
    ROICalculator,
    quick_roi
)

from .job_market import (
    JobMarketSignal,
    JobMarketAnalyzer,
    get_workforce_outlook
)

__all__ = [
    'ForecastInput',
    'ForecastOutput',
    'EnrollmentForecaster',
    'quick_forecast',
    'ROIInput',
    'ROIOutput',
    'ROICalculator',
    'quick_roi',
    'JobMarketSignal',
    'JobMarketAnalyzer',
    'get_workforce_outlook',
]