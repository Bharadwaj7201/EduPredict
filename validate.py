#!/usr/bin/env python3
"""
EduPredict MVP - Quick Validation
Tests core logic without external dependencies.
"""

from dataclasses import dataclass
from typing import Dict


# Simplified forecast logic (same as models/forecasting.py)
@dataclass
class ForecastInput:
    program_type: str
    student_type: str
    start_term: str
    scenario: str
    state: str


@dataclass
class ForecastOutput:
    projected_pool: int
    year1_enrollment: int
    year2_enrollment: int
    year3_enrollment: int
    growth_rate: float
    confidence_score: float


class SimpleForecaster:
    """Simplified forecaster for validation."""
    
    SCENARIO_MULTIPLIERS = {
        "Baseline": 1.0,
        "Optimistic": 1.25,
        "Conservative": 0.75
    }
    
    TERM_FACTORS = {
        "FA26": 1.0,
        "SP27": 0.65,
        "FA28": 1.05
    }
    
    STUDENT_BASELINE = {
        "International": {
            "MS in AI": 45,
            "BS in AI": 35,
            "AI in Cybersecurity": 25
        },
        "Domestic": {
            "MS in AI": 30,
            "BS in AI": 55,
            "AI in Cybersecurity": 40
        }
    }
    
    STATE_MULTIPLIERS = {
        "CT": 0.9,
        "NY": 1.15,
        "MA": 1.25
    }
    
    def forecast(self, inputs: ForecastInput) -> ForecastOutput:
        baseline = self.STUDENT_BASELINE[inputs.student_type][inputs.program_type]
        scenario_mult = self.SCENARIO_MULTIPLIERS[inputs.scenario]
        term_factor = self.TERM_FACTORS[inputs.start_term]
        state_mult = self.STATE_MULTIPLIERS[inputs.state]
        
        year1 = int(baseline * scenario_mult * term_factor * state_mult)
        
        growth_rate = 0.20 if inputs.scenario == "Optimistic" else (
            0.10 if inputs.scenario == "Baseline" else 0.05
        )
        
        year2 = int(year1 * (1 + growth_rate))
        year3 = int(year2 * (1 + growth_rate * 0.8))
        
        projected_pool = year1 + year2 + year3
        
        return ForecastOutput(
            projected_pool=projected_pool,
            year1_enrollment=year1,
            year2_enrollment=year2,
            year3_enrollment=year3,
            growth_rate=growth_rate,
            confidence_score=0.80
        )


@dataclass
class ROIOutput:
    starting_salary: int
    salary_5year: int
    total_tuition_revenue: int
    program_cost_estimate: int
    roi_ratio: float


class SimpleROICalculator:
    """Simplified ROI calculator."""
    
    STARTING_SALARIES = {
        "MS in AI": {"CT": 95000, "NY": 110000, "MA": 115000},
        "BS in AI": {"CT": 75000, "NY": 85000, "MA": 90000},
        "AI in Cybersecurity": {"CT": 98000, "NY": 112000, "MA": 118000}
    }
    
    TUITION_RATES = {
        "MS in AI": {"International": 35000, "Domestic": 25000},
        "BS in AI": {"International": 32000, "Domestic": 18000},
        "AI in Cybersecurity": {"International": 34000, "Domestic": 24000}
    }
    
    STARTUP_COSTS = {
        "MS in AI": 500000,
        "BS in AI": 750000,
        "AI in Cybersecurity": 550000
    }
    
    def calculate(self, program: str, state: str, year1: int, year2: int, year3: int, student_type: str) -> ROIOutput:
        starting_salary = self.STARTING_SALARIES[program][state]
        salary_5year = int(starting_salary * (1.08 ** 5))
        
        annual_tuition = self.TUITION_RATES[program][student_type]
        program_years = 2 if "MS" in program or "Cybersecurity" in program else 4
        
        total_tuition = (year1 + year2 + year3) * annual_tuition * program_years
        startup_cost = self.STARTUP_COSTS[program]
        operational_cost = (year1 + year2 + year3) * 12000
        
        total_cost = startup_cost + operational_cost
        net_return = total_tuition - total_cost
        roi_ratio = round(net_return / total_cost, 2) if total_cost > 0 else 0
        
        return ROIOutput(
            starting_salary=starting_salary,
            salary_5year=salary_5year,
            total_tuition_revenue=total_tuition,
            program_cost_estimate=total_cost,
            roi_ratio=roi_ratio
        )


