# AWS EC2 Deployment Guide (Student Account)

Deploy EduPredict Pro to AWS EC2 using AWS Academy Learner Lab.

**Time needed:** ~10 minutes (mostly waiting for auto-deploy)

---

## Prerequisites

- AWS Academy Learner Lab access
- Security group with ports 22 (SSH) and 8501 (Streamlit) open

---

## Step 1: Start Your Lab

1. Go to **AWS Academy** > **Learner Lab**
2. Click **Start Lab** (wait for green circle)
3. Click **AWS** to open the console
4. Make sure region is **us-east-1** (N. Virginia)

---

## Step 2: Launch EC2 Instance

1. Go to **EC2** > **Launch Instance**
2. Configure:

| Setting | Value |
|---------|-------|
| Name | `edupredict-pro` |
| AMI | **Ubuntu Server 24.04 LTS** (Free tier) |
| Instance type | **t2.micro** (Free tier) |
| Key pair | Create new or select existing |
| Network | Allow SSH (port 22) from My IP |

3. **Security Group** -- Click "Edit" next to Network settings:
   - Keep SSH (port 22) rule
   - Click **Add security group rule**:
     - Type: **Custom TCP**
     - Port range: **8501**
     - Source: **0.0.0.0/0** (Anywhere)
     - Description: `Streamlit App`

4. **Advanced Details** (expand at bottom):
   - Scroll to **User data**
   - Paste this entire script:

```bash
#!/bin/bash
exec > /var/log/edupredict-deploy.log 2>&1
set -e

apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl

cd /home/ubuntu
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

python3 -m pip install --break-system-packages -r requirements.txt

cat > /etc/systemd/system/edupredict.service <<SVCEOF
[Unit]
Description=EduPredict Pro Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Edupredict-Pro
ExecStart=/usr/bin/python3 -m streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5
Environment=HOME=/home/ubuntu

[Install]
WantedBy=multi-user.target
SVCEOF

chown -R ubuntu:ubuntu /home/ubuntu/Edupredict-Pro
systemctl daemon-reload
systemctl enable edupredict
systemctl start edupredict
```

5. Click **Launch instance**

---

## Step 3: Access Your App

1. Wait **3-5 minutes** for auto-deploy to finish
2. Go to **EC2** > **Instances**
3. Click on your instance
4. Copy the **Public IPv4 address**
5. Open in browser: `http://<YOUR-IP>:8501`

The app should be live with the full dashboard.

---

## Troubleshooting

### App not loading after 5 minutes?

SSH into the instance and check the deploy log:

```bash
ssh -i your-key.pem ubuntu@<PUBLIC-IP>
sudo cat /var/log/edupredict-deploy.log
```

Check if the service is running:

```bash
sudo systemctl status edupredict
```

Restart the service:

```bash
sudo systemctl restart edupredict
```

### Security group not working?

Make sure port 8501 is open:
1. Go to **EC2** > **Security Groups**
2. Select your instance's security group
3. **Inbound rules** > **Edit** > Add rule:
   - Type: Custom TCP
   - Port: 8501
   - Source: 0.0.0.0/0

### Lab session timing out?

AWS Academy labs have a ~4 hour limit. The app only runs while the lab is active. For permanent hosting, use [Streamlit Cloud](https://share.streamlit.io).

---

## Alternative: Docker on EC2

If you prefer Docker, SSH into your instance and run:

```bash
sudo apt-get update -y && sudo apt-get install -y docker.io
sudo systemctl start docker
cd /home/ubuntu
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro
sudo docker build -t edupredict-pro .
sudo docker run -d -p 8501:8501 --restart always edupredict-pro
```

---

## Architecture

```
User Browser
     |
     v
AWS EC2 (t2.micro, Ubuntu 24.04)
     |
     +-- systemd service (auto-start)
     |      |
     |      +-- Streamlit (port 8501)
     |             |
     |             +-- ui/app.py (dashboard)
     |             +-- models/ (forecasting, ROI, job market)
     |             +-- data/raw/ (BLS, IPEDS CSVs)
     |
     +-- Security Group
            +-- Port 22 (SSH)
            +-- Port 8501 (Streamlit)
```

---

## Cost

- **t2.micro:** Free tier eligible (750 hours/month)
- **Storage:** 8 GB EBS (free tier)
- **Data transfer:** Minimal
- **Total:** $0 with student account

---

*For permanent deployment, use [Streamlit Cloud](https://share.streamlit.io) -- it's free and doesn't expire.*
