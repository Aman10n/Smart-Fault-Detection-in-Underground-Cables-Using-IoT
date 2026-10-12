"""
============================================================
  Smart Fault Detection in Underground Cables Using IoT
  Backend Server with IoT Sensor Simulation
  ECE Department - Final Year Project
============================================================
  
  IoT Sensors Simulated Per Segment:
    1. Temperature Sensor (DS18B20 equivalent)
    2. Current Transformer (CT Sensor)
    3. Voltage Sensor (PT - Potential Transformer)
    4. Insulation Resistance Sensor (Megger equivalent)
    5. Humidity/Moisture Sensor (SHT31 equivalent)
    6. Partial Discharge Sensor (HFCT based)
    
  Fault Detection Methods:
    - Time Domain Reflectometry (TDR)
    - Murray Loop Bridge Test
    - Thermal Profiling Analysis
    - Partial Discharge Analysis
    - Insulation Resistance Monitoring
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging
import os
import random
import math
import secrets
import time
import threading
from datetime import datetime
from collections import deque
from functools import wraps


logger = logging.getLogger(__name__)
API_VERSION = '1.0.0'

# ============================================================
# FLASK APPLICATION SETUP
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(32)

socketio_options = {'async_mode': 'threading'}
allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS')
if allowed_origins:
    socketio_options['cors_allowed_origins'] = [
        origin.strip() for origin in allowed_origins.split(',') if origin.strip()
    ]

socketio = SocketIO(app, **socketio_options)

# ============================================================
# CABLE NETWORK CONFIGURATION (33kV XLPE Underground Cable)
# ============================================================
CABLE_CONFIG = {
    'total_length': 10.0,           # Total cable length in km
    'num_segments': 20,             # Number of monitoring segments
    'cable_type': 'XLPE 33kV Underground',
    'conductor': 'Copper (300 sq.mm)',
    'rated_voltage': 33.0,          # kV
    'rated_current': 400.0,         # Amps
    'resistance_per_km': 0.0601,    # Ω/km at 20°C
    'capacitance_per_km': 0.21,     # µF/km
    'inductance_per_km': 0.38,      # mH/km
    'char_impedance': 42.5,         # Ω (characteristic impedance)
    'insulation_resistance_min': 100,  # MΩ (minimum acceptable)
    'max_operating_temp': 90,       # °C for XLPE insulation
    'propagation_velocity': 1.7e8,  # m/s in XLPE cable (~57% of c)
    'dielectric_constant': 2.3,     # XLPE relative permittivity
}

# ============================================================
# FAULT TYPE DEFINITIONS
# ============================================================
FAULT_TYPES = {
    'short_circuit': {
        'name': 'Short Circuit',
        'icon': '⚡',
        'severity': 'CRITICAL',
        'color': '#ff0040',
        'description': 'Line-to-line or line-to-ground short circuit detected. '
                      'Caused by insulation breakdown between conductors or to earth.'
    },
    'open_circuit': {
        'name': 'Open Circuit',
        'icon': '🔌',
        'severity': 'HIGH',
        'color': '#ff6600',
        'description': 'Cable conductor discontinuity detected. '
                      'Caused by mechanical damage or conductor burnout.'
    },
    'ground_fault': {
        'name': 'Ground Fault',
        'icon': '⏚',
        'severity': 'HIGH',
        'color': '#ff9900',
        'description': 'Insulation failure causing earth leakage current. '
                      'Partial breakdown of cable insulation to ground.'
    },
    'degradation': {
        'name': 'Cable Degradation',
        'icon': '📉',
        'severity': 'MEDIUM',
        'color': '#ffcc00',
        'description': 'Gradual insulation deterioration detected. '
                      'Aging effects causing increased partial discharge activity.'
    },
    'water_ingress': {
        'name': 'Water Ingress',
        'icon': '💧',
        'severity': 'MEDIUM',
        'color': '#0099ff',
        'description': 'Moisture penetration in cable joint or outer sheath. '
                      'Can lead to water treeing and eventual failure.'
    },
    'thermal_fault': {
        'name': 'Thermal Hotspot',
        'icon': '🔥',
        'severity': 'HIGH',
        'color': '#ff3300',
        'description': 'Abnormal temperature rise detected at cable joint. '
                      'Caused by high-resistance connection or overloading.'
    }
}


def synchronized(method):
    """Serialize access to mutable cable-network state."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)
    return wrapper


