import os
import sys
import tempfile
import subprocess
import time
from pathlib import Path

# Mock gemini script
FAKE_GEMINI = """#!/bin/bash
echo "FAKE GEMINI RUNNING. HOME=$HOME" >> {call_log}
echo "Simulating gemini..."
# Fail first 2 times with quota error
if [ -f "{fail_counter}" ]; then
    count=$(cat "{fail_counter}")
else
    count=0
fi

if [ "$count" -lt 2 ]; then
    echo "RetryableQuotaError: Quota exceeded" >&2
    echo "429 Too Many Requests" >&2
    echo $((count+1)) > "{fail_counter}"
    exit 1
else
    echo '{{"output": "Success"}}'
    exit 0
fi
"""

def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Setup fake home with pool
        llm_home = tmp_path / "llm_root"
        llm_home.mkdir()
        for i in range(4):
            (llm_home / f"acc{i}").mkdir()
            
        # Setup fake bin
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        
        call_log = tmp_path / "calls.log"
        fail_counter = tmp_path / "fail_count"
        
        fake_gemini_path = bin_dir / "gemini"
        fake_gemini_path.write_text(FAKE_GEMINI.format(call_log=call_log, fail_counter=fail_counter))
        fake_gemini_path.chmod(0o755)
        
        # Setup fake task file
        task_file = tmp_path / "Task.md"
        task_file.write_text("- [ ] P0 Test Task\n")
        
        # Env
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + ":" + env["PATH"]
        env["WORKBOT_LLM_HOME"] = str(llm_home)
        
        # Run workbot
        # We use the updated script directly or via path if overwritten
        cmd = ["/opt/workbot/bin/workbot", "run", "--task-file", str(task_file), "--no-architect", "--no-review", "--no-fixer", "--profile", "smoke"]
        
        print("Running workbot...")
        # Since workbot script defaults to loading config from /etc or /opt, it should be fine.
        # But we need to make sure 'smoke' profile works. 
        # The default config in the script has 'smoke' profile.
        
        proc = subprocess.run(cmd, env=env, cwd=os.getcwd(), capture_output=True, text=True)
        
        print("Workbot Output:")
        print(proc.stdout)
        print("Workbot Stderr:")
        print(proc.stderr)
        
        if not call_log.exists():
            print("❌ No calls to gemini made.")
            sys.exit(1)
            
        calls = call_log.read_text().splitlines()
        print("\nGemini Calls:")
        for line in calls:
            print(line)
            
        # Verify rotation
        # Should have failed twice then succeeded.
        # Should see different accounts.
        homes = [line.split("HOME=")[1] for line in calls if "HOME=" in line]
        unique_homes = set(homes)
        
        if len(unique_homes) > 1:
            print(f"\n✅ SUCCESS: Rotated through {len(unique_homes)} accounts: {unique_homes}")
        else:
            print(f"\n❌ FAILURE: Used only {len(unique_homes)} account: {unique_homes}")
            sys.exit(1)

if __name__ == "__main__":
    main()
