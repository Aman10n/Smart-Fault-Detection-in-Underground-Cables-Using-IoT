/**
 * ============================================================
 *  Smart Fault Detection in Underground Cables Using IoT
 *  Frontend Dashboard Application
 *  ECE Department - Final Year Project
 * ============================================================
 */

// ============================================================
// GLOBAL STATE
// ============================================================
const State = {
    socket: null,
    connected: false,
    data: null,
    cableConfig: null,
    animFrame: null,
    pulsePhase: 0,
    dataFlowOffset: 0,
};

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
    initControls();
    initSegmentSelect();
    updateClock();
    setInterval(updateClock, 1000);
    resizeCanvases();
    window.addEventListener('resize', resizeCanvases);
});

// ============================================================
// SOCKET.IO CONNECTION
// ============================================================
function initSocket() {
    State.socket = io();

    State.socket.on('connect', () => {
        State.connected = true;
        updateConnectionStatus('ONLINE', 'online');
        console.log('✓ Connected to IoT server');
    });

    State.socket.on('disconnect', () => {
        State.connected = false;
        updateConnectionStatus('OFFLINE', '');
    });

    State.socket.on('connected', (msg) => {
        State.cableConfig = msg.config;
        updateCableInfo();
    });

    State.socket.on('sensor_data', (data) => {
        State.data = data;
        if (!State.cableConfig && data.cable_config) {
            State.cableConfig = data.cable_config;
            updateCableInfo();
        }
        updateDashboard(data);
    });

    State.socket.on('fault_alert', (fault) => {
        showFaultOverlay(fault);
    });

    State.socket.on('fault_cleared', () => {
        // Data update will handle UI
    });

    State.socket.on('all_faults_cleared', () => {
        hideFaultOverlay();
    });

    State.socket.on('tdr_result', (data) => {
        if (data.waveform) {
            drawTDR(data.waveform);
        }
    });

    State.socket.on('murray_result', (data) => {
        updateMurrayResults(data);
    });
}

function updateConnectionStatus(text, className) {
    const dot = document.getElementById('system-status-dot');
    const txt = document.getElementById('system-status-text');
    dot.className = 'status-dot ' + className;
    txt.textContent = text;
}

// ============================================================
// CONTROL PANEL
// ============================================================
function initControls() {
    document.getElementById('btn-inject-fault').addEventListener('click', () => {
        const faultType = document.getElementById('fault-type-select').value || null;
        const segVal = document.getElementById('segment-select').value;
        const segmentId = segVal !== '' ? parseInt(segVal) : null;
        State.socket.emit('inject_fault', {
            fault_type: faultType,
            segment_id: segmentId,
        });
    });

    document.getElementById('btn-clear-faults').addEventListener('click', () => {
        State.socket.emit('clear_all_faults', {});
        hideFaultOverlay();
    });

    document.getElementById('btn-run-tdr').addEventListener('click', () => {
        State.socket.emit('run_tdr', {});
    });

    document.getElementById('btn-run-murray').addEventListener('click', () => {
        State.socket.emit('run_murray', {});
    });

    document.getElementById('fault-overlay-dismiss').addEventListener('click', () => {
        hideFaultOverlay();
    });
}

function initSegmentSelect() {
    const sel = document.getElementById('segment-select');
    for (let i = 0; i < 20; i++) {
        const opt = document.createElement('option');
        opt.value = i;
        const start = (i * 0.5).toFixed(1);
        const end = ((i + 1) * 0.5).toFixed(1);
        opt.textContent = `Seg ${i} (${start}-${end} km)`;
        sel.appendChild(opt);
    }
}

// ============================================================
// CLOCK
// ============================================================
function updateClock() {
    const now = new Date();
    document.getElementById('header-clock').textContent = now.toLocaleTimeString('en-US', { hour12: false });
}

