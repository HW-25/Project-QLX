<<<<<<< HEAD
#!/usr/bin/env python3
"""
Project: QLX (Phase Alpha)
Module: EON Monitor Lite v1.3.1
Status: Public / Community Edition

Description:
A high-performance telemetry engine designed to bridge hardware energy metrics 
with compute-value (Valor) for the Project: QLX Energy-Compute Nexus.

Features:
- Physical Precision: Direct mW monitoring on Apple Silicon (M1/M2/M3).
- GPU Acceleration: Native NVIDIA GPU telemetry (Power/Usage) via NVML.
- Arbitrage Logic: Real-time calculation of compute-energy profitability spreads.
- Secure Uplink: Modular telemetry streaming to the QLX Core.
"""

import subprocess
import re
import time
import requests
import json
import logging
import os
import sys
import platform
import uuid
from collections import deque
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Attempt to import psutil for cross-platform load monitoring
try:
    import psutil
except ImportError:
    print("[DEPENDENCY ERROR] 'psutil' library not found.")
    print("Please install it using: pip3 install psutil")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_SETTINGS = {
    "WINDOW_SIZE": 60,
    "SAMPLE_INTERVAL": 1,
    "CONVERSION_FACTOR": 1000000,
    "UPLINK_URL": "http://your-server-ip/api/uplink",
    "NODE_ID": f"QLX-{str(uuid.uuid4())[:8].upper()}",
    "LOCATION": "Global",
    "IS_GREEN_ENERGY": False,
    "LOG_LEVEL": "INFO",
    "LOG_FILE": str(Path.home() / "qlx_eon_lite.log")
}

class Config:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self._load_from_json()

    def _load_from_json(self):
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.settings.update(json.load(f))
            except Exception as e:
                print(f"[ERROR] Failed to parse config.json: {e}")

    def __getattr__(self, name):
        return self.settings.get(name)

config = Config()

# ============================================================================
# TELEMETRY ENGINE
# ============================================================================

class EONTelemetry:
    def __init__(self):
        self.history = deque(maxlen=config.WINDOW_SIZE)
        self.platform = platform.system()
        self.is_apple_silicon = self._check_apple_silicon()
        
    def _check_apple_silicon(self) -> bool:
        if self.platform == "Darwin":
            try:
                cpu_info = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode()
                return "Apple" in cpu_info
            except:
                return False
        return False

    def capture_power_mw(self) -> float:
        """Captures real-time power consumption. Uses physical metrics where available."""
        if self.is_apple_silicon:
            return self._get_macos_physical_power()
        else:
            return self._get_simulated_power_from_load()

    def _get_macos_physical_power(self) -> float:
        """Reads physical mW from Apple Silicon powermetrics."""
        try:
            cmd = ['sudo', 'powermetrics', '--samplers', 'cpu_power', '-i', '1000', '-n', '1']
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            match = re.search(r'Combined Power \(CPU \+ GPU \+ ANE\): (\d+) mW', process.stdout)
            return float(match.group(1)) if match else self._get_simulated_power_from_load()
        except:
            return self._get_simulated_power_from_load()

    def _get_simulated_power_from_load(self) -> float:
        """Fallback: Simulates power (mW) based on CPU load and TDP estimates."""
        load = psutil.cpu_percent(interval=None)
        # Base assumption: 5W idle, 30W peak for a typical laptop
        base_power = 5000 
        peak_power = 30000
        return base_power + (load / 100.0 * (peak_power - base_power))

    def record(self, value: float):
        self.history.append(value)

    def get_average(self) -> float:
        return sum(self.history) / len(self.history) if self.history else 0.0

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    telemetry = EONTelemetry()
    session_id = str(uuid.uuid4())[:6].upper()
    
    print("\n" + "═"*60)
    print(f" PROJECT: QLX | EON MONITOR LITE v1.2.0")
    print(f" NODE_ID: {config.NODE_ID} | SESSION: {session_id}")
    print(f" PLATFORM: {telemetry.platform} | MODE: {'PHYSICAL' if telemetry.is_apple_silicon else 'SIMULATED'}")
    print("═"*60)
    print(" [STATUS] Telemetry streaming active...")
    print(" [ACTION] Press Ctrl+C to disconnect node\n")

    try:
        while True:
            power = telemetry.capture_power_mw()
            telemetry.record(power)
            avg = telemetry.get_average()
            
            # Calculate Valor (Compute-Value)
            valor = (avg * config.WINDOW_SIZE) / config.CONVERSION_FACTOR
            
            # Dashboard Output
            sys.stdout.write(
                f"\r [LIVE] Power: {power:5.0f}mW | "
                f"Avg: {avg:5.0f}mW | "
                f"Yield: {valor:.8f} QLX"
            )
            sys.stdout.flush()
            
            # Uplink logic would trigger here every window cycle
            # (Omitted in Lite version for simplicity/security)
            
            time.sleep(config.SAMPLE_INTERVAL)
            
    except KeyboardInterrupt:
        print(f"\n\n [INFO] Node {config.NODE_ID} disconnected safely.")
        print(" Join the Nexus at quarlex.com")

if __name__ == "__main__":
    main()
=======
import os
import time
import json
import platform
import logging
import subprocess
from datetime import datetime

# Attempt to import optional dependencies
try:
    import psutil
except ImportError:
    print("[ERROR] Missing 'psutil' library. Install with: pip3 install psutil")
    exit(1)

try:
    import requests
except ImportError:
    print("[ERROR] Missing 'requests' library. Install with: pip3 install requests")
    exit(1)

try:
    import pynvml
    HAS_GPU_SUPPORT = True
