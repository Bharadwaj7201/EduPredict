#!/bin/bash

# AWS EC2 Deployment Script for EduPredict Pro
# Run this on your AWS EC2 instance after launching

echo "🎓 EduPredict Pro - AWS Deployment"
echo "===================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -y

# Install Python and pip
echo "🐍 Installing Python..."
sudo apt-get install -y python3 python3-pip python3-venv git

# Install Docker (optional but recommended)
echo "🐳 Installing Docker..."
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Clone repository
echo "📁 Cloning repository..."
cd ~
git clone https://github.com/GaneshMunagala714/Edupredict-Pro.git
cd Edupredict-Pro

# Install Python dependencies
echo "📚 Installing dependencies..."
pip3 install -r requirements.txt

# Create systemd service for auto-start
echo "⚙️ Creating auto-start service..."
sudo tee /etc/systemd/system/edupredict.service > /dev/null <<EOF
[Unit]
Description=EduPredict Pro Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Edupredict-Pro
ExecStart=/usr/bin/python3 -m streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start the service
echo "🚀 Starting EduPredict Pro..."
sudo systemctl daemon-reload
sudo systemctl enable edupredict
sudo systemctl start edupredict

# Check status
echo ""
echo "✅ Deployment Complete!"
echo ""
echo "App is running at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo ""
echo "📊 Service Status:"
sudo systemctl status edupredict --no-pager

# Show logs command
echo ""
echo "📋 Useful Commands:"
echo "  View logs: sudo journalctl -u edupredict -f"
echo "  Restart:   sudo systemctl restart edupredict"
echo "  Stop:      sudo systemctl stop edupredict"
