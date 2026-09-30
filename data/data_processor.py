"""
EduPredict MVP - Data Processor
Cleans and prepares IPEDS data for forecasting.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import os


class IPEDSProcessor:
    """
    Processes IPEDS enrollment data for AI programs.
    
    Filters for:
    - AI/ML/DS related programs
    - CT, NY, MA states only (MVP scope)
    - Graduate and undergraduate levels
    """
    
    # States in MVP scope
    MVP_STATES = ["CT", "NY", "MA"]
    
    # CIP codes for AI/ML/DS programs
    # 11.0101 - Computer Science
    # 11.0199 - Computer Science, Other
    # 11.0701 - Computer Science and related
    # 30.3001 - Artificial Intelligence (new code)
    # 30.9999 - Multi/Interdisciplinary Studies, Other
    AI_CIP_CODES = [
        "11.0101",   # Computer Science
        "11.0199",   # CS Other
        "11.0701",   # Computer Science
        "30.3001",   # Artificial Intelligence
        "30.9999",   # Interdisciplinary
    ]
    
    # Keywords to identify AI programs
    AI_KEYWORDS = [
        "artificial intelligence",
        "machine learning",
        "data science",
        "deep learning",
        "neural network",
        "AI",
        "ML",
        "computational",
        "analytics"
    ]
    
    def __init__(self, raw_data_path: str = None):
        """
        Initialize processor.
        
        Args:
            raw_data_path: Path to raw IPEDS CSV file
        """
        self.raw_data_path = raw_data_path
        self.processed_data = None
    
    def load_data(self, file_path: str = None) -> pd.DataFrame:
        """
        Load raw IPEDS data.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with raw data
        """
        path = file_path or self.raw_data_path
        if not path:
            raise ValueError("No data path provided")
        
        df = pd.read_csv(path, low_memory=False)
        print(f"Loaded {len(df)} records from {path}")
        return df
    
    def filter_mvp_states(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter for CT, NY, MA only."""
        # Look for state column (various naming conventions in IPEDS)
        state_cols = [col for col in df.columns if 'state' in col.lower()]
        
        if not state_cols:
            print("Warning: No state column found")
            return df
        
        state_col = state_cols[0]
        filtered = df[df[state_col].isin(self.MVP_STATES)].copy()
        print(f"Filtered to MVP states: {len(filtered)} records")
        return filtered
    
    def identify_ai_programs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify AI-related programs based on CIP codes and names.
        
        Args:
            df: DataFrame with program data
            
        Returns:
            DataFrame with AI programs flagged
        """
        # Check for CIP code column
        cip_cols = [col for col in df.columns if 'cip' in col.lower()]
        
        if cip_cols:
            cip_col = cip_cols[0]
            # Match CIP codes
            df['is_ai_cip'] = df[cip_col].astype(str).str[:7].isin(self.AI_CIP_CODES)
        else:
            df['is_ai_cip'] = False
        
        # Check program names for AI keywords
        name_cols = [col for col in df.columns if 'program' in col.lower() or 'cip' in col.lower()]
        
        if name_cols:
            name_col = name_cols[0]
            df['name_lower'] = df[name_col].astype(str).str.lower()
            df['is_ai_name'] = df['name_lower'].apply(
                lambda x: any(keyword in x for keyword in self.AI_KEYWORDS)
            )
        else:
            df['is_ai_name'] = False
        
        # Combined flag
        df['is_ai_program'] = df['is_ai_cip'] | df['is_ai_name']
        
        ai_programs = df[df['is_ai_program']].copy()
        print(f"Identified {len(ai_programs)} AI-related programs")
        
        return ai_programs
    
    def extract_enrollment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract enrollment numbers from IPEDS data.
        
        Args:
            df: DataFrame with AI programs
            
        Returns:
            DataFrame with enrollment summary
        """
        # Find enrollment columns (various naming in IPEDS)
        enroll_cols = [col for col in df.columns if any(
            term in col.lower() for term in ['enroll', 'student', 'headcount']
        )]
        
        if not enroll_cols:
            print("Warning: No enrollment columns found")
            return df
        
        # Get institution and state columns
        inst_cols = [col for col in df.columns if 'inst' in col.lower() or 'name' in col.lower()]
        state_cols = [col for col in df.columns if 'state' in col.lower()]
        
        # Build summary
        summary_cols = []
        if inst_cols:
            summary_cols.append(inst_cols[0])
        if state_cols:
            summary_cols.append(state_cols[0])
        summary_cols.extend(enroll_cols[:5])  # First 5 enrollment columns
        
        summary = df[summary_cols].copy()
        
        return summary
    
    def process(self, input_path: str = None, output_path: str = None) -> pd.DataFrame:
        """
        Full processing pipeline.
        
        Args:
            input_path: Path to raw data
            output_path: Path to save processed data
            
        Returns:
            Processed DataFrame
        """
        # Load
        df = self.load_data(input_path)
        
        # Filter states
        df = self.filter_mvp_states(df)
        
        # Identify AI programs
        df = self.identify_ai_programs(df)
        
        # Extract enrollment
        df = self.extract_enrollment_data(df)
        
        # Clean column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        self.processed_data = df
        
        # Save if path provided
        if output_path:
            df.to_csv(output_path, index=False)
            print(f"Saved processed data to {output_path}")
        
        return df
    
    def get_state_summary(self) -> pd.DataFrame:
        """Get enrollment summary by state."""
        if self.processed_data is None:
            raise ValueError("No processed data available. Run process() first.")
        
        # Find state and enrollment columns
        state_col = [c for c in self.processed_data.columns if 'state' in c][0]
        enroll_cols = [c for c in self.processed_data.columns if any(
            x in c for x in ['enroll', 'student', 'headcount']
        )]
        
        if enroll_cols:
            summary = self.processed_data.groupby(state_col)[enroll_cols[0]].sum().reset_index()
            summary.columns = ['state', 'total_enrollment']
            return summary
        
        return pd.DataFrame()


def quick_process(input_file: str, output_file: str = None) -> pd.DataFrame:
    """
    Quick process function.
    
    Example:
        df = quick_process("ipeds_raw.csv", "ipeds_clean.csv")
    """
    processor = IPEDSProcessor(input_file)
    return processor.process(output_path=output_file)


if __name__ == "__main__":
    # Example usage
    raw_path = "/Users/munagalatarakanagaganesh/Documents/predict/ipeds_enrollment_raw.csv/Data_3-3-2026---237.csv"
    output_path = "data/processed/ipeds_ai_programs.csv"
    
    if os.path.exists(raw_path):
        df = quick_process(raw_path, output_path)
        print(f"\nProcessed {len(df)} AI programs")
        print("\nState summary:")
        print(processor.get_state_summary())
    else:
        print(f"Raw data not found at {raw_path}")