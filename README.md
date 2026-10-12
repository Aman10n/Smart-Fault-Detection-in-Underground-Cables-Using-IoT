# ⚡ Smart Fault Detection in Underground Cables Using IoT

> **ECE Department — Final Year Project**  
> Real-time IoT-based monitoring and fault detection system for underground power cables with TDR analysis, Murray Loop testing, and comprehensive sensor simulation.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![Socket.IO](https://img.shields.io/badge/Socket.IO-Real--time-orange?logo=socket.io)
![License](https://img.shields.io/badge/License-Academic-purple)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [IoT Sensor Simulation](#iot-sensor-simulation)
- [Fault Detection Methods](#fault-detection-methods)
- [Dashboard Guide](#dashboard-guide)
- [API Reference](#api-reference)
- [Development](#development)
- [Container Deployment](#container-deployment)

---

## 🔍 Overview

This project simulates an IoT-based system for detecting and locating faults in underground power cables. It demonstrates real-world concepts used in power distribution networks using:

- **6 different IoT sensors** per monitoring segment
- **20 monitoring segments** along a 10 km cable route
- **120 total IoT sensors** providing real-time data
- **6 fault types** with realistic electrical effects
- **TDR (Time Domain Reflectometry)** for fault location
- **Murray Loop Bridge Test** for precise fault distance measurement

---

## ✨ Features

| Feature | Description |
|---------|------------|
| 🌡️ Real-time Monitoring | 120 IoT sensors streaming data at 1 Hz |
| 📊 TDR Analysis | Time Domain Reflectometry waveform simulation |
| 🔌 Murray Loop Test | Bridge circuit method for fault location |
| 🗺️ Cable Visualization | Animated underground cable route with sensor nodes |
| 🌡️ Thermal Profiling | Temperature distribution along cable length |
| ⚡ Fault Injection | Simulate 6 different fault types on demand |
| 🔔 Alert System | Real-time fault notifications with overlay alerts |
| 📈 Health Monitoring | Per-segment and overall cable health scoring |
| 📱 Responsive Design | Works on desktop, tablet, and mobile |

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Backend** | Python + Flask | Simple, no build step, widely installed |
| **Real-time** | Flask-SocketIO | WebSocket for live sensor data streaming |
| **Frontend** | Vanilla HTML/CSS/JS | Zero build tools, no npm/webpack needed |
| **Charts** | HTML5 Canvas | No chart library dependencies |
| **Transport** | simple-websocket | Lightweight WebSocket for Flask-SocketIO |

**Total dependencies: Only 3 Python packages!**

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** installed ([Download Python](https://www.python.org/downloads/))
- Make sure "Add Python to PATH" is checked during installation

### Windows (One-Click)

```bash
# Just double-click start.bat
start.bat
```

### Manual Start

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python app.py
```

### Open Dashboard
Navigate to: **http://localhost:5000**

---

## ⚙️ Configuration

The application works with safe local defaults. Override these environment variables when needed:

| Variable | Default | Purpose |
|----------|---------|---------|
| `HOST` | `127.0.0.1` | Server bind address; use `0.0.0.0` inside a container |
| `PORT` | `5000` | HTTP and WebSocket port |
| `SECRET_KEY` | Random per process | Stable Flask secret for deployed environments |
| `CORS_ALLOWED_ORIGINS` | Same-origin only | Comma-separated trusted Socket.IO origins |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `DEBUG` | `false` | Enable Flask debug mode for local development only |

PowerShell example:

```powershell
$env:PORT = "8080"
$env:SECRET_KEY = "replace-with-a-long-random-value"
python app.py
```

---

## 📁 Project Structure

```
smart-cable-fault-detection/
├── app.py                      # Flask backend + IoT simulator
├── requirements.txt            # Python dependencies (only 3!)
├── requirements-dev.txt        # Test and lint dependencies
├── pyproject.toml              # Pytest and Ruff configuration
├── start.bat                   # Windows one-click launcher
├── start.sh                    # Linux/Mac launcher
├── README.md                   # This file
├── .github/workflows/ci.yml    # Automated quality checks
├── tests/                      # Simulation, HTTP, and Socket.IO tests
├── templates/
│   └── index.html              # Dashboard HTML
└── static/
    ├── css/
    │   └── style.css           # Dashboard styles
    └── js/
        └── app.js              # Frontend logic
```

---

## 📡 IoT Sensor Simulation

### Sensors Per Segment (6 types)

| Sensor | Real-world Equivalent | Parameter | Unit |
|--------|----------------------|-----------|------|
| Temperature | DS18B20 | Cable temperature | °C |
| Current | CT (Current Transformer) | Load current | A |
| Voltage | PT (Potential Transformer) | Cable voltage | kV |
| Insulation Resistance | Megger | Insulation health | MΩ |
| Humidity | SHT31 | Moisture level | %RH |
| Partial Discharge | HFCT Sensor | PD magnitude | pC |

### Cable Configuration

| Parameter | Value |
|-----------|-------|
| Cable Type | XLPE 33kV Underground |
| Total Length | 10 km |
| Conductor | Copper (300 sq.mm) |
| Rated Voltage | 33 kV |
| Rated Current | 400 A |
| Resistance | 0.0601 Ω/km |
| Capacitance | 0.21 µF/km |
| Propagation Velocity | 1.7 × 10⁸ m/s |

---

## 🔬 Fault Detection Methods

### 1. Time Domain Reflectometry (TDR)

TDR sends a fast electrical pulse down the cable and analyzes reflections:

```
Reflection Coefficient: ρ = (Z₂ - Z₁) / (Z₂ + Z₁)

Short Circuit (Z₂ → 0):  ρ → -1 (negative reflection)
Open Circuit (Z₂ → ∞):   ρ → +1 (positive reflection)
```

**Fault Distance = (v × t) / 2** where:
- v = propagation velocity (1.7 × 10⁸ m/s)
- t = round-trip time of reflection

### 2. Murray Loop Bridge Test

Bridge method for precise fault location:

```
Fault Distance = (Rₐ / (Rₐ + R_b)) × 2L

Where:
- Rₐ, R_b = Bridge arm resistances at balance
- L = Total cable length
```

### 3. Supported Fault Types

| Fault Type | Severity | Effects |
|-----------|----------|---------|
| ⚡ Short Circuit | CRITICAL | Current spike, voltage drop, temp rise |
| 🔌 Open Circuit | HIGH | Current drops to ~0, no voltage beyond fault |
| ⏚ Ground Fault | HIGH | Leakage current, insulation resistance drop |
| 📉 Degradation | MEDIUM | Gradual PD increase, insulation weakening |
| 💧 Water Ingress | MEDIUM | Humidity spike, insulation resistance drop |
| 🔥 Thermal Hotspot | HIGH | Extreme temperature rise at fault point |

---

## 🖥️ Dashboard Guide

### Overview Cards
- **System Uptime** — How long the monitoring system has been running
- **Active IoT Sensors** — Total sensors deployed (120 = 20 segments × 6 sensors)
- **Cable Health** — Average health score across all segments (0-100%)
- **Active Faults** — Number of currently detected faults

### Cable Route Visualization
- Interactive canvas showing the 10 km underground cable route
- Green nodes = healthy, Yellow = warning, Red = fault
- Pulsing red circles indicate active fault locations
- Animated data flow pulses along the cable

### TDR Waveform
- Shows incident pulse and any fault reflections
- Red marker indicates detected fault position
- Displays reflection coefficient and fault distance

### Controls
- **Inject Fault** — Simulate a cable fault (random or specific)
- **Clear All Faults** — Reset the cable to healthy state
- **Run TDR Test** — Execute Time Domain Reflectometry
- **Murray Loop Test** — Run bridge circuit test for fault location

---

## 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard page |
| `/api/config` | GET | Cable configuration |
| `/api/fault-types` | GET | Available fault types |
| `/api/data` | GET | Current system data |
| `/api/health` | GET | Service readiness and fault status |
| `/api/faults` | POST | Inject a fault; accepts `segment_id` and `fault_type` |
| `/api/faults` | DELETE | Clear all active faults |
| `/api/faults/<segment_id>` | DELETE | Clear one segment's fault |
| `/api/diagnostics/tdr` | POST | Run and return a TDR scan |
| `/api/diagnostics/murray` | POST | Run a Murray Loop test for an active fault |

Example:

```bash
curl -X POST http://localhost:5000/api/faults \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 4, "fault_type": "water_ingress"}'
```

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `sensor_data` | Server → Client | Real-time sensor data (1 Hz) |
| `fault_alert` | Server → Client | New fault notification |
| `inject_fault` | Client → Server | Inject a fault |
| `clear_all_faults` | Client → Server | Clear all faults |
| `run_tdr` | Client → Server | Run TDR test |
| `run_murray` | Client → Server | Run Murray Loop test |
| `operation_error` | Server → Client | Validation or operation failure |

---

## 🧪 Development

```bash
pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
node --check static/js/app.js
```

Every push and pull request runs these checks on Python 3.10 and 3.13 through GitHub Actions.

---

## 🐳 Container Deployment

```bash
docker build -t smart-fault-detection .
docker run --rm -p 5000:5000 \
  -e SECRET_KEY="replace-with-a-long-random-value" \
  smart-fault-detection
```

The image runs as an unprivileged user and includes a health check against `/api/health`. For a network-facing deployment, put the service behind a TLS-terminating reverse proxy and configure `CORS_ALLOWED_ORIGINS` explicitly.

---

## 🎓 Academic References

1. **Time Domain Reflectometry** — IEEE Std 400.4-2015
2. **Murray Loop Test** — IEC 60502 Cable Testing Standards
3. **XLPE Cable Properties** — IEEE Std 48-1996
4. **Partial Discharge Testing** — IEC 60270
5. **IoT in Power Systems** — IEEE Smart Grid Communications

---

## 📄 License

This project is created for academic purposes as part of the ECE Department Final Year Project.

---

<div align="center">

**Built with ❤️ for ECE Department**

*Smart Fault Detection in Underground Cables Using IoT*

</div>