# ============================================================
# CABLE SEGMENT CLASS (IoT Sensor Node)
# ============================================================
class CableSegment:
    """
    Represents a monitored segment of underground cable.
    Each segment has 6 IoT sensors deployed in a sensor node.
    
    In a real deployment, each segment would have:
    - Arduino/ESP32 based sensor node
    - LoRaWAN/NB-IoT connectivity
    - Solar + battery power supply
    - IP67 rated enclosure
    """
    
    def __init__(self, seg_id, start_km, end_km):
        self.id = seg_id
        self.start_km = start_km
        self.end_km = end_km
        self.mid_km = (start_km + end_km) / 2
        self.length = end_km - start_km
        
        # Baseline values (normal operation)
        self.base_temp = 22 + random.uniform(-3, 5)  # Ambient underground temp
        self.base_current = CABLE_CONFIG['rated_current'] * random.uniform(0.55, 0.75)
        self.base_voltage = CABLE_CONFIG['rated_voltage'] * random.uniform(0.97, 1.02)
        self.base_insulation_r = 1000 + random.uniform(-100, 200)   # MΩ
        self.base_humidity = 35 + random.uniform(-5, 5)              # %RH
        self.base_pd = random.uniform(0.5, 3.0)                     # pC (picocoulombs)
        
        # Current real-time readings
        self.temperature = self.base_temp
        self.current = self.base_current
        self.voltage = self.base_voltage
        self.insulation_resistance = self.base_insulation_r
        self.humidity = self.base_humidity
        self.partial_discharge = self.base_pd
        self.health = 100.0
        
        # GPS coordinates for visualization (simulated route)
        angle = (seg_id / CABLE_CONFIG['num_segments']) * math.pi * 0.4
        self.lat = 28.6139 + seg_id * 0.002 + math.sin(angle) * 0.005
        self.lng = 77.2090 + seg_id * 0.003 + math.cos(angle) * 0.003
        
        # Fault state
        self.fault_type = None
        self.fault_active = False
        self.fault_start_time = None
    
    def update_normal(self):
        """Simulate normal IoT sensor readings with realistic noise"""
        t = time.time()
        
        # Temperature: slow diurnal variation + noise
        self.temperature = (self.base_temp 
                          + 2.0 * math.sin(t / 600)       # Slow oscillation
                          + random.gauss(0, 0.3))          # Sensor noise
        
        # Current: load variation pattern
        self.current = (self.base_current 
                       + 20 * math.sin(t / 120)            # Load variation
                       + random.gauss(0, 3))               # Noise
        self.current = max(0, self.current)
        
        # Voltage: slight variations
        self.voltage = (self.base_voltage 
                       + 0.2 * math.sin(t / 180)
                       + random.gauss(0, 0.05))
        
        # Insulation resistance: stable with small drift
        self.insulation_resistance = (self.base_insulation_r 
                                     + random.gauss(0, 10)
                                     + 15 * math.sin(t / 300))
        
        # Humidity: slow environmental changes
        self.humidity = (self.base_humidity 
                        + 3 * math.sin(t / 400)
                        + random.gauss(0, 1))
        self.humidity = max(0, min(100, self.humidity))
        
        # Partial discharge: occasional spikes
        self.partial_discharge = abs(self.base_pd + random.gauss(0, 0.3))
        if random.random() < 0.02:  # 2% chance of small spike
            self.partial_discharge += random.uniform(2, 5)
        
        # Health score
        self.health = min(100, max(0, 92 + random.uniform(0, 8)))
    
    def apply_fault(self, fault_type):
        """Inject a fault into this segment"""
        self.fault_type = fault_type
        self.fault_active = True
        self.fault_start_time = datetime.now()
    
    def update_with_fault(self):
        """Update sensor readings with active fault effects"""
        if not self.fault_active:
            self.update_normal()
            return
        
        ft = self.fault_type
        noise = random.gauss(0, 1)
        
        if ft == 'short_circuit':
            self.temperature = self.base_temp + random.uniform(45, 85) + noise
            self.current = CABLE_CONFIG['rated_current'] * random.uniform(3.5, 8.0)
            self.voltage = CABLE_CONFIG['rated_voltage'] * random.uniform(0.05, 0.35)
            self.insulation_resistance = random.uniform(0.01, 3)
            self.partial_discharge = random.uniform(80, 250)
            self.humidity = self.base_humidity + random.uniform(0, 5)
            self.health = random.uniform(2, 12)
            
        elif ft == 'open_circuit':
            self.temperature = self.base_temp + random.uniform(-2, 5)
            self.current = random.uniform(0, 1.5)
            self.voltage = random.uniform(0, 0.3)
            self.insulation_resistance = self.base_insulation_r * 0.85
            self.partial_discharge = random.uniform(0, 4)
            self.humidity = self.base_humidity
            self.health = random.uniform(18, 32)
            
        elif ft == 'ground_fault':
            self.temperature = self.base_temp + random.uniform(12, 30)
            self.current = self.base_current + random.uniform(60, 180)
            self.voltage = self.base_voltage * random.uniform(0.45, 0.75)
            self.insulation_resistance = random.uniform(0.5, 15)
            self.humidity = 55 + random.uniform(0, 30)
            self.partial_discharge = random.uniform(25, 90)
            self.health = random.uniform(12, 28)
            
        elif ft == 'degradation':
            self.temperature = self.base_temp + random.uniform(5, 18)
            self.current = self.base_current + random.gauss(0, 25)
            self.voltage = self.base_voltage * random.uniform(0.82, 0.94)
            self.insulation_resistance = random.uniform(40, 180)
            self.partial_discharge = random.uniform(18, 55)
            self.humidity = self.base_humidity + random.uniform(0, 10)
            self.health = random.uniform(32, 52)
            
        elif ft == 'water_ingress':
            self.temperature = self.base_temp + random.uniform(2, 10)
            self.current = self.base_current + random.gauss(0, 18)
            self.voltage = self.base_voltage * random.uniform(0.85, 0.95)
            self.insulation_resistance = random.uniform(8, 65)
            self.humidity = 78 + random.uniform(0, 22)
            self.partial_discharge = random.uniform(12, 45)
            self.health = random.uniform(38, 58)
            
        elif ft == 'thermal_fault':
            self.temperature = self.base_temp + random.uniform(55, 110)
            self.current = self.base_current + random.uniform(35, 90)
            self.voltage = self.base_voltage * random.uniform(0.78, 0.93)
            self.insulation_resistance = random.uniform(15, 85)
            self.partial_discharge = random.uniform(28, 75)
            self.humidity = self.base_humidity + random.uniform(5, 15)
            self.health = random.uniform(8, 22)
    
    def clear_fault(self):
        """Remove active fault"""
        self.fault_type = None
        self.fault_active = False
        self.fault_start_time = None
    
    def to_dict(self):
        """Serialize segment data for API/WebSocket"""
        return {
            'id': self.id,
            'start_km': round(self.start_km, 2),
            'end_km': round(self.end_km, 2),
            'mid_km': round(self.mid_km, 2),
            'temperature': round(self.temperature, 1),
            'current': round(self.current, 1),
            'voltage': round(self.voltage, 2),
            'insulation_resistance': round(self.insulation_resistance, 1),
            'humidity': round(self.humidity, 1),
            'partial_discharge': round(self.partial_discharge, 2),
            'health': round(self.health, 1),
            'lat': round(self.lat, 6),
            'lng': round(self.lng, 6),
            'fault_active': self.fault_active,
            'fault_type': self.fault_type,
            'fault_info': FAULT_TYPES.get(self.fault_type) if self.fault_type else None,
        }


