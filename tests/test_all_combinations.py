"""
EduPredict MVP - Comprehensive Test Suite
Tests all 162 input combinations and validates outputs.

Usage:
    python tests/test_all_combinations.py
    python tests/test_all_combinations.py --verbose
    python tests/test_all_combinations.py --save-report
"""

import sys
import os
import argparse
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.forecasting import ForecastInput, EnrollmentForecaster
from models.roi_calculator import ROIInput, ROICalculator
from models.job_market import JobMarketAnalyzer


class EduPredictTester:
    """Comprehensive test suite for EduPredict MVP."""
    
    # All possible input values
    PROGRAMS = ["MS in AI", "BS in AI", "AI in Cybersecurity"]
    STUDENT_TYPES = ["International", "Domestic"]
    TERMS = ["FA26", "SP27", "FA28"]
    SCENARIOS = ["Conservative", "Baseline", "Optimistic"]
    STATES = ["CT", "NY", "MA"]
    
    def __init__(self):
        """Initialize tester with models."""
        self.forecaster = EnrollmentForecaster()
        self.roi_calc = ROICalculator()
        self.job_analyzer = JobMarketAnalyzer()
        self.results = []
        self.errors = []
    
    def test_combination(self, program: str, student_type: str, 
                         term: str, scenario: str, state: str) -> Dict:
        """
        Test a single input combination.
        
        Returns:
            Dict with test results
        """
        result = {
            "inputs": {
                "program": program,
                "student_type": student_type,
                "term": term,
                "scenario": scenario,
                "state": state
            },
            "passed": True,
            "errors": []
        }
        
        try:
            # Test forecasting
            forecast_input = ForecastInput(
                program_type=program,
                student_type=student_type,
                start_term=term,
                scenario=scenario,
                state=state
            )
            forecast = self.forecaster.forecast(forecast_input)
            
            # Validate forecast outputs
            if forecast.year1_enrollment < 0:
                result["errors"].append("Year 1 enrollment is negative")
            if forecast.projected_pool < 0:
                result["errors"].append("Projected pool is negative")
            if not 0 <= forecast.confidence_score <= 1:
                result["errors"].append("Confidence score out of range")
            
            result["forecast"] = {
                "year1": forecast.year1_enrollment,
                "year2": forecast.year2_enrollment,
                "year3": forecast.year3_enrollment,
                "pool": forecast.projected_pool,
                "confidence": forecast.confidence_score
            }
            
            # Test ROI calculation
            roi_input = ROIInput(
                program_type=program,
                state=state,
                year1_enrollment=forecast.year1_enrollment,
                year2_enrollment=forecast.year2_enrollment,
                year3_enrollment=forecast.year3_enrollment
            )
            roi = self.roi_calc.calculate(roi_input, student_type)
            
            # Validate ROI outputs
            if roi.starting_salary < 0:
                result["errors"].append("Starting salary is negative")
            if roi.roi_ratio < 0:
                result["errors"].append("ROI ratio is negative")
            if roi.total_tuition_revenue < 0:
                result["errors"].append("Tuition revenue is negative")
            
            result["roi"] = {
                "starting_salary": roi.starting_salary,
                "roi_ratio": roi.roi_ratio,
                "revenue": roi.total_tuition_revenue,
                "payback": roi.payback_period_years
            }
            
            # Test job market
            job_signal = self.job_analyzer.get_signal(state)
            
            if job_signal.job_growth_rate < 0:
                result["errors"].append("Job growth rate is negative")
            
            result["job_market"] = {
                "growth": job_signal.job_growth_rate,
                "demand": job_signal.demand_level
            }
            
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Exception: {str(e)}")
        
        # Mark as failed if any errors
        if result["errors"]:
            result["passed"] = False
        
        return result
    
    def run_all_tests(self, verbose: bool = False) -> Tuple[int, int]:
        """
        Run tests for all 162 combinations.
        
        Args:
            verbose: Print detailed output
            
        Returns:
            (passed_count, total_count)
        """
        total = 0
        passed = 0
        
        print("=" * 70)
        print("EduPredict MVP - Comprehensive Test Suite")
        print("=" * 70)
        print(f"Testing {len(self.PROGRAMS)} x {len(self.STUDENT_TYPES)} x "
              f"{len(self.TERMS)} x {len(self.SCENARIOS)} x {len(self.STATES)} = "
              f"{len(self.PROGRAMS) * len(self.STUDENT_TYPES) * len(self.TERMS) * len(self.SCENARIOS) * len(self.STATES)} combinations")
        print("=" * 70)
        
        for program in self.PROGRAMS:
            for student_type in self.STUDENT_TYPES:
                for term in self.TERMS:
                    for scenario in self.SCENARIOS:
                        for state in self.STATES:
                            result = self.test_combination(
                                program, student_type, term, scenario, state
                            )
                            self.results.append(result)
                            total += 1
                            
                            if result["passed"]:
                                passed += 1
                                status = "✓ PASS"
                            else:
                                status = "✗ FAIL"
                                self.errors.append(result)
                            
                            if verbose:
                                inputs = result["inputs"]
                                print(f"\n{status} | {inputs['program']} | {inputs['student_type']} | "
                                      f"{inputs['term']} | {inputs['scenario']} | {inputs['state']}")
                                if result["forecast"]:
                                    print(f"       Forecast: Y1={result['forecast']['year1']}, "
                                          f"Pool={result['forecast']['pool']}, "
                                          f"Conf={result['forecast']['confidence']:.0%}")
                                if result["errors"]:
                                    for error in result["errors"]:
                                        print(f"       ERROR: {error}")
                            else:
                                # Progress indicator
                                if total % 50 == 0:
                                    print(f"  ... tested {total} combinations ({passed} passed)")
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests:    {total}")
        print(f"Passed:         {passed}")
        print(f"Failed:         {total - passed}")
        print(f"Success rate:   {passed/total*100:.1f}%")
        print("=" * 70)
        
        return passed, total
    
    def test_success_criteria(self) -> bool:
        """
        Test the success criteria scenario:
        MS in AI + International + FA26 + Baseline + CT
        """
        print("\n" + "=" * 70)
        print("SUCCESS CRITERIA TEST")
        print("=" * 70)
        print("Input: MS in AI + International + FA26 + Baseline + CT")
        print("-" * 70)
        
        result = self.test_combination(
            "MS in AI", "International", "FA26", "Baseline", "CT"
        )
        
        if not result["passed"]:
            print("✗ FAILED - Test did not complete")
            return False
        
        forecast = result["forecast"]
        roi = result["roi"]
        
        print(f"Year 1 Enrollment:     {forecast['year1']} students")
        print(f"3-Year Pool:           {forecast['pool']} students")
        print(f"Confidence:            {forecast['confidence']:.0%}")
        print(f"ROI Ratio:             {roi['roi_ratio']:.2f}x")
        print(f"Starting Salary:       ${roi['starting_salary']:,}")
        print("-" * 70)
        
        # Check criteria
        criteria_passed = True
        
        if forecast["year1"] < 30 or forecast["year1"] > 100:
            print(f"⚠ Year 1 enrollment ({forecast['year1']}) outside expected range (30-100)")
            criteria_passed = False
        
        if forecast["pool"] < 100:
            print(f"⚠ 3-year pool ({forecast['pool']}) below minimum (100)")
            criteria_passed = False
        
        if roi["roi_ratio"] < 1.0:
            print(f"⚠ ROI ratio ({roi['roi_ratio']}) below 1.0")
            criteria_passed = False
        
        if forecast["confidence"] < 0.7:
            print(f"⚠ Confidence ({forecast['confidence']:.0%}) below 70%")
            criteria_passed = False
        
        # Get recommendation
        job_signal = self.job_analyzer.get_signal("CT")
        demand_score = self.job_analyzer.get_demand_score("CT")
        
        if roi["roi_ratio"] >= 1.5 and forecast["confidence"] > 0.75:
            recommendation = "STRONG GO"
        elif roi["roi_ratio"] >= 1.0:
            recommendation = "GO"
        elif roi["roi_ratio"] >= 0.7:
            recommendation = "CONDITIONAL"
        else:
            recommendation = "RECONSIDER"
        
        print(f"Job Market Growth:     {job_signal.job_growth_rate}%")
        print(f"Demand Score:          {demand_score}/100")
        print(f"Recommendation:        {recommendation}")
        print("=" * 70)
        
        if criteria_passed and recommendation in ["STRONG GO", "GO"]:
            print("✓ SUCCESS CRITERIA MET")
            return True
        else:
            print("✗ SUCCESS CRITERIA NOT FULLY MET")
            return False
    
    def generate_report(self, filename: str = None) -> str:
        """Generate detailed test report."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.md"
        
        report_path = os.path.join("tests", filename)
        
        with open(report_path, 'w') as f:
            f.write("# EduPredict MVP - Test Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            total = len(self.results)
            passed = sum(1 for r in self.results if r["passed"])
            
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests:** {total}\n")
            f.write(f"- **Passed:** {passed}\n")
            f.write(f"- **Failed:** {total - passed}\n")
            f.write(f"- **Success Rate:** {passed/total*100:.1f}%\n\n")
            
            # Success criteria
            f.write("## Success Criteria Test\n\n")
            f.write("Input: MS in AI + International + FA26 + Baseline + CT\n\n")
            
            success_result = next(
                (r for r in self.results 
                 if r["inputs"]["program"] == "MS in AI"
                 and r["inputs"]["student_type"] == "International"
                 and r["inputs"]["term"] == "FA26"
                 and r["inputs"]["scenario"] == "Baseline"
                 and r["inputs"]["state"] == "CT"),
                None
            )
            
            if success_result:
                f.write(f"- **Year 1:** {success_result['forecast']['year1']} students\n")
                f.write(f"- **3-Year Pool:** {success_result['forecast']['pool']} students\n")
                f.write(f"- **ROI:** {success_result['roi']['roi_ratio']:.2f}x\n")
                f.write(f"- **Status:** {'PASS' if success_result['passed'] else 'FAIL'}\n\n")
            
            # Failed tests
            if self.errors:
                f.write("## Failed Tests\n\n")
                for error in self.errors:
                    inputs = error["inputs"]
                    f.write(f"### {inputs['program']} | {inputs['student_type']} | "
                           f"{inputs['term']} | {inputs['scenario']} | {inputs['state']}\n\n")
                    for err in error["errors"]:
                        f.write(f"- {err}\n")
                    f.write("\n")
            
            # Statistics by category
            f.write("## Statistics by Category\n\n")
            
            # By program
            f.write("### By Program\n\n")
            for program in self.PROGRAMS:
                program_results = [r for r in self.results if r["inputs"]["program"] == program]
                program_passed = sum(1 for r in program_results if r["passed"])
                f.write(f"- **{program}:** {program_passed}/{len(program_results)} passed\n")
            
            f.write("\n### By State\n\n")
            for state in self.STATES:
                state_results = [r for r in self.results if r["inputs"]["state"] == state]
                state_passed = sum(1 for r in state_results if r["passed"])
                avg_pool = sum(r["forecast"]["pool"] for r in state_results if r["forecast"]) / len(state_results)
                f.write(f"- **{state}:** {state_passed}/{len(state_results)} passed "
                       f"(avg pool: {avg_pool:.0f} students)\n")
            
            f.write("\n### By Scenario\n\n")
            for scenario in self.SCENARIOS:
                scenario_results = [r for r in self.results if r["inputs"]["scenario"] == scenario]
                scenario_passed = sum(1 for r in scenario_results if r["passed"])
                f.write(f"- **{scenario}:** {scenario_passed}/{len(scenario_results)} passed\n")
        
        print(f"\nReport saved to: {report_path}")
        return report_path


def main():
    parser = argparse.ArgumentParser(description="Test all EduPredict combinations")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed output for each test")
    parser.add_argument("--save-report", "-s", action="store_true",
                       help="Save detailed report to file")
    parser.add_argument("--success-only", action="store_true",
                       help="Only run success criteria test")
    
    args = parser.parse_args()
    
    tester = EduPredictTester()
    
    if args.success_only:
        tester.test_success_criteria()
    else:
        # Run all tests
        passed, total = tester.run_all_tests(verbose=args.verbose)
        
        # Run success criteria
        success_passed = tester.test_success_criteria()
        
        # Save report if requested
        if args.save_report:
            tester.generate_report()
        
        # Exit with appropriate code
        if passed == total and success_passed:
            print("\n✓ ALL TESTS PASSED")
            return 0
        else:
            print(f"\n✗ {total - passed} TESTS FAILED")
            return 1


if __name__ == "__main__":
    sys.exit(main())
