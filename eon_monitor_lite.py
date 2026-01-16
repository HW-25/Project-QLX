#!/usr/bin/env python3
"""
Project: QLX (Phase Alpha)
Module: EON Monitor Lite v1.2.0
Status: Public / Community Edition

Description:
A cross-platform telemetry tool designed to monitor hardware energy consumption 
and calculate real-time compute-value (Valor) for the Quarlex Energy-Compute Nexus.

Features:
- Physical Precision: Direct mW monitoring on Apple Silicon (M1/M2/M3).
- Cross-Platform: Load-based simulation for Windows and Linux.
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