# ============================================================
# TDR (TIME DOMAIN REFLECTOMETRY) SIMULATION
# ============================================================
class TDRSimulator:
    """
    Simulates Time Domain Reflectometry for cable fault location.
    
    TDR works by sending a fast-rise electrical pulse down the cable
    and measuring reflections caused by impedance discontinuities.
    
    Reflection coefficient ρ = (Z2 - Z1) / (Z2 + Z1)
    where Z1 = cable impedance, Z2 = fault impedance
    
    - Short circuit (Z2 → 0): ρ → -1 (negative reflection)
    - Open circuit (Z2 → ∞): ρ → +1 (positive reflection)
    - Partial fault: |ρ| < 1
    """
    
    @staticmethod
    def generate_waveform(cable_length, fault_location=None, fault_type=None, num_points=500):
        """Generate TDR waveform data"""
        waveform = []
        v_prop = CABLE_CONFIG['propagation_velocity']
        
        # Time axis covers round-trip for full cable + margin
        max_distance = cable_length * 1.2
        total_time = 2 * max_distance * 1000 / v_prop * 1e6  # µs
        dt = total_time / num_points
        
        for i in range(num_points):
            t = i * dt  # Time in µs
            distance = (t * 1e-6 * v_prop) / 2 / 1000  # One-way distance (km)
            
            # === Incident Pulse (Gaussian) ===
            pulse_width = 0.018 * total_time
            pulse_center = 0.04 * total_time
            incident = 0.95 * math.exp(-((t - pulse_center) ** 2) / (2 * pulse_width ** 2))
            
            # === Cable Characteristic Impedance Baseline ===
            if distance > 0.1:
                attenuation = math.exp(-0.015 * distance)
                baseline = 0.50 * attenuation
            else:
                baseline = 0.5 + 0.3 * math.exp(-((t - pulse_center * 1.5) ** 2) / (2 * (pulse_width * 2) ** 2))
            
            # Small impedance variations along cable (joints, etc.)
            baseline += 0.01 * math.sin(distance * 4) * math.exp(-0.02 * distance)
            
            # === Fault Reflection ===
            reflection = 0
            if fault_location is not None and fault_type is not None:
                fault_time = 2 * fault_location * 1000 / v_prop * 1e6 + pulse_center
                reflection_width = 0.025 * total_time
                
                # Reflection coefficient based on fault type
                rho_map = {
                    'short_circuit': -0.85,
                    'open_circuit': 0.90,
                    'ground_fault': -0.50,
                    'degradation': -0.20,
                    'water_ingress': -0.30,
                    'thermal_fault': -0.40,
                }
                rho = rho_map.get(fault_type, 0)
                
                reflection = rho * math.exp(-((t - fault_time) ** 2) / (2 * reflection_width ** 2))
                
                # Secondary reflection (smaller)
                reflection += rho * 0.15 * math.exp(-((t - fault_time * 1.3) ** 2) / (2 * (reflection_width * 1.5) ** 2))
            
            # === End-of-Cable Reflection ===
            end_time = 2 * cable_length * 1000 / v_prop * 1e6 + pulse_center
            end_width = 0.025 * total_time
            end_reflection = 0.25 * math.exp(-((t - end_time) ** 2) / (2 * end_width ** 2))
            
            # === Noise ===
            noise = random.gauss(0, 0.008)
            
            value = incident + baseline + reflection + end_reflection + noise
            
            waveform.append({
                'time': round(t, 4),
                'amplitude': round(value, 4),
                'distance': round(distance, 3)
            })
        
        return waveform


