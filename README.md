# EduPredict Pro

**AI Degree Program Planning & Decision Intelligence Tool**

A professional dashboard for College Deans to evaluate launching AI degree programs. Built with **Flask** (no Streamlit), HTML/CSS/JS, and Plotly.js.

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
| **Backend** | Flask + Gunicorn |
| **Frontend** | HTML5, CSS3, Vanilla JS |
| **Charts** | Plotly.js (3D surfaces, interactive) |
| **Data** | Pandas, NumPy |
| **Deployment** | AWS EC2, Docker, Gunicorn |

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

## Deploy to AWS EC2 (Student Account)

### 1. Start Your Lab
- AWS Academy → Learner Lab → Start Lab
- Make sure you're in **us-east-1** (N. Virginia)

### 2. Launch EC2 Instance

**EC2** → **Launch Instance**

| Setting | Value |
|---------|-------|
| Name | `edupredict-pro` |
| AMI | Ubuntu Server 24.04 LTS |
| Type | t2.micro (Free tier) |
| Key pair | Create new or select |

**Security Group:**
- SSH (port 22) - My IP
- HTTP (port 80) - 0.0.0.0/0

**Advanced Details → User Data:**
```bash
#!/bin/bash
exec > /var/log/edupredict-deploy.log 2>&1
set -e

echo "=== EduPredict Pro Flask Auto-Deploy ==="

apt-get update -y
apt-get install -y python3 python3-pip git nginx

cd /home/ubuntu
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

pip3 install --break-system-packages -r requirements.txt

cat > /etc/systemd/system/edupredict.service <<'EOF'
[Unit]
Description=EduPredict Pro Flask App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Edupredict-Pro
ExecStart=/usr/bin/python3 -m gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/nginx/sites-available/edupredict <<'EOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/edupredict /etc/nginx/sites-enabled/

chown -R ubuntu:ubuntu /home/ubuntu/Edupredict-Pro

systemctl daemon-reload
systemctl enable edupredict
systemctl start edupredict
systemctl restart nginx

echo "=== DEPLOY COMPLETE ==="
echo "App URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
```

### 3. Access Your App

Wait **3-5 minutes**, then visit:
```
http://<YOUR-EC2-PUBLIC-IP>
```

No port number needed (port 80).

---

## Project Structure

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

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/api/forecast` | POST | Generate enrollment forecast |
| `/api/scenarios` | POST | Compare all scenarios |
| `/api/states` | POST | Compare all states |
| `/api/validate` | GET | Validate all 162 combinations |
| `/health` | GET | Health check |

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

**Ganesh Munagala** — [GitHub](https://github.com/GaneshMunagala714) | [Portfolio](https://ganeshmunagala714.github.io/Ganesh-Portfolio)

Built for higher education leadership decision-making.
