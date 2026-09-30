"""
EduPredict MVP - Job Market Signals
State-level workforce demand indicators with AI occupation exposure analysis.

Data Sources:
- BLS Occupational Employment Statistics (May 2023)
- Anthropic Economic Index / Labor Market Impacts (March 2026)
  - Massenkoff & McCrory: "Labor market impacts of AI: A new measure and early evidence"
- Industry job market reports

Key Insight from Anthropic 2026:
AI coverage is far below theoretical capability. Computer & Math occupations show
94% theoretical feasibility but only 33% actual coverage -- a 61% gap that creates
uncertainty in workforce forecasting.
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    """AI disruption risk levels for occupations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AIOccupationExposure:
    """AI exposure metrics for a specific occupation from Anthropic 2026 research."""
    occupation: str
    observed_exposure: float  # 0-1, actual usage-based coverage
    theoretical_feasibility: float  # 0-1, what AI could theoretically do
    coverage_gap: float  # theoretical - observed
    bls_growth_projection_2034: float  # BLS projected change 2024-2034
    young_worker_hiring_impact: float  # Change in job finding rate (22-25 age group)
    risk_level: RiskLevel
    key_finding: str  # Summary insight from research


@dataclass
class JobMarketSignal:
    """Job market data for a state with AI-aware workforce indicators."""
    state: str
    job_growth_rate: float  # 5-year annual growth %
    open_positions_estimate: int
    demand_level: str  # High, Medium, Low
    trend_direction: str  # Growing, Stable, Declining
    # AI-enhanced fields
    top_exposed_occupations: List[str] = field(default_factory=list)
    ai_coverage_gap: float = 0.0  # Gap between theory and reality
    avg_salary_premium: float = 0.0  # % above national average