# ============================================================
# MURRAY LOOP BRIDGE TEST SIMULATION
# ============================================================
class MurrayLoopTest:
    """
    Simulates Murray Loop Bridge Test for precise fault location.
    
    The Murray Loop test is a bridge method used to locate
    faults in underground cables. It requires a sound (healthy)
    cable running parallel to the faulty cable.
    
    Formula: Fault Distance = (R_a / (R_a + R_b)) × 2L
    
    where:
    - R_a, R_b = Bridge arm resistances (adjusted for balance)
    - L = Total cable length
    """
    
    @staticmethod
    def calculate(cable_length, fault_distance, r_per_km):
        """Simulate Murray Loop bridge measurement"""
        # Total loop resistance
        R_loop = 2 * cable_length * r_per_km
        
        # Fault-side resistance
        R_fault = fault_distance * r_per_km
        
        # Bridge balance point (with realistic measurement noise)
        R_a = R_fault + random.gauss(0, 0.0008)
        R_b = R_loop - R_fault + random.gauss(0, 0.0008)
        
        # Calculate measured distance
        measured_distance = (R_a / (R_a + R_b)) * 2 * cable_length
        
        # Measurement uncertainty
        measured_distance += random.gauss(0, 0.03)
        measured_distance = max(0, min(cable_length, measured_distance))
        
        error = abs(measured_distance - fault_distance)
        
        return {
            'measured_distance': round(measured_distance, 3),
            'actual_distance': round(fault_distance, 3),
            'error_km': round(error, 3),
            'error_meters': round(error * 1000, 1),
            'error_percent': round(error / cable_length * 100, 2),
            'accuracy': round((1 - error / cable_length) * 100, 2),
            'R_a': round(R_a, 6),
            'R_b': round(R_b, 6),
            'R_loop': round(R_loop, 4),
            'bridge_ratio': round(R_a / (R_a + R_b), 6) if (R_a + R_b) > 0 else 0,
        }