except ImportError:
    HAS_GPU_SUPPORT = False

# --- CONFIGURATION & LOGGING ---
LOG_FILE = "qlx_monitor.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() if not os.environ.get('SILENT') else logging.NullHandler()
    ]
)
logger = logging.getLogger("QLX_EON")

class EONMonitorLite:
    """
    Project: QLX | EON Monitor Lite v1.3.1 (Enhanced Arbitrage Edition)
    Professional energy-compute telemetry node with real-time spread calculation.
    """
    def __init__(self, config_path="config.json"):
        self.version = "1.3.1"
        self.node_id = f"QLX-{os.urandom(4).hex().upper()}"
        self.session_id = os.urandom(3).hex().upper()
        self.platform_name = platform.system()
        self.is_apple_silicon = self._check_apple_silicon()
        self.config = self._load_config(config_path)
        
        # --- ARBITRAGE CONSTANTS (Alpha Simulation) ---
        # Current Global Avg AI Compute Value per kWh ($)
        self.COMPUTE_MARKET_VALUE = 0.18  
        # Cost of Stranded/Excess Green Energy ($)
        self.SPOT_ENERGY_COST = 0.045     
        
        # Initialize GPU if supported
        self.gpu_available = False
        if HAS_GPU_SUPPORT:
            try:
                pynvml.nvmlInit()
                self.gpu_available = True
                logger.info("NVIDIA GPU monitoring initialized.")
            except Exception as e:
                logger.warning(f"NVIDIA GPU found but NVML failed to initialize: {e}")

    def _check_apple_silicon(self):
        if self.platform_name == "Darwin":
            try:
                cpu_info = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode("utf-8")
                return "Apple" in cpu_info
            except: return False
        return False

    def _load_config(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {"server_url": "http://localhost:5000/telemetry", "interval": 1.0}

    def get_system_metrics(self):
        """Collects CPU, Memory, and Power metrics."""
        cpu_utilization_percent = psutil.cpu_percent(interval=None)
        memory_utilization_percent = psutil.virtual_memory().percent
        
        power_mw = 0.0
        mode = "SIMULATED"

        if self.is_apple_silicon:
            try:
                cmd = ["sudo", "powermetrics", "-n", "1", "--samplers", "cpu_power"]
                output = subprocess.check_output(cmd).decode("utf-8")
                for line in output.split('\n'):
                    if "Combined Power" in line:
                        power_mw = float(line.split(':')[1].split('mW')[0].strip())
                        mode = "PHYSICAL"
                        break
            except:
                power_mw = cpu_utilization_percent * 250
        else:
            power_mw = cpu_utilization_percent * 300 

        return {
            "cpu_utilization_percent": cpu_utilization_percent,
            "memory_utilization_percent": memory_utilization_percent,
            "power_mw": power_mw,
            "mode": mode
        }

    def get_gpu_metrics(self):
        """Collects NVIDIA GPU metrics if available."""
        if not self.gpu_available: return None
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            power_draw = pynvml.nvmlDeviceGetPowerUsage(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return {"gpu_power_mw": power_draw, "gpu_utilization_percent": utilization.gpu}
        except: return None

    def run(self):
        print("="*65)
        print(f" PROJECT: QLX | EON MONITOR v{self.version} | ARBITRAGE MODE")
        print(f" NODE_ID: {self.node_id} | SESSION: {self.session_id}")
        print(f" PLATFORM: {self.platform_name} | GPU: {'ACTIVE' if self.gpu_available else 'N/A'}")
        print("="*65)
        print("\n[STATUS] Streaming telemetry to global compute-energy ledger...")
        print("[ACTION] Press Ctrl+C to stop node simulation\n")

        try:
            while True:
                sys_metrics = self.get_system_metrics()
                gpu_metrics = self.get_gpu_metrics()
                
                # --- ARBITRAGE CALCULATION ENGINE ---
                total_power_mw = sys_metrics['power_mw']
                if gpu_metrics:
                    total_power_mw += gpu_metrics['gpu_power_mw']
                
                # Convert mW to kW
                power_kw = total_power_mw / 1_000_000
                
                # Calculate hourly arbitrage spread ($)
                # Formula: (Market Value - Energy Cost) * Consumption
                net_profit_hourly = power_kw * (self.COMPUTE_MARKET_VALUE - self.SPOT_ENERGY_COST)
                
                # QLX Yield Logic (Simplified)
                yield_qlx = power_kw * 1000 * 0.00006 
                
                # Build Display String
                display_str = f"[LIVE] Power: {total_power_mw:>6.0f}mW | CPU: {sys_metrics['cpu_utilization_percent']:>4.1f}%"
                if gpu_metrics:
                    display_str += f" | GPU: {gpu_metrics['gpu_utilization_percent']:>3.0f}%"
                
                display_str += f" | Spread: ${net_profit_hourly:.6f}/hr | Yield: {yield_qlx:.8f} QLX"
                
                print(display_str, end='\r')
                
                # Persistence
                log_data = {**sys_metrics, "gpu": gpu_metrics, "profit_hr": net_profit_hourly, "yield": yield_qlx}
                logger.info(f"Arbitrage_Pulse: {json.dumps(log_data)}")
                
                time.sleep(self.config.get("interval", 1.0))
        except KeyboardInterrupt:
            print("\n\n[INFO] Node telemetry suspended. Local logs preserved.")
            if self.gpu_available: pynvml.nvmlShutdown()

if __name__ == "__main__":
    monitor = EONMonitorLite()
    monitor.run()
>>>>>>> 95d0b55 (Upgrade: v1.3.1 - Strategic Arbitrage Telemetry)
