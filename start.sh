#!/bin/bash
# Smart Fault Detection in Underground Cables Using IoT
# One-click start script for Linux/Mac

echo ""
echo "  =============================================================="
echo "   ⚡ Smart Fault Detection in Underground Cables Using IoT"
echo "   📡 IoT Simulation System"
echo "   🎓 ECE Department - Final Year Project"
echo "  =============================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  ❌ Python3 is not installed!"
    echo "  📥 Install: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "  ✓ Python3 found"
echo ""

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "  📦 Creating virtual environment..."
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
    echo ""
fi

# Activate
source venv/bin/activate

# Install deps
echo "  📦 Installing dependencies..."
pip install -r requirements.txt --quiet
echo "  ✓ Dependencies installed"
echo ""

echo "  🚀 Starting IoT Server..."
echo "  🌐 Open your browser at: http://localhost:5000"
echo ""
echo "  Press Ctrl+C to stop the server"
echo "  =============================================================="
echo ""

python app.py
