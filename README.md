````markdown
#EduPredict Pro

AI Degree Program Planning & Decision Intelligence Tool

A professional decision-support platform for evaluating AI degree-program opportunities using enrollment forecasting, scenario analysis, ROI modeling, labor-market intelligence, and AI exposure analysis.

🚀 **Live Demo:**  
https://edupredict-b250.onrender.com/

📦 **GitHub Repository:**  
https://github.com/Bharadwaj7201/EduPredict

[Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
[Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
[License](https://img.shields.io/badge/License-MIT-green)

---

Overview

EduPredict Pro is an end-to-end analytics and decision-intelligence platform designed to help higher-education decision makers evaluate potential AI degree programs.

The platform combines:

- Enrollment forecasting
- Scenario analysis
- ROI and financial modeling
- Labor-market intelligence
- AI exposure analysis
- Interactive data visualization
- Automated PDF reporting

The application is built with **Flask, Python, HTML/CSS/JavaScript, Plotly.js, and SQLAlchemy**, and is deployed as a production web service using **Gunicorn and Render**.

---

What's Different

EduPredict Pro focuses on combining quantitative forecasting with labor-market intelligence rather than relying on a single metric.

Key differentiators

- **Production Flask Application** — Built with Flask and standard HTML/CSS/JavaScript rather than Streamlit
- **Anthropic 2026 Research** — Incorporates AI labor-market research from the Anthropic Economic Index
- **Observed AI Exposure** — Uses observed usage data alongside theoretical capability measures
- **Scenario-Based Forecasting** — Evaluates multiple program, market, and scenario combinations
- **Financial Decision Support** — Combines enrollment projections with ROI, break-even, and payback analysis
- **Automated Reporting** — Generates downloadable PDF reports for analysis results

---

Live Deployment

EduPredict Pro is deployed as a production Flask web application using Gunicorn.

### Live Application

🚀 **EduPredict Pro:**  
https://edupredict-b250.onrender.com/

### Build Command

```bash
pip install -r requirements.txt
````

### Production Start Command

```bash
gunicorn -w 2 -b 0.0.0.0:$PORT app:app
```

---

## Technology Stack

| Layer                | Technology                 |
| -------------------- | -------------------------- |
| **Backend**          | Python, Flask, Gunicorn    |
| **Frontend**         | HTML5, CSS3, JavaScript    |
| **Visualization**    | Plotly.js                  |
| **Data & Modeling**  | Pandas, NumPy, Statsmodels |
| **Database**         | SQLite, SQLAlchemy         |
| **Reporting**        | FPDF2                      |
| **Deployment**       | Render + Gunicorn          |
| **Containerization** | Docker                     |

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Bharadwaj7201/EduPredict.git
cd EduPredict
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

### 4. Open the Dashboard

Open:

```text
http://localhost:5000
```

---

## Project Structure

```text
Edupredict-Pro/
├── app.py                      # Flask application and API routes
│
├── models/
│   ├── forecasting.py          # Enrollment forecasting engine
│   ├── roi_calculator.py       # ROI and financial analysis
│   └── job_market.py           # AI exposure and labor-market analysis
│
├── templates/
│   └── index.html              # Main dashboard interface
│
├── static/                     # CSS, JavaScript, and frontend assets
│
├── data/
│   └── raw/                    # Source CSV data files
│
├── tests/                      # Application validation and tests
│
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── ec2-userdata.sh             # AWS deployment automation
├── AWS-DEPLOY.md               # AWS deployment documentation
└── README.md                   # Project documentation
```

---

## API Endpoints

| Endpoint                   | Method | Description                                            |
| -------------------------- | ------ | ------------------------------------------------------ |
| `/`                        | GET    | Main dashboard                                         |
| `/api/forecast`            | POST   | Generate enrollment forecast, ROI, and market analysis |
| `/api/scenarios`           | POST   | Compare forecasting scenarios                          |
| `/api/states`              | POST   | Compare state-level market conditions                  |
| `/api/validate`            | GET    | Validate all 162 program-market combinations           |
| `/api/ai-report/<program>` | GET    | Generate AI exposure analysis                          |
| `/api/report`              | POST   | Generate a downloadable PDF report                     |
| `/health`                  | GET    | Application health check                               |

---

## Key Features

### 1. AI Exposure Analysis

Analyzes AI exposure and labor-market indicators using integrated research and labor-market data.

* **Observed Exposure:** Real Claude usage data
* **Coverage Gap:** 61% gap between theory (94%) and observed exposure (33%)
* **BLS Impact:** -0.6 percentage points employment growth per 10% exposure
* **Young Worker Alert:** -14% hiring for ages 22–25 in exposed roles

---

### 2. Enrollment Forecasting

Provides multi-year enrollment projections for AI degree programs.

* 3-year enrollment projections
* Confidence intervals
* 162 validated program-market combinations
* Scenario analysis:

  * Baseline
  * Optimistic
  * Conservative

---

### 3. ROI & Financial Analysis

Evaluates the financial implications of launching an AI degree program.

* Tuition revenue analysis
* Program cost modeling
* Break-even analysis
* Payback period calculations
* ROI projections

---

### 4. Interactive Analytics

Interactive visualizations provide decision-makers with a clear view of forecast and market results.

* Enrollment projection charts
* ROI visualizations
* Scenario comparison charts
* State-level comparison charts
* Interactive Plotly.js dashboards

---

### 5. Automated Reporting

The platform can generate downloadable PDF reports containing analysis results.

* Forecast results
* Scenario analysis
* ROI metrics
* Market analysis
* Program-level insights

---

## Validation & Results

### Success Criteria

**Scenario:** MS in AI + International + FA26 + Baseline + Connecticut

| Metric            | Expected     | Actual            |
| ----------------- | ------------ | ----------------- |
| Year 1 Enrollment | 40 students  | ✅ 40              |
| 3-Year Enrollment | 131 students | ✅ 131             |
| ROI               | 3.43x        | ✅ 3.43x           |
| AI Exposure       | 65%          | ✅ Data Scientists |
| Demand Score      | 80/100       | ✅ 80              |

The application validates **162 program-market combinations** across supported programs, student populations, states, launch terms, and scenarios.

---

## Data Sources

EduPredict Pro incorporates data from the following sources:

### Labor Market Data

* **BLS Occupational Employment Statistics**
* May 2023 data

### AI Exposure Research

* **Anthropic Economic Index**
* March 2026
* Massenkoff & McCrory
* *Labor market impacts of AI: A new measure and early evidence*

### Education Data

* **IPEDS Institutional Data**
* 2023–2024

---

## Deployment

The current production application is deployed using **Render** with **Gunicorn**.

### Production Configuration

**Build Command**

```bash
pip install -r requirements.txt
```

**Start Command**

```bash
gunicorn -w 2 -b 0.0.0.0:$PORT app:app
```

### Application

🚀 **Live Demo:**
[https://edupredict-b250.onrender.com/](https://edupredict-b250.onrender.com/)

The repository also includes Docker and AWS deployment configuration for alternative deployment environments.

---

## Local Development

To run the application locally:

```bash
git clone https://github.com/Bharadwaj7201/EduPredict.git
cd EduPredict
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://localhost:5000
```

---

## Author

**Bharadwaj Gottimukkula**

GitHub:
[https://github.com/Bharadwaj7201](https://github.com/Bharadwaj7201)

---

## License

This project is licensed under the **MIT License**.

```

### What I changed from your old README

- Removed the **outdated Ganesh Munagala** GitHub/portfolio information. Your current repository is `Bharadwaj7201/EduPredict`. :contentReference[oaicite:0]{index=0}
- Replaced the long **AWS EC2 deployment instructions** with your actual current Render deployment, while still mentioning that the AWS/Docker files remain in the repository. The old README's EC2 section was extensive and based on the previous repository. :contentReference[oaicite:1]{index=1}
- Added your **live Render URL** prominently at the top.
- Added `/api/ai-report/<program>` and `/api/report` to the API section.
- Added **SQLAlchemy, Statsmodels, and FPDF2** to the technology stack because they are part of your current application.
- Added a proper **Overview** so recruiters understand the project before getting into implementation details.
- Consolidated deployment information so the README doesn't repeat the same commands.
- Kept your existing **AI exposure, forecasting, ROI, validation, and data-source terminology** rather than replacing the substance of your project. :contentReference[oaicite:2]{index=2}

**One thing I intentionally did not change:** the quantitative claims under AI Exposure Analysis and the Success Criteria. Those are project-specific claims from your existing README, so I preserved them rather than silently altering or “correcting” them. :contentReference[oaicite:3]{index=3}

Available next action: :contentReference[oaicite:4]{index=4}
```