# ============================================================
# CABLE NETWORK (Main System)
# ============================================================
class CableNetwork:
    """
    Main cable network system managing all segments,
    fault detection, and IoT sensor simulation.
    """
    
    def __init__(self):
        self.lock = threading.RLock()
        self.segments = []
        self.fault_log = deque(maxlen=100)
        self.active_faults = {}
        self.system_start_time = datetime.now()
        self.tdr_waveform = []
        self.murray_result = None
        self.total_faults_detected = 0
        
        # Initialize cable segments
        seg_length = CABLE_CONFIG['total_length'] / CABLE_CONFIG['num_segments']
        for i in range(CABLE_CONFIG['num_segments']):
            start = round(i * seg_length, 3)
            end = round((i + 1) * seg_length, 3)
            self.segments.append(CableSegment(i, start, end))
        
        # Initial TDR scan (clean cable)
        self.tdr_waveform = TDRSimulator.generate_waveform(CABLE_CONFIG['total_length'])
        
        logger.info("Initialized %s cable segments", len(self.segments))
        logger.info("Deployed %s IoT sensors", len(self.segments) * 6)
    
    @synchronized
    def inject_fault(self, segment_id=None, fault_type=None):
        """Inject a fault into the cable network"""
        if segment_id is None:
            # Pick a random segment that doesn't already have a fault
            available = [s.id for s in self.segments if not s.fault_active]
            if not available:
                return None
            segment_id = random.choice(available)
        
        if fault_type is None:
            fault_type = random.choice(list(FAULT_TYPES.keys()))

        if fault_type not in FAULT_TYPES:
            return None
        
        if segment_id < 0 or segment_id >= len(self.segments):
            return None
        
        segment = self.segments[segment_id]
        
        # Don't inject if already faulted
        if segment.fault_active:
            return None
        
        segment.apply_fault(fault_type)
        self.total_faults_detected += 1
        
        fault_info = {
            'id': f"FLT-{self.total_faults_detected:04d}",
            'segment_id': segment_id,
            'fault_type': fault_type,
            'fault_name': FAULT_TYPES[fault_type]['name'],
            'severity': FAULT_TYPES[fault_type]['severity'],
            'location_km': round(segment.mid_km, 2),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'ACTIVE',
            'icon': FAULT_TYPES[fault_type]['icon'],
            'color': FAULT_TYPES[fault_type]['color'],
            'description': FAULT_TYPES[fault_type]['description'],
        }
        
        self.active_faults[segment_id] = fault_info
        self.fault_log.appendleft(fault_info)
        
        # Auto-run TDR scan
        self.tdr_waveform = TDRSimulator.generate_waveform(
            CABLE_CONFIG['total_length'],
            segment.mid_km,
            fault_type
        )
        
        # Auto-run Murray Loop
        self.murray_result = MurrayLoopTest.calculate(
            CABLE_CONFIG['total_length'],
            segment.mid_km,
            CABLE_CONFIG['resistance_per_km']
        )
        self.murray_result['fault_type'] = FAULT_TYPES[fault_type]['name']
        self.murray_result['fault_severity'] = FAULT_TYPES[fault_type]['severity']
        
        return fault_info
    
    @synchronized
    def clear_fault(self, segment_id=None):
        """Clear faults from the cable network"""
        if segment_id is None:
            for seg in self.segments:
                seg.clear_fault()
            self.active_faults.clear()
        else:
            if 0 <= segment_id < len(self.segments):
                self.segments[segment_id].clear_fault()
                self.active_faults.pop(segment_id, None)
        
        # Refresh TDR (clean)
        if not self.active_faults:
            self.tdr_waveform = TDRSimulator.generate_waveform(CABLE_CONFIG['total_length'])
            self.murray_result = None
        else:
            # TDR for remaining fault
            fault = list(self.active_faults.values())[0]
            seg = self.segments[fault['segment_id']]
            self.tdr_waveform = TDRSimulator.generate_waveform(
                CABLE_CONFIG['total_length'],
                seg.mid_km,
                seg.fault_type
            )
    
    @synchronized
    def update(self):
        """Update all segment sensor readings"""
        for seg in self.segments:
            if seg.fault_active:
                seg.update_with_fault()
            else:
                seg.update_normal()
    
    @synchronized
    def get_overview(self):
        """Get system overview statistics"""
        healths = [s.health for s in self.segments]
        temps = [s.temperature for s in self.segments]
        currents = [s.current for s in self.segments]
        voltages = [s.voltage for s in self.segments]
        
        uptime = (datetime.now() - self.system_start_time).total_seconds()
        
        return {
            'cable_health': round(sum(healths) / len(healths), 1),
            'min_health': round(min(healths), 1),
            'max_temperature': round(max(temps), 1),
            'avg_temperature': round(sum(temps) / len(temps), 1),
            'avg_current': round(sum(currents) / len(currents), 1),
            'avg_voltage': round(sum(voltages) / len(voltages), 2),
            'max_current': round(max(currents), 1),
            'active_fault_count': len(self.active_faults),
            'total_faults_detected': self.total_faults_detected,
            'total_sensors': CABLE_CONFIG['num_segments'] * 6,
            'uptime_seconds': int(uptime),
            'system_status': 'FAULT' if self.active_faults else 'NORMAL',
        }
    
    @synchronized
    def get_temperature_profile(self):
        """Get temperature values along cable length"""
        return [
            {'km': round(s.mid_km, 2), 'temp': round(s.temperature, 1), 'fault': s.fault_active}
            for s in self.segments
        ]
    
    @synchronized
    def get_all_data(self):
        """Get complete system data package for WebSocket streaming"""
        return {
            'overview': self.get_overview(),
            'cable_config': CABLE_CONFIG,
            'segments': [s.to_dict() for s in self.segments],
            'active_faults': list(self.active_faults.values()),
            'tdr_waveform': self.tdr_waveform,
            'murray_result': self.murray_result,
            'temp_profile': self.get_temperature_profile(),
            'fault_log': list(self.fault_log),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }


