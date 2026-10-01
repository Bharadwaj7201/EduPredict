# EduPredict Pro

**AI Degree Program Planning & Decision Intelligence Tool**

A professional decision-support platform for evaluating AI degree-program opportunities using enrollment forecasting, scenario analysis, ROI modeling, labor-market intelligence, and AI exposure analysis.

🚀 **Live Demo:** https://edupredict-b250.onrender.com

📦 **GitHub:** https://github.com/Bharadwaj7201/EduPredict

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What's Different

Unlike other AI education tools, EduPredict:
- **No Streamlit** -- Pure Flask + HTML/CSS/JS for professional deployment
- **Anthropic 2026 Research** -- Latest AI labor market data (Massenkoff & McCrory)
- **Observed Exposure** -- Real usage data, not just theoretical capabilities
- **Honest Predictions** -- Shows coverage gaps, hiring slowdowns, and warnings
- **AWS EC2 Ready** -- Production deployment with Gunicorn + Nginx

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, Flask, Gunicorn |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Charts** | Plotly.js |
| **Data & Modeling** | Pandas, NumPy, Statsmodels |
| **Database** | SQLite, SQLAlchemy |
| **Reporting** | FPDF2 |
| **Deployment** | GitHub + Render + Gunicorn |

---

## Quick Start (Local)

```bash
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

---
## Live Deployment

EduPredict Pro is deployed as a production Flask web service using Gunicorn.

**Live Application:**  
https://edupredict-b250.onrender.com

### Production Start Command

```bash
gunicorn -w 2 -b 0.0.0.0:$PORT app:app

Build Command : pip install -r requirements.txt




```
Edupredict-Pro/
├── app.py                      # Flask application (main entry point)
├── models/
│   ├── forecasting.py          # Enrollment forecasting engine
│   ├── roi_calculator.py       # ROI and financial analysis
│   └── job_market.py           # AI exposure analysis (Anthropic 2026)
├── templates/
│   └── index.html              # Main dashboard UI (pink theme)
├── static/                     # CSS, JS, assets
├── data/raw/                   # CSV data files
├── requirements.txt            # Flask dependencies (no Streamlit)
├── Dockerfile                  # Container config
├── ec2-userdata.sh            # AWS auto-deploy script
└── AWS-DEPLOY.md              # Detailed deployment guide
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/api/forecast` | POST | Generate enrollment forecast, ROI, and market analysis |
| `/api/scenarios` | POST | Compare forecasting scenarios |
| `/api/states` | POST | Compare state-level market conditions |
| `/api/validate` | GET | Validate all 162 combinations |
| `/api/ai-report/<program>` | GET | Generate AI exposure analysis |
| `/api/report` | POST | Generate downloadable PDF report |
| `/health` | GET | Application health check |

---

## Key Features

### 1. AI Exposure Analysis (Anthropic 2026)
- **Observed Exposure**: Real Claude usage data
- **Coverage Gap**: 61% gap between theory (94%) and reality (33%)
- **BLS Impact**: -0.6pp employment growth per 10% exposure
- **Young Worker Alert**: -14% hiring for age 22-25 in exposed roles

### 2. Enrollment Forecasting
- 3-year projections with confidence intervals
- 162 validated input combinations
- Scenario analysis (Baseline/Optimistic/Conservative)

### 3. ROI Calculator
- Tuition revenue vs. program costs
- Break-even analysis
- Payback period calculations

### 4. Interactive Visualizations
- Enrollment projection charts (Plotly.js)
- ROI pie charts
- Scenario comparison bar charts
- State comparison charts

---

## Success Criteria

**Test:** MS in AI + International + FA26 + Baseline + CT

| Metric | Expected | Actual |
|--------|----------|--------|
| Year 1 | 40 students | ✅ 40 |
| 3-Year Pool | 131 students | ✅ 131 |
| ROI | 3.43x | ✅ 3.43x |
| AI Exposure | 65% (HIGH) | ✅ Data Scientists |
| Demand Score | 80/100 | ✅ 80 |

---

## Data Sources

- **BLS Occupational Employment Statistics** (May 2023)
- **Anthropic Economic Index** (March 2026)
  - Massenkoff & McCrory: "Labor market impacts of AI: A new measure and early evidence"
- **IPEDS Institutional Data** (2023-2024)

---

## Author
Bharadwaj Gottimukkula 
Here is the live demo - https://edupredict-b250.onrender.com/

Built for higher education leadership decision-making.