class AIOccupationDatabase:
    """
    Anthropic 2026 Labor Market Impacts -- Observed Exposure Data.
    
    Source: Massenkoff & McCrory (2026) "Labor market impacts of AI: A new measure and early evidence"
    URL: https://www.anthropic.com/research/labor-market-impacts
    Data: https://huggingface.co/datasets/Anthropic/EconomicIndex
    
    Key Finding: "For every 10 percentage point increase in coverage, 
    BLS growth projections drop by 0.6 percentage points."
    """
    
    # Observed Exposure scores from Anthropic Economic Index (March 2026)
    # Based on millions of Claude conversations in professional settings
    OBSERVED_EXPOSURE = {
        # Computer & Math Category (94% theoretical, 33% actual coverage)
        "Computer Programmers": 0.75,  # #1 most exposed
        "Software Developers": 0.72,
        "Data Scientists": 0.65,
        "Information Security Analysts": 0.55,  # AI in Cybersecurity proxy
        "Computer Systems Analysts": 0.60,
        "Database Administrators": 0.58,
        "Network Architects": 0.45,
        
        # Business & Financial
        "Financial Analysts": 0.60,
        "Market Research Analysts": 0.52,
        "Accountants": 0.48,
        
        # Office & Admin (90% theoretical)
        "Customer Service Representatives": 0.70,  # #2 most exposed
        "Data Entry Keyers": 0.67,  # #3 most exposed
        "Paralegals": 0.55,
        "Administrative Assistants": 0.45,
        
        # Education (lower exposure)
        "Postsecondary Teachers": 0.25,
        "Instructional Coordinators": 0.30,
    }
    
    # Coverage Gap by Occupational Category
    # From Figure 2: Theoretical capability vs. Observed exposure
    CATEGORY_COVERAGE = {
        "Computer & Math": {
            "theoretical": 0.94,  # 94% theoretically feasible
            "observed": 0.33,     # Only 33% actually covered
            "gap": 0.61           # 61 percentage point gap
        },
        "Office & Admin": {
            "theoretical": 0.90,
            "observed": 0.28,
            "gap": 0.62
        },
        "Business & Financial": {
            "theoretical": 0.75,
            "observed": 0.25,
            "gap": 0.50
        },
        "Education": {
            "theoretical": 0.40,
            "observed": 0.15,
            "gap": 0.25
        }
    }
    
    # BLS Projection Correlation
    # Key finding: "For every 10pp increase in coverage, BLS projections drop 0.6pp"
    BLS_PROJECTION_IMPACT = -0.06  # Per 1% exposure
    
    # Young Worker Impact (Brynjolfsson et al. 2025 via Anthropic)
    # Workers aged 22-25 in exposed occupations
    YOUNG_WORKER_HIRING_SLOWDOWN = -0.14  # 14% drop in job finding rate
    
    # Worker Demographics in High Exposure Roles (Figure 5)
    HIGH_EXPOSURE_WORKER_PROFILE = {
        "female_share": 0.56,  # +16pp vs unexposed
        "white_share": 0.72,   # +11pp vs unexposed
        "asian_share": 0.12,   # 2x unexposed rate
        "graduate_degree_share": 0.174,  # 4x unexposed (4.5%)
        "earnings_premium": 0.47,  # +47% above average
        "median_age": 42  # Older than unexposed
    }
    
    @classmethod
    def get_exposure(cls, occupation: str) -> float:
        """Get observed exposure score for an occupation."""
        return cls.OBSERVED_EXPOSURE.get(occupation, 0.0)
    
    @classmethod
    def get_category_gap(cls, category: str) -> float:
        """Get coverage gap for an occupational category."""
        cat_data = cls.CATEGORY_COVERAGE.get(category, {})
        return cat_data.get("gap", 0.0)
    
    @classmethod
    def calculate_bls_impact(cls, exposure: float) -> float:
        """
        Calculate projected BLS employment impact.
        
        Formula: For every 10pp exposure, -0.6pp growth projection (2024-2034)
        
        Args:
            exposure: Observed exposure score (0-1)
            
        Returns:
            Projected employment change percentage point impact
        """
        return exposure * 100 * cls.BLS_PROJECTION_IMPACT
    
    @classmethod
    def get_risk_level(cls, exposure: float) -> RiskLevel:
        """
        Determine risk level based on observed exposure.
        
        Thresholds based on Anthropic analysis of unemployment impacts.
        """
        if exposure >= 0.70:
            return RiskLevel.CRITICAL  # Top 3 most exposed occupations
        elif exposure >= 0.60:
            return RiskLevel.HIGH
        elif exposure >= 0.40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    @classmethod
    def get_top_exposed(cls, n: int = 10) -> List[Tuple[str, float]]:
        """Get top N most exposed occupations."""
        sorted_occ = sorted(cls.OBSERVED_EXPOSURE.items(), key=lambda x: x[1], reverse=True)
        return sorted_occ[:n]
    
    @classmethod
    def get_program_exposure(cls, program_type: str) -> AIOccupationExposure:
        """
        Get AI exposure profile for an EduPredict program type.
        
        Args:
            program_type: "MS in AI", "BS in AI", or "AI in Cybersecurity"
        """
        # Map programs to primary occupations
        program_mappings = {
            "MS in AI": {
                "primary": "Data Scientists",
                "secondary": ["Computer Programmers", "Machine Learning Engineers"],
                "category": "Computer & Math",
                "avg_salary": 115000
            },
            "BS in AI": {
                "primary": "Software Developers",
                "secondary": ["Computer Programmers", "Computer Systems Analysts"],
                "category": "Computer & Math",
                "avg_salary": 85000
            },
            "AI in Cybersecurity": {
                "primary": "Information Security Analysts",
                "secondary": ["Network Architects", "Database Administrators"],
                "category": "Computer & Math",
                "avg_salary": 105000
            }
        }
        
        mapping = program_mappings.get(program_type, program_mappings["MS in AI"])
        primary_occ = mapping["primary"]
        category = mapping["category"]
        
        exposure = cls.get_exposure(primary_occ)
        category_data = cls.CATEGORY_COVERAGE.get(category, {})
        theoretical = category_data.get("theoretical", 0.94)
        observed = category_data.get("observed", 0.33)
        gap = category_data.get("gap", 0.61)
        
        # Calculate BLS impact
        bls_impact = cls.calculate_bls_impact(exposure)
        
        # Young worker hiring impact
        young_impact = cls.YOUNG_WORKER_HIRING_SLOWDOWN if exposure > 0.50 else 0.0
        
        risk = cls.get_risk_level(exposure)
        
        # Key finding summary
        if exposure >= 0.70:
            finding = f"CRITICAL: {primary_occ} is among top 3 most AI-exposed occupations. " \
                     f"Young worker hiring down {abs(young_impact):.0%}."
        elif exposure >= 0.60:
            finding = f"HIGH: {primary_occ} shows {exposure:.0%} observed exposure. " \
                     f"Gap between theory ({theoretical:.0%}) and reality ({observed:.0%}) creates uncertainty."
        else:
            finding = f"MODERATE: {primary_occ} has {exposure:.0%} exposure. " \
                     f"Coverage gap of {gap:.0%} suggests room for growth."
        
        return AIOccupationExposure(
            occupation=primary_occ,
            observed_exposure=exposure,
            theoretical_feasibility=theoretical,
            coverage_gap=gap,
            bls_growth_projection_2034=bls_impact,
            young_worker_hiring_impact=young_impact,
            risk_level=risk,
            key_finding=finding
        )