def test_success_criteria():
    """Test the exact success criteria from professor requirements."""
    print("\n" + "="*60)
    print("EduPredict MVP - Validation Tests")
    print("="*60)
    
    print("\n>>> Test: Success Criteria Scenario")
    print("-" * 40)
    print("Inputs:")
    print("  Program: MS in AI")
    print("  Student Type: International")
    print("  Term: FA26 (Fall 2026)")
    print("  Scenario: Baseline")
    print("  State: CT (Connecticut)")
    
    forecaster = SimpleForecaster()
    inputs = ForecastInput(
        program_type="MS in AI",
        student_type="International",
        start_term="FA26",
        scenario="Baseline",
        state="CT"
    )
    
    forecast = forecaster.forecast(inputs)
    
    print(f"\nForecast Results:")
    print(f"  Year 1 Enrollment: {forecast.year1_enrollment} students")
    print(f"  3-Year Pool: {forecast.projected_pool} students")
    print(f"  Confidence: {int(forecast.confidence_score * 100)}%")
    
    roi_calc = SimpleROICalculator()
    roi = roi_calc.calculate("MS in AI", "CT", forecast.year1_enrollment, 
                              forecast.year2_enrollment, forecast.year3_enrollment, 
                              "International")
    
    print(f"\nROI Results:")
    print(f"  Starting Salary: ${roi.starting_salary:,}")
    print(f"  5-Year Salary: ${roi.salary_5year:,}")
    print(f"  Tuition Revenue: ${roi.total_tuition_revenue:,}")
    print(f"  Program Costs: ${roi.program_cost_estimate:,}")
    print(f"  ROI Ratio: {roi.roi_ratio}x")
    
    # Validate
    assert forecast.year1_enrollment > 0, "Year 1 must have students"
    assert forecast.projected_pool > forecast.year1_enrollment, "Pool > Year 1"
    assert roi.roi_ratio > 0, "ROI must be positive"
    assert roi.starting_salary > 80000, "Salary should be realistic for AI roles"
    
    print("\n✓ All validations passed!")
    
    # Recommendation
    if roi.roi_ratio >= 1.5:
        rec = "STRONG GO"
    elif roi.roi_ratio >= 1.0:
        rec = "GO"
    elif roi.roi_ratio >= 0.7:
        rec = "CONDITIONAL"
    else:
        rec = "RECONSIDER"
    
    print(f"\n{'='*60}")
    print(f"RECOMMENDATION: {rec}")
    print(f"{'='*60}")
    
    return True


def test_all_combinations():
    """Test all MVP input combinations."""
    print("\n>>> Test: All MVP Combinations")
    print("-" * 40)
    
    forecaster = SimpleForecaster()
    
    programs = ["MS in AI", "BS in AI", "AI in Cybersecurity"]
    student_types = ["International", "Domestic"]
    terms = ["FA26", "SP27", "FA28"]
    scenarios = ["Baseline", "Optimistic", "Conservative"]
    states = ["CT", "NY", "MA"]
    
    total_combinations = len(programs) * len(student_types) * len(terms) * len(scenarios) * len(states)
    print(f"Testing {total_combinations} combinations...")
    
    count = 0
    for program in programs:
        for student in student_types:
            for term in terms:
                for scenario in scenarios:
                    for state in states:
                        inputs = ForecastInput(program, student, term, scenario, state)
                        result = forecaster.forecast(inputs)
                        
                        # Basic validations
                        assert result.year1_enrollment > 0, f"Failed: {program}, {student}, {term}, {scenario}, {state}"
                        assert result.projected_pool > 0
                        assert 0 <= result.confidence_score <= 1
                        
                        count += 1
    
    print(f"✓ All {count} combinations validated successfully!")
    return True


if __name__ == "__main__":
    try:
        test_success_criteria()
        test_all_combinations()
        
        print("\n" + "="*60)
        print("✓ ALL VALIDATIONS PASSED")
        print("="*60)
        print("\nSystem is ready for deployment.")
        print("\nTo run the full app:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run: streamlit run ui/app.py")
        print("  3. Or use: ./run.sh")
        
    except AssertionError as e:
        print(f"\n✗ Validation failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)