// ============================================================
// DASHBOARD UPDATE (called every 1s)
// ============================================================
function updateDashboard(data) {
    updateOverviewCards(data.overview);
    updateSystemStatus(data.overview);
    drawCableRoute(data.segments, data.active_faults);
    drawTDR(data.tdr_waveform);
    drawTemperatureProfile(data.temp_profile);
    updateGauges(data.overview, data.segments);
    updateSensorTable(data.segments);
    updateFaultPanel(data.active_faults);
    if (data.murray_result) {
        updateMurrayResults(data.murray_result);
    }
    updateAlertLog(data.fault_log);
    document.getElementById('footer-timestamp').textContent = data.timestamp;
}

// ============================================================
// OVERVIEW CARDS
// ============================================================
function updateOverviewCards(overview) {
    // Uptime
    const h = Math.floor(overview.uptime_seconds / 3600);
    const m = Math.floor((overview.uptime_seconds % 3600) / 60);
    const s = overview.uptime_seconds % 60;
    document.getElementById('stat-uptime').textContent =
        `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

    // Sensors
    document.getElementById('stat-sensors').textContent = overview.total_sensors;

    // Health
    const health = overview.cable_health;
    document.getElementById('stat-health').textContent = health + '%';
    const healthBar = document.getElementById('health-bar');
    healthBar.style.width = health + '%';
    healthBar.className = 'bar-fill ' + (health > 80 ? 'bar-green' : health > 50 ? 'bar-orange' : 'bar-red');

    // Faults
    document.getElementById('stat-faults').textContent = overview.active_fault_count;
    const faultBar = document.getElementById('fault-bar');
    faultBar.style.width = Math.min(overview.active_fault_count * 25, 100) + '%';
    faultBar.className = 'bar-fill ' + (overview.active_fault_count > 0 ? 'bar-red' : 'bar-green');

    // Badge
    document.getElementById('sensor-count-badge').textContent = overview.total_sensors + ' Sensors';
}

function updateSystemStatus(overview) {
    if (overview.active_fault_count > 0) {
        updateConnectionStatus('FAULT DETECTED', 'fault');
    } else if (State.connected) {
        updateConnectionStatus('ONLINE', 'online');
    }
}

// ============================================================
// CABLE INFO
// ============================================================
function updateCableInfo() {
    const c = State.cableConfig;
    if (!c) return;
    document.getElementById('info-cable-type').textContent = c.cable_type || 'XLPE 33kV';
    document.getElementById('info-length').textContent = c.total_length + ' km';
    document.getElementById('info-conductor').textContent = c.conductor || 'Copper';
    document.getElementById('info-voltage').textContent = c.rated_voltage + ' kV';
    document.getElementById('info-current').textContent = c.rated_current + ' A';
    document.getElementById('info-segments').textContent = c.num_segments;
    document.getElementById('cable-type-badge').textContent = c.cable_type || 'XLPE 33kV';
}

// ============================================================
// CANVAS RESIZE
// ============================================================
function resizeCanvases() {
    resizeCanvas('cable-route-canvas');
    resizeCanvas('tdr-canvas');
    resizeCanvas('temp-canvas');
    // Redraw if data available
    if (State.data) {
        drawCableRoute(State.data.segments, State.data.active_faults);
        drawTDR(State.data.tdr_waveform);
        drawTemperatureProfile(State.data.temp_profile);
    }
}

function resizeCanvas(id) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
}

// ============================================================
// CABLE ROUTE VISUALIZATION (Canvas)
// ============================================================
function drawCableRoute(segments, activeFaults) {
    const canvas = document.getElementById('cable-route-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.getBoundingClientRect().width;
    const H = canvas.getBoundingClientRect().height;
    const dpr = window.devicePixelRatio || 1;

    ctx.clearRect(0, 0, W, H);

    const padL = 50, padR = 40, padT = 45, padB = 40;
    const routeW = W - padL - padR;
    const routeY = H / 2;
    const n = segments.length;

    // === Background elements ===
    // Ground layer
    ctx.fillStyle = 'rgba(30, 20, 10, 0.15)';
    ctx.fillRect(padL - 10, routeY + 20, routeW + 20, H - routeY - 20);

    // Ground line
    ctx.strokeStyle = 'rgba(120, 90, 50, 0.3)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padL - 10, routeY + 20);
    ctx.lineTo(padL + routeW + 10, routeY + 20);
    ctx.stroke();
    ctx.setLineDash([]);

    // "Underground" label
    ctx.fillStyle = 'rgba(120, 90, 50, 0.4)';
    ctx.font = '9px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('UNDERGROUND', padL, routeY + 34);

    // "Surface" label
    ctx.fillStyle = 'rgba(100, 140, 200, 0.3)';
    ctx.fillText('SURFACE', padL, routeY + 12);

    // Distance markers
    ctx.fillStyle = 'rgba(136, 146, 176, 0.5)';
    ctx.font = '9px JetBrains Mono, monospace';
    ctx.textAlign = 'center';
    for (let i = 0; i <= 10; i++) {
        const x = padL + (i / 10) * routeW;
        ctx.fillText(i + ' km', x, H - 8);

        // Tick marks
        ctx.strokeStyle = 'rgba(136, 146, 176, 0.15)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, routeY - 25);
        ctx.lineTo(x, routeY + 25);
        ctx.stroke();
    }

    // Title
    ctx.fillStyle = 'rgba(0, 212, 255, 0.6)';
    ctx.font = 'bold 10px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('CABLE ROUTE — 33kV XLPE UNDERGROUND', padL, 20);

    // === Data flow animation ===
    State.dataFlowOffset = (State.dataFlowOffset + 2) % 30;

    // === Draw cable (main line) ===
    const gradient = ctx.createLinearGradient(padL, 0, padL + routeW, 0);
    gradient.addColorStop(0, '#00d4ff');
    gradient.addColorStop(0.5, '#7b61ff');
    gradient.addColorStop(1, '#00d4ff');

    ctx.strokeStyle = gradient;
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.beginPath();

    for (let i = 0; i < n; i++) {
        const x = padL + (segments[i].mid_km / 10) * routeW;
        const y = routeY + Math.sin(i * 0.3) * 8;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Cable glow
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.12)';
    ctx.lineWidth = 12;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
        const x = padL + (segments[i].mid_km / 10) * routeW;
        const y = routeY + Math.sin(i * 0.3) * 8;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Data flow pulses
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.4)';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 26]);
    ctx.lineDashOffset = -State.dataFlowOffset;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
        const x = padL + (segments[i].mid_km / 10) * routeW;
        const y = routeY + Math.sin(i * 0.3) * 8;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.lineDashOffset = 0;

    // === Draw sensor nodes ===
    State.pulsePhase = (State.pulsePhase + 0.08) % (Math.PI * 2);

    for (let i = 0; i < n; i++) {
        const seg = segments[i];
        const x = padL + (seg.mid_km / 10) * routeW;
        const y = routeY + Math.sin(i * 0.3) * 8;
        const health = seg.health;

        let color, glowColor;
        if (seg.fault_active) {
            color = seg.fault_info ? seg.fault_info.color : '#ff0040';
            glowColor = color;
        } else if (health > 80) {
            color = '#00ff88';
            glowColor = 'rgba(0, 255, 136, 0.3)';
        } else if (health > 50) {
            color = '#ffaa00';
            glowColor = 'rgba(255, 170, 0, 0.3)';
        } else {
            color = '#ff0040';
            glowColor = 'rgba(255, 0, 64, 0.3)';
        }

        // Fault pulse ring
        if (seg.fault_active) {
            const pulseR = 12 + 8 * Math.sin(State.pulsePhase + i);
            ctx.beginPath();
            ctx.arc(x, y, pulseR, 0, Math.PI * 2);
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.3 + 0.3 * Math.sin(State.pulsePhase + i);
            ctx.stroke();
            ctx.globalAlpha = 1;
        }

        // Node glow
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fillStyle = glowColor;
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.15)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Segment label (every other segment)
        if (i % 2 === 0) {
            ctx.fillStyle = 'rgba(136, 146, 176, 0.6)';
            ctx.font = '8px JetBrains Mono, monospace';
            ctx.textAlign = 'center';
            ctx.fillText('S' + i, x, y - 14);
        }

        // Fault label
        if (seg.fault_active && seg.fault_info) {
            ctx.fillStyle = color;
            ctx.font = 'bold 9px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(seg.fault_info.icon + ' ' + seg.fault_info.name, x, y + 24);

            // Distance marker
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.font = '8px JetBrains Mono, monospace';
            ctx.fillText(seg.mid_km.toFixed(1) + ' km', x, y + 35);
        }
    }

    // Start/End labels
    ctx.fillStyle = 'rgba(0, 212, 255, 0.7)';
    ctx.font = 'bold 10px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('SUBSTATION A', padL, padT - 12);
    ctx.fillText('SUBSTATION B', padL + routeW, padT - 12);

    // Substation icons
    drawSubstationIcon(ctx, padL, routeY, '#00d4ff');
    drawSubstationIcon(ctx, padL + routeW, routeY, '#7b61ff');
}

function drawSubstationIcon(ctx, x, y, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x - 8, y - 10, 16, 20);
    ctx.beginPath();
    ctx.moveTo(x, y - 10);
    ctx.lineTo(x - 5, y - 18);
    ctx.lineTo(x + 5, y - 18);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
}

// ============================================================
// TDR WAVEFORM (Canvas)
// ============================================================
function drawTDR(waveform) {
    const canvas = document.getElementById('tdr-canvas');
    if (!canvas || !waveform || waveform.length === 0) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.getBoundingClientRect().width;
    const H = canvas.getBoundingClientRect().height;

    ctx.clearRect(0, 0, W, H);

    const padL = 55, padR = 20, padT = 30, padB = 30;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    // Find ranges
    let minAmp = Infinity, maxAmp = -Infinity;
    let maxDist = 0;
    for (const p of waveform) {
        if (p.amplitude < minAmp) minAmp = p.amplitude;
        if (p.amplitude > maxAmp) maxAmp = p.amplitude;
        if (p.distance > maxDist) maxDist = p.distance;
    }
    const ampRange = maxAmp - minAmp || 1;

    // Grid
    ctx.strokeStyle = 'rgba(136, 146, 176, 0.08)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
        const y = padT + (i / 5) * plotH;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(padL + plotW, y);
        ctx.stroke();
    }
    for (let i = 0; i <= 10; i++) {
        const x = padL + (i / 10) * plotW;
        ctx.beginPath();
        ctx.moveTo(x, padT);
        ctx.lineTo(x, padT + plotH);
        ctx.stroke();
    }

    // Axis labels
    ctx.fillStyle = 'rgba(136, 146, 176, 0.5)';
    ctx.font = '9px JetBrains Mono, monospace';
    ctx.textAlign = 'center';
    for (let i = 0; i <= 10; i++) {
        const x = padL + (i / 10) * plotW;
        const dist = (i / 10) * maxDist;
        ctx.fillText(dist.toFixed(1), x, H - 6);
    }
    ctx.fillText('Distance (km)', padL + plotW / 2, H - 0);

    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
        const y = padT + (i / 4) * plotH;
        const val = maxAmp - (i / 4) * ampRange;
        ctx.fillText(val.toFixed(2), padL - 6, y + 3);
    }

    // Title
    ctx.fillStyle = 'rgba(0, 212, 255, 0.6)';
    ctx.font = 'bold 10px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('TDR PULSE RESPONSE', padL, 16);

    ctx.textAlign = 'right';
    ctx.fillStyle = 'rgba(136, 146, 176, 0.4)';
    ctx.font = '9px JetBrains Mono, monospace';
    ctx.fillText('Amplitude (V)', padL + plotW, 16);

    // Waveform glow
    ctx.beginPath();
    for (let i = 0; i < waveform.length; i++) {
        const x = padL + (waveform[i].distance / maxDist) * plotW;
        const y = padT + plotH - ((waveform[i].amplitude - minAmp) / ampRange) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.15)';
    ctx.lineWidth = 6;
    ctx.stroke();

    // Waveform main line
    ctx.beginPath();
    for (let i = 0; i < waveform.length; i++) {
        const x = padL + (waveform[i].distance / maxDist) * plotW;
        const y = padT + plotH - ((waveform[i].amplitude - minAmp) / ampRange) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    const tdrGrad = ctx.createLinearGradient(padL, 0, padL + plotW, 0);
    tdrGrad.addColorStop(0, '#00d4ff');
    tdrGrad.addColorStop(0.5, '#00ff88');
    tdrGrad.addColorStop(1, '#7b61ff');
    ctx.strokeStyle = tdrGrad;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Fill under curve
    ctx.lineTo(padL + plotW, padT + plotH);
    ctx.lineTo(padL, padT + plotH);
    ctx.closePath();
    const fillGrad = ctx.createLinearGradient(0, padT, 0, padT + plotH);
    fillGrad.addColorStop(0, 'rgba(0, 212, 255, 0.08)');
    fillGrad.addColorStop(1, 'rgba(0, 212, 255, 0)');
    ctx.fillStyle = fillGrad;
    ctx.fill();

    // Detect and mark fault reflection
    // Look for significant negative or positive deviation from baseline
    let faultIdx = -1;
    let faultAmp = 0;
    const baseline = 0.5;
    for (let i = Math.floor(waveform.length * 0.15); i < Math.floor(waveform.length * 0.85); i++) {
        const dev = Math.abs(waveform[i].amplitude - baseline);
        if (dev > 0.15 && dev > Math.abs(faultAmp)) {
            // Check it's not the incident pulse (first 15%)
            if (waveform[i].distance > 0.5) {
                faultAmp = waveform[i].amplitude - baseline;
                faultIdx = i;
            }
        }
    }

    if (faultIdx > 0) {
        const fx = padL + (waveform[faultIdx].distance / maxDist) * plotW;
        const fy = padT + plotH - ((waveform[faultIdx].amplitude - minAmp) / ampRange) * plotH;

        // Fault marker line
        ctx.strokeStyle = 'rgba(255, 0, 64, 0.5)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(fx, padT);
        ctx.lineTo(fx, padT + plotH);
        ctx.stroke();
        ctx.setLineDash([]);

        // Fault marker dot
        ctx.beginPath();
        ctx.arc(fx, fy, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#ff0040';
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 0, 64, 0.5)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(fx, fy, 10, 0, Math.PI * 2);
        ctx.stroke();

        // Label
        ctx.fillStyle = '#ff0040';
        ctx.font = 'bold 10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('FAULT REFLECTION', fx, padT + 14);
        ctx.font = '9px JetBrains Mono, monospace';
        ctx.fillText(waveform[faultIdx].distance.toFixed(2) + ' km', fx, padT + 26);

        // Update TDR info
        const rho = faultAmp > 0 ? 'Positive (Open)' : 'Negative (Short/Ground)';
        document.getElementById('tdr-fault-info').textContent =
            `Fault at ${waveform[faultIdx].distance.toFixed(2)} km | ρ = ${faultAmp.toFixed(3)} (${rho})`;
        document.getElementById('tdr-fault-info').style.color = '#ff0040';
    } else {
        document.getElementById('tdr-fault-info').textContent = 'No fault reflection detected';
        document.getElementById('tdr-fault-info').style.color = '#00ff88';
    }
}

// ============================================================
// TEMPERATURE PROFILE (Canvas)
// ============================================================
function drawTemperatureProfile(profile) {
    const canvas = document.getElementById('temp-canvas');
    if (!canvas || !profile || profile.length === 0) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.getBoundingClientRect().width;
    const H = canvas.getBoundingClientRect().height;

    ctx.clearRect(0, 0, W, H);

    const padL = 55, padR = 20, padT = 30, padB = 30;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    let minT = Infinity, maxT = -Infinity;
    for (const p of profile) {
        if (p.temp < minT) minT = p.temp;
        if (p.temp > maxT) maxT = p.temp;
    }
    // Ensure reasonable range
    minT = Math.min(minT, 15);
    maxT = Math.max(maxT, 40);
    const tempRange = maxT - minT || 1;

    // Update badge
    document.getElementById('max-temp-badge').textContent = maxT.toFixed(1);

    // Grid
    ctx.strokeStyle = 'rgba(136, 146, 176, 0.08)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padT + (i / 4) * plotH;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(padL + plotW, y);
        ctx.stroke();

        // Y labels
        ctx.fillStyle = 'rgba(136, 146, 176, 0.5)';
        ctx.font = '9px JetBrains Mono, monospace';
        ctx.textAlign = 'right';
        const val = maxT - (i / 4) * tempRange;
        ctx.fillText(val.toFixed(0) + '°', padL - 6, y + 3);
    }

    // X labels
    ctx.textAlign = 'center';
    for (let i = 0; i <= 10; i++) {
        const x = padL + (i / 10) * plotW;
        ctx.fillText(i + '', x, H - 8);
    }
    ctx.fillText('Distance (km)', padL + plotW / 2, H - 0);

    // Title
    ctx.fillStyle = 'rgba(255, 157, 0, 0.6)';
    ctx.font = 'bold 10px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('THERMAL PROFILE', padL, 16);

    // Max operating temp line
    const maxOpY = padT + plotH - ((90 - minT) / tempRange) * plotH;
    if (maxOpY > padT && maxOpY < padT + plotH) {
        ctx.strokeStyle = 'rgba(255, 0, 64, 0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(padL, maxOpY);
        ctx.lineTo(padL + plotW, maxOpY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(255, 0, 64, 0.5)';
        ctx.font = '8px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('MAX (90°C)', padL + plotW, maxOpY - 4);
    }

    // Temperature bars + line
    const barWidth = plotW / profile.length * 0.6;

    for (let i = 0; i < profile.length; i++) {
        const p = profile[i];
        const x = padL + (p.km / 10) * plotW;
        const y = padT + plotH - ((p.temp - minT) / tempRange) * plotH;
        const barH = padT + plotH - y;

        // Color based on temperature
        let color;
        if (p.fault) {
            color = '#ff0040';
        } else if (p.temp > 70) {
            color = '#ff3300';
        } else if (p.temp > 45) {
            color = '#ff9d00';
        } else {
            color = '#00d4ff';
        }

        // Bar
        const barGrad = ctx.createLinearGradient(0, y, 0, padT + plotH);
        barGrad.addColorStop(0, color);
        barGrad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = barGrad;
        ctx.fillRect(x - barWidth / 2, y, barWidth, barH);

        // Top dot
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
    }

    // Temperature line
    ctx.beginPath();
    for (let i = 0; i < profile.length; i++) {
        const p = profile[i];
        const x = padL + (p.km / 10) * plotW;
        const y = padT + plotH - ((p.temp - minT) / tempRange) * plotH;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    const tempGrad = ctx.createLinearGradient(padL, 0, padL + plotW, 0);
    tempGrad.addColorStop(0, '#00d4ff');
    tempGrad.addColorStop(0.5, '#ff9d00');
    tempGrad.addColorStop(1, '#00d4ff');
    ctx.strokeStyle = tempGrad;
    ctx.lineWidth = 2;
    ctx.stroke();
}

// ============================================================
// GAUGES
// ============================================================
function updateGauges(overview, segments) {
    const config = State.cableConfig || { rated_current: 400, rated_voltage: 33 };

    // Current
    const currentPct = Math.min((overview.avg_current / config.rated_current) * 100, 100);
    document.getElementById('gauge-current').textContent = overview.avg_current + ' A';
    document.getElementById('current-gauge-fill').style.width = currentPct + '%';

    // Voltage
    const voltagePct = Math.min((overview.avg_voltage / config.rated_voltage) * 100, 100);
    document.getElementById('gauge-voltage').textContent = overview.avg_voltage + ' kV';
    document.getElementById('voltage-gauge-fill').style.width = voltagePct + '%';

    // Temperature
    const tempPct = Math.min((overview.max_temperature / 90) * 100, 100);
    document.getElementById('gauge-temp').textContent = overview.max_temperature + ' °C';
    document.getElementById('temp-gauge-fill').style.width = tempPct + '%';

    // Insulation resistance
    let avgInsR = 0;
    if (segments && segments.length > 0) {
        avgInsR = segments.reduce((s, seg) => s + seg.insulation_resistance, 0) / segments.length;
    }
    const insPct = Math.min((avgInsR / 1200) * 100, 100);
    document.getElementById('gauge-insulation').textContent = avgInsR.toFixed(0) + ' MΩ';
    document.getElementById('insulation-gauge-fill').style.width = insPct + '%';
}

// ============================================================
// SENSOR TABLE
// ============================================================
function updateSensorTable(segments) {
    const tbody = document.getElementById('sensor-table-body');
    if (!tbody) return;

    // Build rows
    let html = '';
    for (const seg of segments) {
        const isFault = seg.fault_active;
        const rowClass = isFault ? 'fault-row' : '';
        const healthColor = seg.health > 80 ? '#00ff88' : seg.health > 50 ? '#ffaa00' : '#ff0040';
        const healthBarColor = seg.health > 80 ? 'bar-green' : seg.health > 50 ? 'bar-orange' : 'bar-red';

        html += `<tr class="${rowClass}">
            <td>${seg.id}</td>
            <td>${seg.start_km.toFixed(1)} - ${seg.end_km.toFixed(1)} km</td>
            <td style="color: ${seg.temperature > 60 ? '#ff3300' : seg.temperature > 40 ? '#ffaa00' : '#e8ecf4'}">${seg.temperature}</td>
            <td style="color: ${seg.current > 500 ? '#ff0040' : '#e8ecf4'}">${seg.current}</td>
            <td>${seg.voltage}</td>
            <td style="color: ${seg.insulation_resistance < 100 ? '#ff0040' : '#e8ecf4'}">${seg.insulation_resistance}</td>
            <td>${seg.humidity}</td>
            <td style="color: ${seg.partial_discharge > 20 ? '#ff9d00' : '#e8ecf4'}">${seg.partial_discharge}</td>
            <td>
                <div class="health-cell">
                    <span style="color: ${healthColor}">${seg.health}%</span>
                    <div class="health-mini-bar">
                        <div class="health-mini-fill ${healthBarColor}" style="width: ${seg.health}%"></div>
                    </div>
                </div>
            </td>
            <td>
                ${isFault
                    ? `<span class="status-badge status-fault">${seg.fault_info ? seg.fault_info.icon : '⚡'} FAULT</span>`
                    : '<span class="status-badge status-ok">✓ OK</span>'
                }
            </td>
        </tr>`;
    }
    tbody.innerHTML = html;
}

// ============================================================
// FAULT PANEL
// ============================================================
function updateFaultPanel(activeFaults) {
    const noFaultMsg = document.getElementById('no-fault-msg');
    const faultDetails = document.getElementById('fault-details');

    if (!activeFaults || activeFaults.length === 0) {
        noFaultMsg.style.display = 'flex';
        faultDetails.style.display = 'none';
        document.getElementById('murray-section').style.display = 'none';
        return;
    }

    noFaultMsg.style.display = 'none';
    faultDetails.style.display = 'flex';

    let html = '';
    for (const fault of activeFaults) {
        const sevClass = fault.severity === 'CRITICAL' ? 'severity-critical'
            : fault.severity === 'HIGH' ? 'severity-high' : 'severity-medium';

        html += `
        <div class="fault-card" style="border-color: ${fault.color}">
            <div class="fault-card-header">
                <span class="fault-card-icon">${fault.icon}</span>
                <span class="fault-card-title" style="color: ${fault.color}">${fault.fault_name}</span>
                <span class="fault-card-severity ${sevClass}">${fault.severity}</span>
            </div>
            <div class="fault-card-detail">
                <span>Fault ID</span><span>${fault.id}</span>
            </div>
            <div class="fault-card-detail">
                <span>Location</span><span>${fault.location_km} km</span>
            </div>
            <div class="fault-card-detail">
                <span>Segment</span><span>#${fault.segment_id}</span>
            </div>
            <div class="fault-card-detail">
                <span>Detected At</span><span>${fault.timestamp}</span>
            </div>
            <div class="fault-card-detail">
                <span>Status</span><span style="color: ${fault.color}">${fault.status}</span>
            </div>
            <div class="fault-card-desc">${fault.description}</div>
        </div>`;
    }
    faultDetails.innerHTML = html;
}

// ============================================================
// MURRAY LOOP RESULTS
// ============================================================
function updateMurrayResults(result) {
    const section = document.getElementById('murray-section');
    const container = document.getElementById('murray-results');

    if (result.error) {
        section.style.display = 'block';
        container.innerHTML = `<div style="text-align: center; padding: 12px; color: var(--text-secondary); font-size: 0.78rem;">${result.error}</div>`;
        return;
    }

    section.style.display = 'block';
    container.innerHTML = `
        <div class="murray-row">
            <span>Fault Type</span>
            <span style="color: #ff6600">${result.fault_type || '--'}</span>
        </div>
        <div class="murray-row">
            <span>Measured Distance</span>
            <span style="color: var(--cyan)">${result.measured_distance} km</span>
        </div>
        <div class="murray-row">
            <span>Actual Distance</span>
            <span>${result.actual_distance} km</span>
        </div>
        <div class="murray-row">
            <span>Error</span>
            <span style="color: ${result.error_km < 0.1 ? 'var(--green)' : 'var(--orange)'}">${result.error_meters} m (${result.error_percent}%)</span>
        </div>
        <div class="murray-row">
            <span>R_a (Bridge)</span>
            <span>${result.R_a} Ω</span>
        </div>
        <div class="murray-row">
            <span>R_b (Bridge)</span>
            <span>${result.R_b} Ω</span>
        </div>
        <div class="murray-row">
            <span>R_loop</span>
            <span>${result.R_loop} Ω</span>
        </div>
        <div class="murray-row">
            <span>Bridge Ratio</span>
            <span>${result.bridge_ratio}</span>
        </div>
        <div class="murray-accuracy">
            <div class="accuracy-value">${result.accuracy}%</div>
            <div class="accuracy-label">Location Accuracy</div>
        </div>
    `;
}

// ============================================================
// ALERT LOG
// ============================================================
function updateAlertLog(faultLog) {
    const container = document.getElementById('alert-log-content');
    const noAlerts = document.getElementById('no-alerts-msg');
    const badge = document.getElementById('alert-count-badge');

    if (!faultLog || faultLog.length === 0) {
        noAlerts.style.display = 'flex';
        badge.textContent = '0 Alerts';
        return;
    }

    noAlerts.style.display = 'none';
    badge.textContent = faultLog.length + ' Alerts';

    let html = '';
    for (const fault of faultLog.slice(0, 20)) {
        html += `
        <div class="alert-item" style="border-color: ${fault.color}">
            <span class="alert-item-icon">${fault.icon}</span>
            <div class="alert-item-content">
                <div class="alert-item-title" style="color: ${fault.color}">${fault.fault_name}</div>
                <div class="alert-item-detail">Segment #${fault.segment_id} • ${fault.location_km} km • ${fault.severity}</div>
                <div class="alert-item-time">${fault.timestamp}</div>
            </div>
        </div>`;
    }
    container.innerHTML = html;
}

// ============================================================
// FAULT OVERLAY
// ============================================================
function showFaultOverlay(fault) {
    const overlay = document.getElementById('fault-overlay');
    document.getElementById('fault-overlay-icon').textContent = fault.icon;
    document.getElementById('fault-overlay-title').textContent = 'FAULT DETECTED: ' + fault.fault_name;
    document.getElementById('fault-overlay-desc').textContent = fault.description;
    document.getElementById('fault-overlay-location').textContent = 'Location: ' + fault.location_km + ' km (Segment #' + fault.segment_id + ')';
    document.getElementById('fault-overlay-severity').textContent = 'Severity: ' + fault.severity;
    overlay.classList.add('active');

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        hideFaultOverlay();
    }, 5000);
}

function hideFaultOverlay() {
    document.getElementById('fault-overlay').classList.remove('active');
}
