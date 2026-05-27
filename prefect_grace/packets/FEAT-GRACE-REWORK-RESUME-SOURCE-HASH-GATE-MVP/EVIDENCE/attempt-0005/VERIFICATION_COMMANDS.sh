#!/bin/bash
# Verification commands for attempt-0005

echo "=== Running targeted tests ==="
pytest -q tests/test_prefect_grace_rework_resume_policy.py \
  tests/test_prefect_grace_state_store_resume.py \
  tests/test_prefect_grace_backlog_controller_resume_integration.py \
  tests/test_prefect_grace_codex_launcher.py \
  tests/test_prefect_grace_codex_launcher_resume_gate.py

echo ""
echo "=== Running feature pipeline regression tests ==="
pytest -q tests/test_prefect_grace_feature_pipeline_dynamic.py

echo ""
echo "=== Running compile check ==="
python3 -m compileall prefect_grace/tasks/codex_launcher.py \
  prefect_grace/platform/rework_resume_policy.py \
  prefect_grace/platform/state_store.py \
  prefect_grace/platform/backlog_controller.py \
  prefect_grace/cli.py

echo ""
echo "=== Running GRACE lint ==="
python3 scripts/grace_lint.py prefect_grace/tasks/codex_launcher.py

echo ""
echo "=== Verification complete ==="