# ============================================================
# INITIALIZE SYSTEM
# ============================================================
network = CableNetwork()
simulation_active = True


def simulation_loop():
    """Background IoT simulation thread (1 Hz update rate)"""
    global simulation_active
    while simulation_active:
        try:
            network.update()
            data = network.get_all_data()
            socketio.emit('sensor_data', data)
            socketio.sleep(1)
        except Exception:
            logger.exception("Simulation update failed")
            socketio.sleep(1)


# ============================================================
# FLASK ROUTES
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/config')
def api_config():
    return jsonify(CABLE_CONFIG)


@app.route('/api/fault-types')
def api_fault_types():
    return jsonify(FAULT_TYPES)


@app.route('/api/data')
def api_data():
    return jsonify(network.get_all_data())


@app.route('/api/health')
def api_health():
    """Lightweight readiness endpoint for operators and container probes."""
    overview = network.get_overview()
    return jsonify({
        'status': 'degraded' if overview['active_fault_count'] else 'healthy',
        'service': 'smart-fault-detection',
        'version': API_VERSION,
        'uptime_seconds': overview['uptime_seconds'],
        'active_faults': overview['active_fault_count'],
    })


def parse_segment_id(value, *, allow_none=True):
    """Validate and normalize a segment identifier received from a client."""
    if value is None and allow_none:
        return None
    if isinstance(value, bool):
        raise ValueError('Segment ID must be an integer')
    try:
        segment_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('Segment ID must be an integer') from exc
    if not 0 <= segment_id < len(network.segments):
        raise ValueError(f'Segment ID must be between 0 and {len(network.segments) - 1}')
    return segment_id


def parse_fault_type(value):
    """Validate a requested fault type, allowing None for a random fault."""
    if value in (None, ''):
        return None
    if value not in FAULT_TYPES:
        raise ValueError('Unknown fault type')
    return value


# ============================================================
# SOCKET.IO EVENT HANDLERS
# ============================================================
@socketio.on('connect')
def handle_connect():
    logger.info("Dashboard client connected")
    emit('connected', {'status': 'ok', 'config': CABLE_CONFIG})
    emit('sensor_data', network.get_all_data())