class JobMarketAnalyzer:
    """
    Provides AI job market signals for states with Anthropic 2026 exposure data.
    
    Combines:
    - State-level demand indicators (BLS, industry reports)
    - AI occupation exposure (Anthropic Economic Index)
    - BLS projection correlations
    - Hiring slowdown warnings for young workers
    
    Data Sources:
    - data/raw/job_market_data.csv (state-level)
    - Anthropic Economic Index (occupation-level AI exposure)
    """
    
    # State-level fallback data
    STATE_DATA = {
        "CT": {
            "job_growth_rate": 28.5,  # 5-year growth %
            "open_positions_base": 1200,
            "demand_level": "Medium-High",
            "trend_direction": "Growing",
            "top_employers": "United Technologies, Pratt & Whitney, Hartford Insurance, Pfizer",
            "avg_salary": 102000,
            "cost_of_living_index": 112  # US avg = 100
        },
        "NY": {
            "job_growth_rate": 35.8,
            "open_positions_base": 8500,
            "demand_level": "Very High",
            "trend_direction": "Growing",
            "top_employers": "Google NYC, Meta, Bloomberg, JPMorgan Chase, IBM",
            "avg_salary": 118000,
            "cost_of_living_index": 135
        },
        "MA": {
            "job_growth_rate": 42.3,
            "open_positions_base": 6200,
            "demand_level": "Very High",
            "trend_direction": "Growing",
            "top_employers": "MIT, Harvard, Google Cambridge, Amazon Boston, Biogen, HubSpot",
            "avg_salary": 115000,
            "cost_of_living_index": 125
        }
    }
    
    def __init__(self, data_path: str = None):
        """
        Initialize job market analyzer with AI exposure database.
        
        Args:
            data_path: Path to job_market_data.csv (optional)
        """
        self.data_path = data_path or self._find_data_file()
        self.state_data = self._load_data()
        self.ai_db = AIOccupationDatabase()
    
    def _find_data_file(self) -> str:
        """Find the job market data file."""
        possible_paths = [
            "data/raw/job_market_data.csv",
            "../data/raw/job_market_data.csv",
            "../../data/raw/job_market_data.csv",
            "/Users/munagalatarakanagaganesh/Documents/Notes/01_Projects/EduPredict-MVP/data/raw/job_market_data.csv"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _load_data(self) -> Dict:
        """Load data from CSV or use enhanced fallback."""
        if not self.data_path or not os.path.exists(self.data_path):
            print("Job market: Using enhanced fallback with Anthropic 2026 data")
            return self.STATE_DATA
        
        try:
            data = {}
            with open(self.data_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    state = row['state']
                    data[state] = {
                        'job_growth_rate': float(row['ai_job_growth_5yr']),
                        'open_positions_base': int(row['open_positions_sample']),
                        'demand_level': row['demand_level'],
                        'trend_direction': 'Growing',
                        'top_employers': row.get('top_employers', ''),
                        'avg_salary': int(row.get('avg_salary', 100000)),
                        'cost_of_living_index': int(row.get('col_index', 100))
                    }
            print(f"Job market: Loaded data for {len(data)} states from CSV")
            return data
        except Exception as e:
            print(f"Job market: Error loading CSV: {e}")
            return self.STATE_DATA
    
    def get_signal(self, state: str, program_type: str = "MS in AI") -> JobMarketSignal:
        """
        Get enhanced job market signal for a state and program.
        
        Args:
            state: CT, NY, or MA
            program_type: Program to analyze exposure for
            
        Returns:
            JobMarketSignal with AI-aware indicators
        """
        if state not in self.state_data:
            raise ValueError(f"State {state} not supported in MVP")
        
        data = self.state_data[state]
        
        # Get AI exposure for this program
        exposure = self.ai_db.get_program_exposure(program_type)
        
        # Top exposed occupations in this state
        top_exposed = [occ for occ, _ in self.ai_db.get_top_exposed(5)]
        
        return JobMarketSignal(
            state=state,
            job_growth_rate=data["job_growth_rate"],
            open_positions_estimate=data["open_positions_base"],
            demand_level=data["demand_level"],
            trend_direction=data["trend_direction"],
            top_exposed_occupations=top_exposed,
            ai_coverage_gap=exposure.coverage_gap,
            avg_salary_premium=data.get("avg_salary", 100000) / 100000 - 1
        )
    
    def get_ai_exposure_report(self, program_type: str) -> AIOccupationExposure:
        """
        Get comprehensive AI exposure report for a program.
        
        Example:
            report = analyzer.get_ai_exposure_report("MS in AI")
            print(f"Risk Level: {report.risk_level.value}")
            print(f"Key Finding: {report.key_finding}")
        """
        return self.ai_db.get_program_exposure(program_type)
    
    def get_demand_score(self, state: str, program_type: str = "MS in AI") -> int:
        """
        Get AI-adjusted demand score (0-100).
        
        Factors:
        - Base demand level (state economy)
        - Growth rate (5-year projection)
        - AI exposure risk (penalty for high exposure)
        - Coverage gap (opportunity for new graduates)
        
        Args:
            state: State abbreviation
            program_type: Program to score
            
        Returns:
            Adjusted demand score 0-100
        """
        signal = self.get_signal(state, program_type)
        exposure = self.ai_db.get_program_exposure(program_type)
        
        # Base score from demand level
        base_scores = {
            "Very High": 85,
            "High": 75,
            "Medium-High": 65,
            "Medium": 50,
            "Low": 25
        }
        base = base_scores.get(signal.demand_level, 50)
        
        # Growth bonus
        growth_bonus = min(signal.job_growth_rate / 2, 15)
        
        # AI exposure penalty (high exposure = slightly lower score due to disruption risk)
        exposure_penalty = 0
        if exposure.risk_level == RiskLevel.CRITICAL:
            exposure_penalty = -10
        elif exposure.risk_level == RiskLevel.HIGH:
            exposure_penalty = -5
        
        # Coverage gap bonus (gap = opportunity for new graduates)
        gap_bonus = signal.ai_coverage_gap * 10  # Up to 6 points
        
        score = base + growth_bonus + exposure_penalty + gap_bonus
        return int(max(0, min(100, score)))
    
    def get_hiring_warning(self, program_type: str) -> str:
        """
        Get hiring warning for young workers based on AI exposure.
        
        Source: Brynjolfsson et al. (2025) via Anthropic 2026
        Finding: 14% drop in job finding rate for workers aged 22-25 in exposed occupations
        
        Returns:
            Warning message if applicable, empty string otherwise
        """
        exposure = self.ai_db.get_program_exposure(program_type)
        
        if exposure.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return (
                f"⚠️ YOUNG WORKER ALERT: Anthropic 2026 research shows a "
                f"{abs(exposure.young_worker_hiring_impact):.0%} drop in hiring for workers aged 22-25 "
                f"in {exposure.occupation} roles. Consider targeting experienced professionals "
                f"or emphasizing unique human skills in curriculum."
            )
        
        if exposure.coverage_gap > 0.50:
            return (
                f"ℹ️ COVERAGE GAP: {exposure.coverage_gap:.0%} gap between AI theory ({exposure.theoretical_feasibility:.0%}) "
                f"and reality ({exposure.observed_exposure:.0%}) suggests market uncertainty. "
                f"Monitor placement rates closely."
            )
        
        return ""
    
    def format_signal(self, signal: JobMarketSignal, program_type: str = "MS in AI") -> Dict[str, str]:
        """Format signal for display with AI insights."""
        exposure = self.ai_db.get_program_exposure(program_type)
        
        return {
            "State": signal.state,
            "5-Year Growth": f"{signal.job_growth_rate}%",
            "Open Positions": f"~{signal.open_positions_estimate:,}",
            "Demand Level": signal.demand_level,
            "AI Exposure": f"{exposure.observed_exposure:.0%}",
            "Risk Level": exposure.risk_level.value.upper(),
            "Coverage Gap": f"{signal.ai_coverage_gap:.0%}",
            "BLS Impact": f"{exposure.bls_growth_projection_2034:+.1f}pp by 2034",
            "Trend": signal.trend_direction
        }
    
    def get_program_recommendation(self, state: str, program_type: str) -> Dict:
        """
        Get comprehensive program launch recommendation.
        
        Returns dict with:
        - demand_score: 0-100
        - risk_level: low/medium/high/critical
        - recommendation: Launch / Caution / Delay
        - rationale: Explanation
        - warnings: List of concerns
        - opportunities: List of advantages
        """
        signal = self.get_signal(state, program_type)
        exposure = self.ai_db.get_program_exposure(program_type)
        score = self.get_demand_score(state, program_type)
        
        # Build recommendation
        warnings = []
        opportunities = []
        
        # Risk-based warnings
        if exposure.risk_level == RiskLevel.CRITICAL:
            warnings.append(f"{exposure.occupation} is among top 3 most AI-exposed roles")
            warnings.append(f"Young worker hiring down {abs(exposure.young_worker_hiring_impact):.0%}")
        elif exposure.risk_level == RiskLevel.HIGH:
            warnings.append(f"High AI exposure ({exposure.observed_exposure:.0%}) with hiring slowdown risk")
        
        # BLS projection warning
        if exposure.bls_growth_projection_2034 < -3.0:
            warnings.append(f"BLS projects {exposure.bls_growth_projection_2034:.1f}pp weaker growth by 2034")
        
        # Coverage gap opportunity
        if exposure.coverage_gap > 0.50:
            opportunities.append(f"{exposure.coverage_gap:.0%} coverage gap = growth opportunity before full automation")
        
        # Demand opportunity
        if signal.demand_level in ["Very High", "High"]:
            opportunities.append(f"{signal.demand_level} employer demand in {state}")
        
        # Salary opportunity
        if signal.avg_salary_premium > 0.10:
            opportunities.append(f"{signal.avg_salary_premium:.0%} salary premium vs national average")
        
        # Overall recommendation
        if score >= 75 and exposure.risk_level not in [RiskLevel.CRITICAL]:
            rec = "LAUNCH"
            rationale = "Strong demand with manageable AI disruption risk"
        elif score >= 60:
            rec = "CAUTION"
            rationale = "Positive demand but monitor placement rates closely"
        else:
            rec = "DELAY"
            rationale = "Weak demand or high disruption risk -- gather more data"
        
        return {
            "demand_score": score,
            "risk_level": exposure.risk_level.value,
            "recommendation": rec,
            "rationale": rationale,
            "warnings": warnings,
            "opportunities": opportunities,
            "key_finding": exposure.key_finding
        }
    
    def get_all_states(self) -> Dict[str, Dict]:
        """Get data for all states."""
        return self.state_data


def get_workforce_outlook(state: str, program_type: str = "MS in AI") -> Dict[str, str]:
    """
    Quick workforce outlook with AI exposure analysis.
    
    Example:
        outlook = get_workforce_outlook("MA", "MS in AI")
    """
    analyzer = JobMarketAnalyzer()
    signal = analyzer.get_signal(state, program_type)
    return analyzer.format_signal(signal, program_type)


def quick_ai_report(program_type: str) -> Dict[str, any]:
    """
    Quick AI exposure report for a program.
    
    Example:
        report = quick_ai_report("MS in AI")
        print(f"Risk: {report['risk_level']}")
        print(f"BLS Impact: {report['bls_impact']}")
    """
    db = AIOccupationDatabase()
    exposure = db.get_program_exposure(program_type)
    
    return {
        "occupation": exposure.occupation,
        "observed_exposure": exposure.observed_exposure,
        "theoretical_feasibility": exposure.theoretical_feasibility,
        "coverage_gap": exposure.coverage_gap,
        "risk_level": exposure.risk_level.value,
        "bls_impact_2034": exposure.bls_growth_projection_2034,
        "young_worker_impact": exposure.young_worker_hiring_impact,
        "key_finding": exposure.key_finding
    }


if __name__ == "__main__":
    # Test the enhanced analyzer
    analyzer = JobMarketAnalyzer()
    
    print("=" * 70)
    print("EDUPREDICT JOB MARKET ANALYZER - ANTHROPIC 2026 EDITION")
    print("=" * 70)
    print()
    
    # Test each program
    for program in ["MS in AI", "BS in AI", "AI in Cybersecurity"]:
        print(f"\n{'='*70}")
        print(f"PROGRAM: {program}")
        print(f"{'='*70}")
        
        # AI Exposure Report
        exposure = analyzer.get_ai_exposure_report(program)
        print(f"\n📊 AI EXPOSURE ANALYSIS")
        print(f"  Primary Occupation: {exposure.occupation}")
        print(f"  Observed Exposure: {exposure.observed_exposure:.0%}")
        print(f"  Theoretical Feasibility: {exposure.theoretical_feasibility:.0%}")
        print(f"  Coverage Gap: {exposure.coverage_gap:.0%}")
        print(f"  Risk Level: {exposure.risk_level.value.upper()}")
        print(f"\n🔮 BLS PROJECTIONS (2024-2034)")
        print(f"  Impact: {exposure.bls_growth_projection_2034:+.1f} percentage points")
        print(f"\n👶 YOUNG WORKER IMPACT (Age 22-25)")
        print(f"  Hiring Change: {exposure.young_worker_hiring_impact:+.0%}")
        print(f"\n💡 KEY FINDING")
        print(f"  {exposure.key_finding}")
        
        # State-by-state recommendations
        print(f"\n🗺️ STATE RECOMMENDATIONS")
        for state in ["CT", "NY", "MA"]:
            rec = analyzer.get_program_recommendation(state, program)
            score = rec['demand_score']
            status = "🟢" if rec['recommendation'] == "LAUNCH" else "🟡" if rec['recommendation'] == "CAUTION" else "🔴"
            print(f"  {status} {state}: Score {score}/100 | {rec['recommendation']} | {rec['rationale']}")
            
            if rec['warnings']:
                for w in rec['warnings'][:2]:
                    print(f"     ⚠️ {w}")
            if rec['opportunities']:
                for o in rec['opportunities'][:2]:
                    print(f"     ✓ {o}")
        
        # Hiring warning
        warning = analyzer.get_hiring_warning(program)
        if warning:
            print(f"\n⚠️ HIRING WARNING")
            print(f"  {warning}")
    
    print("\n" + "=" * 70)
    print("Source: Massenkoff & McCrory (2026) 'Labor market impacts of AI'")
    print("       Anthropic Economic Index / https://huggingface.co/Anthropic/EconomicIndex")
    print("=" * 70)
