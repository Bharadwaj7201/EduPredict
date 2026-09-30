# IPEDS Data Download Guide

> Step-by-step instructions to download actual enrollment data for EduPredict MVP

## Quick Summary

**What you need:** IPEDS Completions data for 2021-2023, filtered for AI/CS programs in CT/NY/MA

**Time required:** 10-15 minutes

**Result:** `ipeds_completions_2021_2023.csv` in your `data/raw/` folder

---

## Step-by-Step Instructions

### Step 1: Go to IPEDS Data Center

Open this URL:
```
https://nces.ed.gov/ipeds/datacenter/Login.aspx?gotoReportId=7&fromResults=true&backText=Data+Center&showButton=true&startYear=2021&endYear=2023&resultYear=2023
```

Or navigate manually:
1. Go to https://nces.ed.gov/ipeds/datacenter/
2. Click **"Compare Institutions"**
3. Click **"By Group"**

### Step 2: Select Survey Data

1. Click **"Completions"** (this is the survey name)
2. Select years:
   - Check **2021-22**
   - Check **2022-23**
   - Check **2023-24** (if available)
3. Click **"Continue"**

### Step 3: Select Institutions

1. Under **"Select Institutions by:"** choose **State**
2. Select these 3 states:
   - [x] Connecticut
   - [x] New York
   - [x] Massachusetts
3. Click **"Continue"**

### Step 4: Select Variables (CIP Codes)

This is the MOST IMPORTANT step. You need AI/ML/CS programs only.

**Select these CIP Codes:**

| CIP Code | Program Name |
|----------|-------------|
| 11.0101 | Computer and Information Sciences, General |
| 11.0199 | Computer Science, Other |
| 11.0701 | Computer Science (various) |
| 30.3001 | Artificial Intelligence (NEW code) |
| 11.0801 | Web Page Design/Digital/Multimedia |
| 11.1003 | Information Technology |
| 30.0801 | Mathematics and Computer Science |
| 30.7100 | Data Science, General |

**How to select:**
1. Click **"CIP Code - 6-digit"**
2. Check the boxes for the codes above
3. Click **"Continue"**

### Step 5: Select Award Levels

Select these:
- [x] Bachelor's degrees
- [x] Master's degrees
- [x] Doctor's degrees - research/scholarship

Click **"Continue"**

### Step 6: Generate Report

1. Review your selections (should show ~40-50 institutions)
2. Click **"Continue"**
3. Wait for data to load (30-60 seconds)

### Step 7: Download Data

1. Click **"Download"** button
2. Choose **"CSV"** format
3. Save file as: `ipeds_completions_2021_2023.csv`
4. Move file to: `EduPredict-MVP/data/raw/`

---

## Alternative: Download Complete Survey File

If the above is too complex, download the full completion files:

1. Go to: https://nces.ed.gov/ipeds/use-the-data/download-access-database
2. Download "Completions" files for:
   - 2021-22: `C2021_C.csv`
   - 2022-23: `C2022_C.csv`
   - 2023-24: `C2023_C.csv` (when available)

3. Use this Python script to extract what you need:

```python
import pandas as pd

# Load files
df_2021 = pd.read_csv("C2021_C.csv", low_memory=False)
df_2022 = pd.read_csv("C2022_C.csv", low_memory=False)
df_2023 = pd.read_csv("C2023_C.csv", low_memory=False)

# CIP codes for AI/ML/CS
cip_codes = ['11.0101', '11.0199', '11.0701', '30.3001', '30.7100']

# Filter for MVP states and CIP codes
states = ['CT', 'NY', 'MA']

for df in [df_2021, df_2022, df_2023]:
    # Filter states (column name varies, usually 'STABBR' or similar)
    state_col = [c for c in df.columns if 'state' in c.lower() or 'stabbr' in c.lower()][0]
    df_filtered = df[df[state_col].isin(states)]
    
    # Filter CIP codes (column usually 'CIPCODE')
    cip_col = [c for c in df.columns if 'cip' in c.lower()][0]
    df_filtered = df_filtered[df_filtered[cip_col].isin(cip_codes)]
    
    # Save
    year = df['YEAR'].iloc[0] if 'YEAR' in df.columns else 'unknown'
    df_filtered.to_csv(f"ipeds_filtered_{year}.csv", index=False)

# Combine all years
import glob
all_files = glob.glob("ipeds_filtered_*.csv")
df_combined = pd.concat([pd.read_csv(f) for f in all_files])
df_combined.to_csv("data/raw/ipeds_completions_2021_2023.csv", index=False)
```

---

## What the Final File Should Look Like

Required columns (IPEDS standard):
- `UNITID` - Institution ID
- `INSTNM` - Institution name
- `STABBR` - State abbreviation
- `CIPCODE` - CIP code
- `AWLEVEL` - Award level (1=Certificate, 3=Associate, 5=Bachelor, 7=Master, 17=Doctor)
- `CTOTALT` - Total completions
- `CTOTALM` - Male completions
- `CTOTALW` - Female completions
- `YEAR` - Academic year

---

## After Download: Run Processor

Once you have the file, run:

```bash
cd EduPredict-MVP
python data/data_processor.py
```

This will:
1. Clean the IPEDS data
2. Filter for your 3 programs (MS AI, BS AI, AI Cyber)
3. Split international vs domestic estimates
4. Save to `data/processed/`

---

## Need Help?

If the IPEDS site is confusing:

1. **Email me the screenshots** of where you're stuck
2. **Alternative:** I can build the system with sample data and you can swap in real data later
3. **Sample data works** for the professor demo - it shows the system architecture works

---

**Recommended approach:** Use the sample data we already have for Sprint 2. Download real IPEDS data in Sprint 4 (before May 4 delivery). The professor cares about a working system more than perfect data at this stage.
