"""
Tests for EduPredict MVP Forecasting Module
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.forecasting import ForecastInput, EnrollmentForecaster, quick_forecast


def test_forecast_ms_ai_international_fa26_baseline_ct():
    """Test the success criteria scenario from professor requirements."""
    print("\n=== Test: MS AI, International, FA26, Baseline, CT ===")
    
    forecaster = EnrollmentForecaster()
    inputs = ForecastInput(
        program_type="MS in AI",
        student_type="International",
        start_term="FA26",
        scenario="Baseline",
        state="CT"
    )
    
    result = forecaster.forecast(inputs)
    
    print(f"Year 1 Enrollment: {result.year1_enrollment}")
    print(f"3-Year Pool: {result.projected_pool}")
    print(f"Confidence: {result.confidence_score:.0%}")
    
    # Assertions
    assert result.year1_enrollment > 0, "Year 1 should have students"
    assert result.projected_pool > result.year1_enrollment, "3-year pool > Year 1"
    assert result.confidence_score > 0.5, "Should have reasonable confidence"
    
    print("✓ Test passed")
    return result


def test_scenario_comparison():
    """Test that scenarios produce different results."""
    print("\n=== Test: Scenario Comparison ===")
    
    forecaster = EnrollmentForecaster()
    base_input = {
        "program_type": "BS in AI",
        "student_type": "Domestic",
        "start_term": "FA26",
        "state": "NY"
    }
    
    scenarios = {}
    for scenario in ["Conservative", "Baseline", "Optimistic"]:
        inputs = ForecastInput(scenario=scenario, **base_input)
        result = forecaster.forecast(inputs)
        scenarios[scenario] = result.year1_enrollment
        print(f"{scenario}: {result.year1_enrollment} students")
    
    # Assertions
    assert scenarios["Conservative"] < scenarios["Baseline"], "Conservative < Baseline"
    assert scenarios["Baseline"] < scenarios["Optimistic"], "Baseline < Optimistic"
    
    print("✓ Test passed")


def test_state_multipliers():
    """Test that different states produce different results."""
    print("\n=== Test: State Multipliers ===")
    
    forecaster = EnrollmentForecaster()
    base_input = {
        "program_type": "MS in AI",
        "student_type": "International",
        "start_term": "FA26",
        "scenario": "Baseline"
    }
    
    states = {}
    for state in ["CT", "NY", "MA"]:
        inputs = ForecastInput(state=state, **base_input)
        result = forecaster.forecast(inputs)
        states[state] = result.year1_enrollment
        print(f"{state}: {result.year1_enrollment} students")
    
    # MA should be highest due to state multiplier
    assert states["MA"] > states["CT"], "MA should have higher enrollment than CT"
    
    print("✓ Test passed")


def test_term_factors():
    """Test that Fall vs Spring terms differ."""
    print("\n=== Test: Term Factors ===")
    
    forecaster = EnrollmentForecaster()
    base_input = {
        "program_type": "AI in Cybersecurity",
        "student_type": "Domestic",
        "scenario": "Baseline",
        "state": "MA"
    }
    
    terms = {}
    for term in ["FA26", "SP27", "FA28"]:
        inputs = ForecastInput(start_term=term, **base_input)
        result = forecaster.forecast(inputs)
        terms[term] = result.year1_enrollment
        print(f"{term}: {result.year1_enrollment} students")
    
    # Spring should be lower than Fall
    assert terms["SP27"] < terms["FA26"], "Spring should be lower than Fall"
    
    print("✓ Test passed")


def test_quick_forecast():
    """Test the convenience function."""
    print("\n=== Test: Quick Forecast Function ===")
    
    result = quick_forecast(
        program="MS in AI",
        student_type="International",
        term="FA26",
        scenario="Baseline",
        state="CT"
    )
    
    print(f"Year 1: {result.year1_enrollment}")
    print(f"3-Year Pool: {result.projected_pool}")
    
    assert result.year1_enrollment > 0, "Should return valid enrollment"
    
    print("✓ Test passed")


def run_all_tests():
    """Run all forecasting tests."""
    print("\n" + "="*60)
    print("EduPredict MVP - Forecasting Tests")
    print("="*60)
    
    try:
        test_forecast_ms_ai_international_fa26_baseline_ct()
        test_scenario_comparison()
        test_state_multipliers()
        test_term_factors()
        test_quick_forecast()
        
        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_all_tests()