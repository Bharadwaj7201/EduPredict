"""
Tests for EduPredict MVP ROI Module
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.roi_calculator import ROIInput, ROICalculator, quick_roi


def test_roi_ms_ai_ma():
    """Test ROI calculation for MS in AI in Massachusetts."""
    print("\n=== Test: ROI - MS AI, MA, 50/60/72 students ===")
    
    calc = ROICalculator()
    inputs = ROIInput(
        program_type="MS in AI",
        state="MA",
        year1_enrollment=50,
        year2_enrollment=60,
        year3_enrollment=72
    )
    
    result = calc.calculate(inputs, "International")
    
    print(f"Starting Salary: ${result.starting_salary:,}")
    print(f"5-Year Salary: ${result.salary_5year:,}")
    print(f"Tuition Revenue: ${result.total_tuition_revenue:,}")
    print(f"Program Costs: ${result.program_cost_estimate:,}")
    print(f"ROI Ratio: {result.roi_ratio}x")
    print(f"Payback Period: {result.payback_period_years} years")
    
    # Assertions
    assert result.starting_salary > 0, "Should have salary data"
    assert result.salary_5year > result.starting_salary, "5-year salary > starting"
    assert result.total_tuition_revenue > 0, "Should have revenue"
    assert result.roi_ratio > 0, "Should have ROI"
    
    print("✓ Test passed")
    return result


def test_international_vs_domestic():
    """Test that International generates more revenue."""
    print("\n=== Test: International vs Domestic Revenue ===")
    
    calc = ROICalculator()
    inputs = ROIInput(
        program_type="BS in AI",
        state="NY",
        year1_enrollment=40,
        year2_enrollment=48,
        year3_enrollment=55
    )
    
    intl_result = calc.calculate(inputs, "International")
    dom_result = calc.calculate(inputs, "Domestic")
    
    print(f"International Revenue: ${intl_result.total_tuition_revenue:,}")
    print(f"Domestic Revenue: ${dom_result.total_tuition_revenue:,}")
    
    # International should generate more revenue
    assert intl_result.total_tuition_revenue > dom_result.total_tuition_revenue, \
        "International should have higher revenue"
    
    print("✓ Test passed")


def test_program_costs():
    """Test that different programs have different costs."""
    print("\n=== Test: Program Cost Differences ===")
    
    calc = ROICalculator()
    
    programs = {}
    for program in ["MS in AI", "BS in AI", "AI in Cybersecurity"]:
        inputs = ROIInput(
            program_type=program,
            state="CT",
            year1_enrollment=30,
            year2_enrollment=35,
            year3_enrollment=40
        )
        result = calc.calculate(inputs, "International")
        programs[program] = result.program_cost_estimate
        print(f"{program}: ${result.program_cost_estimate:,}")
    
    # BS should be most expensive (4 years, more facilities)
    assert programs["BS in AI"] > programs["MS in AI"], "BS should cost more than MS"
    
    print("✓ Test passed")


def test_quick_roi():
    """Test the convenience function."""
    print("\n=== Test: Quick ROI Function ===")
    
    result = quick_roi(
        program="MS in AI",
        state="CT",
        year1=40,
        year2=48,
        year3=55,
        student_type="International"
    )
    
    print(f"ROI Ratio: {result.roi_ratio}x")
    print(f"Break-even: {result.break_even_enrollment} students")
    
    assert result.roi_ratio > 0, "Should have valid ROI"
    assert result.break_even_enrollment > 0, "Should have break-even point"
    
    print("✓ Test passed")


def test_summary_metrics():
    """Test summary formatting."""
    print("\n=== Test: Summary Metrics Formatting ===")
    
    calc = ROICalculator()
    inputs = ROIInput(
        program_type="MS in AI",
        state="MA",
        year1_enrollment=50,
        year2_enrollment=60,
        year3_enrollment=72
    )
    
    result = calc.calculate(inputs, "International")
    summary = calc.get_summary_metrics(result)
    
    print("Summary Metrics:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    assert "Starting Salary" in summary, "Should include starting salary"
    assert "ROI Ratio" in summary, "Should include ROI ratio"
    
    print("✓ Test passed")


def run_all_tests():
    """Run all ROI tests."""
    print("\n" + "="*60)
    print("EduPredict MVP - ROI Tests")
    print("="*60)
    
    try:
        test_roi_ms_ai_ma()
        test_international_vs_domestic()
        test_program_costs()
        test_quick_roi()
        test_summary_metrics()
        
        print("\n" + "="*60)
        print("✓ All ROI tests passed!")
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