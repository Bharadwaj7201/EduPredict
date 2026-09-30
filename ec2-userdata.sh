#!/bin/bash
# EduPredict Pro - Flask EC2 User Data Script
# Deploys Flask app with Gunicorn on AWS EC2
# Paste this into "User data" when launching EC2 instance
# App will be live at http://<PUBLIC-IP> after ~3-5 minutes

exec > /var/log/edupredict-deploy.log 2>&1
set -e

echo "=== EduPredict Pro Flask Auto-Deploy ==="
echo "Started: $(date)"

# Update system
echo "📦 Updating system..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl nginx

# Clone repository
echo "📁 Cloning repository..."
cd /home/ubuntu
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

# Install dependencies
echo "📚 Installing dependencies..."
pip3 install --break-system-packages -r requirements.txt

# Create systemd service for Gunicorn
echo "⚙️ Creating Gunicorn service..."
cat > /etc/systemd/system/edupredict.service <<'EOF'
[Unit]
Description=EduPredict Pro Flask App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Edupredict-Pro
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/python3 -m gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx as reverse proxy (optional but recommended)
echo "🔧 Configuring Nginx..."
cat > /etc/nginx/sites-available/edupredict <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Enable Nginx config
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/edupredict /etc/nginx/sites-enabled/

# Set permissions
chown -R ubuntu:ubuntu /home/ubuntu/Edupredict-Pro

# Start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable edupredict
systemctl start edupredict
systemctl restart nginx

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR-INSTANCE-IP")

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "App URL: http://${PUBLIC_IP}"
echo "Health Check: http://${PUBLIC_IP}/health"
echo "Finished: $(date)"
echo ""
echo "To check status: sudo systemctl status edupredict"
echo "To view logs: sudo journalctl -u edupredict -f"
