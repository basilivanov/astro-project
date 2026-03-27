import os
import subprocess
import sys

# ############################################################################
# AI_HEADER: QUALITY_PIPELINE
# ROLE: Mandatory pre-review check script for B2C Pivot tasks.
# ############################################################################

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAIL: {cmd}")
        print(f"STDOUT: {res.stdout}")
        print(f"STDERR: {res.stderr}")
        return False
    print(f"PASS: {cmd}")
    return True

def main():
    print("--- Mandatory Pipeline Execution ---")
    
    python_exe = os.getenv("PYTHON_EXE", "python3")
    
    critical_scripts = [
        f"{python_exe} tests/test_entitlements_unit.py",
        f"{python_exe} -m pytest tests/test_one_off_runtime_smoke.py -q",
        f"{python_exe} -m pytest -q tests/test_logging_service_api.py tests/test_logging_utils_grace.py",
        f"{python_exe} tests/verify_horary_quota.py",
        f"{python_exe} tests/verify_history_feed.py",
        f"{python_exe} tests/test_notification_mock.py",
        f"{python_exe} tests/test_access_control_integration.py",
        f"{python_exe} scripts/verify_runtime_migrations.py",
        f"{python_exe} scripts/grace_lint.py",
        f"{python_exe} scripts/verify_admin_stats.py",
        f"{python_exe} tests/verify_admin_access.py",
        f"{python_exe} tests/test_llm_mode_resolution.py",
        f"{python_exe} tests/test_llm_fallback_chain.py",
        f"{python_exe} tests/test_llm_model_routing.py",
        f"{python_exe} tests/test_billing_prices.py",
        f"{python_exe} tests/smoke_launch.py"
    ]
    
    all_ok = True
    for cmd in critical_scripts:
        env_cmd = f"export PYTHONPATH=$PYTHONPATH:. && {cmd}"
        if not run_cmd(env_cmd):
            all_ok = False
            
    if not all_ok:
        print("\n!!! PIPELINE FAILED !!!")
        sys.exit(1)
        
    print("\n--- Pipeline Completed Successfully ---")

if __name__ == "__main__":
    main()
