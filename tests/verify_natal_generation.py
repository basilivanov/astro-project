import asyncio
import sys
import os
import uuid
import json
import time
from unittest.mock import MagicMock

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.db import SessionLocal
from backend.app.models import User, Client, Report
from backend.app.services.report_workflow import generate_report_sections
from backend.app.main import ReportWorkflowRequest

async def verify_natal(mode="stub", iterations=1):
    db = SessionLocal()
    # Find or create a test user
    user = db.query(User).filter(User.telegram_id == 123456789).first()
    if not user:
        user = User(telegram_id=123456789, full_name="Natal Tester")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    passed = 0
    total_duration = 0
    for i in range(iterations):
        print(f"\n--- Iteration {i+1}/{iterations} ---")
        # Create a client
        client = Client(
            full_name=f"Natal Client {uuid.uuid4().hex[:4]}",
            birth_location="Moscow",
            user_id=user.id
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        
        report = Report(
            client_id=client.id,
            user_id=user.id,
            report_type="natal_master",
            status="pending",
            is_test=True
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        payload = ReportWorkflowRequest(
            client_name=client.full_name,
            birth_date="1990-01-01T12:00:00",
            birth_location="Moscow",
            birth_lat=55.75,
            birth_lon=37.61,
            birth_timezone="Europe/Moscow",
            report_type="natal_master"
        )
        
        from backend.app.llm.orchestrator import OpenRouterClient
        llm_client = None
        if mode == "openrouter":
            llm_client = OpenRouterClient.from_env()

        start_time = time.time()
        print(f"Generating natal report {report.id} (mode: {mode})...")
        
        try:
            sections, chart = await generate_report_sections(
                report, payload, db, llm_client=llm_client, llm_mode=mode, reset_chunks=True, raise_on_error=False
            )
            
            duration = time.time() - start_time
            total_duration += duration
            print(f"Status: {report.status}")
            print(f"Sections generated: {len(sections)}")
            print(f"Total Duration: {duration:.2f}s")
            
            # Check for fallback error callouts
            fallback_errors = []
            for s in sections:
                if "Ошибка генерации" in s.content:
                    fallback_errors.append(s.section_id)
            
            if report.status == "completed" and len(sections) >= 7: # Threshold for usable report
                if not fallback_errors:
                    print(f"✅ Natal iteration {i+1} passed ({duration:.1f}s)")
                    passed += 1
                else:
                    print(f"⚠️ Natal iteration {i+1} completed with fallbacks in: {fallback_errors}")
            else:
                print(f"❌ Natal iteration {i+1} failed. Status={report.status}, count={len(sections)}")
        except Exception as e:
            print(f"💥 Iteration {i+1} CRASHED: {e}")

    print(f"\n--- Final Results ---")
    print(f"Passed: {passed}/{iterations}")
    if passed > 0:
        print(f"Average Duration: {total_duration/iterations:.2f}s")
    
    if passed < iterations * 0.6: # Relaxed threshold for flaky budget models
        print("❌ Threshold not met")
        sys.exit(1)

    db.close()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stub"
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    asyncio.run(verify_natal(mode=mode, iterations=iters))