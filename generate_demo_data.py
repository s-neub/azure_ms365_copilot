"""
ModelOp Demo Data Orchestrator (Makefile Replacement)
=====================================================
Description: 
    This script replicates the functionality of the 'Makefile' for users 
    who cannot use 'make'. It automates the creation of the 'Phase 1 Lite' 
    demo datasets by dynamically modifying config.yaml and running the ETL script.

Usage:
    python generate_demo_data.py
"""

import os
import sys
import shutil
import subprocess
import yaml
import glob
import time

# --- Constants ---
CONFIG_FILE = 'config.yaml'
ETL_SCRIPT = 'azure_copilot_etl.py'
OUTPUT_DIR = 'generated_chats'
DEMO_DIR = 'phase_1_lite_demo'

def load_config():
    """Loads the current configuration safely."""
    if not os.path.exists(CONFIG_FILE):
        print(f"[!] Error: {CONFIG_FILE} not found.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def save_config(config_data):
    """Saves the modified configuration back to file."""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config_data, f, sort_keys=False)

def run_etl_script():
    """Executes the main ETL python script."""
    print(f"  > Running {ETL_SCRIPT}...")
    try:
        subprocess.check_call([sys.executable, ETL_SCRIPT])
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running ETL script: {e}")
        sys.exit(1)

def move_latest_output(destination_subdir, new_filename):
    """Finds the most recently generated JSON and moves it to the demo folder."""
    # Find latest file in output dir
    search_pattern = os.path.join(OUTPUT_DIR, 'modelop_llm_data_*.json')
    files = glob.glob(search_pattern)
    if not files:
        print("[!] No output file found to move.")
        return

    latest_file = max(files, key=os.path.getctime)
    
    # Ensure destination exists
    dest_dir = os.path.join(DEMO_DIR, destination_subdir)
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_path = os.path.join(dest_dir, new_filename)
    shutil.move(latest_file, dest_path)
    print(f"  > Moved output to: {dest_path}")

def reset_config_defaults():
    """Resets config to the 'Safe' baseline state."""
    print("  [CONFIG] Resetting to safe defaults...")
    conf = load_config()
    
    # Navigate deep structure safely
    try:
        # 1. Reset Defect Rates
        rt = conf.setdefault('simulation', {}).setdefault('red_teaming', {})
        di = rt.setdefault('defect_injection', {})
        rates = di.setdefault('rates', {})
        rates['pii'] = 0.0
        rates['toxicity'] = 0.0
        rates['negative_sentiment'] = 0.05 # Keep slight background noise for realism
        
        # 2. Turn off Adversarial Injection
        ai = rt.setdefault('adversarial_injection', {})
        ai['active'] = False
        
        # 3. Ensure Data Expansion is Active (for consistent style)
        de = rt.setdefault('data_expansion', {})
        de['active'] = True
        
    except KeyError as e:
        print(f"[!] Config structure error: {e}")
    
    save_config(conf)

def generate_baseline():
    print("\n--- 1. GENERATING BASELINE: HEALTHY ---")
    reset_config_defaults()
    run_etl_script()
    move_latest_output("00_Baseline", "00_Business_As_Usual_Healthy.json")

def generate_day1():
    print("\n--- 2. GENERATING DAY 1: TOXICITY SPIKE ---")
    reset_config_defaults()
    
    # Modify for Toxicity
    conf = load_config()
    conf['simulation']['red_teaming']['defect_injection']['rates']['toxicity'] = 0.4
    save_config(conf)
    
    run_etl_script()
    move_latest_output("01_Comparators", "Day_01_Snapshot_Toxicity_Spike.json")

def generate_day2():
    print("\n--- 3. GENERATING DAY 2: PII LEAK ---")
    reset_config_defaults()
    
    # Modify for PII
    conf = load_config()
    conf['simulation']['red_teaming']['defect_injection']['rates']['pii'] = 0.6
    save_config(conf)
    
    run_etl_script()
    move_latest_output("01_Comparators", "Day_02_Snapshot_PII_Leak.json")

def generate_day3():
    print("\n--- 4. GENERATING DAY 3: ADVERSARIAL ATTACK ---")
    reset_config_defaults()
    
    # Modify for Adversarial
    conf = load_config()
    conf['simulation']['red_teaming']['adversarial_injection']['active'] = True
    save_config(conf)
    
    run_etl_script()
    move_latest_output("01_Comparators", "Day_03_Snapshot_Adversarial_Attack.json")

def cleanup():
    """Resets everything after running."""
    print("\n--- CLEANUP ---")
    reset_config_defaults()
    print(f"✅ PHASE 1 LITE PACKAGE COMPLETE")
    print(f"Data located in: {os.path.abspath(DEMO_DIR)}")

if __name__ == "__main__":
    # Ensure we start clean
    if os.path.exists(DEMO_DIR):
        shutil.rmtree(DEMO_DIR)
    
    try:
        generate_baseline()
        generate_day1()
        generate_day2()
        generate_day3()
        cleanup()
    except KeyboardInterrupt:
        print("\n[!] Process interrupted.")
        reset_config_defaults()