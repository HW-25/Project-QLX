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