@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Dashboard client disconnected")


@socketio.on('inject_fault')
def handle_inject_fault(data):
    """Handle fault injection request from dashboard"""
    data = data if isinstance(data, dict) else {}
    try:
        segment_id = parse_segment_id(data.get('segment_id'))
        fault_type = parse_fault_type(data.get('fault_type'))
    except ValueError as exc:
        emit('operation_error', {'message': str(exc)})
        return
    
    fault_info = network.inject_fault(segment_id, fault_type)
    
    if fault_info:
        emit('fault_alert', fault_info, broadcast=True)
        emit('sensor_data', network.get_all_data(), broadcast=True)
        logger.warning(
            "Fault injected: %s at %.2f km",
            fault_info['fault_name'],
            fault_info['location_km'],
        )
    else:
        emit('operation_error', {'message': 'Could not inject fault; the segment may already be faulted'})


@socketio.on('clear_fault')
def handle_clear_fault(data):
    """Handle fault clearing request"""
    data = data if isinstance(data, dict) else {}
    try:
        segment_id = parse_segment_id(data.get('segment_id'), allow_none=False)
    except ValueError as exc:
        emit('operation_error', {'message': str(exc)})
        return
    network.clear_fault(segment_id)
    emit('fault_cleared', {'segment_id': segment_id}, broadcast=True)
    emit('sensor_data', network.get_all_data(), broadcast=True)
    logger.info("Fault cleared for segment %s", segment_id)


@socketio.on('clear_all_faults')
def handle_clear_all(data=None):
    """Clear all active faults"""
    network.clear_fault(None)
    emit('all_faults_cleared', {}, broadcast=True)
    emit('sensor_data', network.get_all_data(), broadcast=True)
    logger.info("All faults cleared")


@socketio.on('run_tdr')
def handle_run_tdr(data=None):
    """Run TDR test on demand"""
    active = list(network.active_faults.values())
    if active:
        fault = active[0]
        seg = network.segments[fault['segment_id']]
        waveform = TDRSimulator.generate_waveform(
            CABLE_CONFIG['total_length'],
            seg.mid_km,
            seg.fault_type
        )
    else:
        waveform = TDRSimulator.generate_waveform(CABLE_CONFIG['total_length'])
    
    network.tdr_waveform = waveform
    emit('tdr_result', {'waveform': waveform}, broadcast=True)
    logger.info("TDR test completed")


@socketio.on('run_murray')
def handle_run_murray(data=None):
    """Run Murray Loop test on demand"""
    active = list(network.active_faults.values())
    if active:
        fault = active[0]
        seg = network.segments[fault['segment_id']]
        result = MurrayLoopTest.calculate(
            CABLE_CONFIG['total_length'],
            seg.mid_km,
            CABLE_CONFIG['resistance_per_km']
        )
        result['fault_type'] = fault['fault_name']
        result['fault_severity'] = fault['severity']
        network.murray_result = result
        emit('murray_result', result, broadcast=True)
        logger.info("Murray Loop test located fault at %.3f km", result['measured_distance'])
    else:
        emit('murray_result', {'error': 'No active fault to locate'}, broadcast=True)


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == '__main__':
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', 'INFO').upper(),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    print("\n" + "=" * 62)
    print("  Smart Fault Detection in Underground Cables Using IoT")
    print("  IoT Sensor Simulation System")
    print("  ECE Department - Final Year Project")
    print("=" * 62)
    print(f"\n  Cable Type    : {CABLE_CONFIG['cable_type']}")
    print(f"  Cable Length  : {CABLE_CONFIG['total_length']} km")
    print(f"  Segments      : {CABLE_CONFIG['num_segments']}")
    print(f"  IoT Sensors   : {CABLE_CONFIG['num_segments'] * 6}")
    print(f"  Rated Voltage : {CABLE_CONFIG['rated_voltage']} kV")
    print(f"  Rated Current : {CABLE_CONFIG['rated_current']} A")
    print(f"\n  Dashboard     : http://localhost:5000")
    print("=" * 62 + "\n")
    
    # Start IoT simulation in background thread
    sim_thread = threading.Thread(target=simulation_loop, daemon=True)
    sim_thread.start()
    print("  [OK] IoT Simulation Engine started (1 Hz update rate)\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
