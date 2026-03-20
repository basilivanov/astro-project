import sys
import os
sys.path.append("/app")
from backend.app.db import SessionLocal
from backend.app.models import Report, ReportChunk
from backend.app.reporting.section_templates import get_default_sections
from backend.app.services.report_workflow import initialize_report_chunks

db = SessionLocal()
report_id = "2c2fd927-0306-4538-8a24-7310131efb51"
report = db.query(Report).filter(Report.id == report_id).first()

if not report:
    print("Report not found")
    sys.exit(1)

print(f"Fixing chunks for report {report.id} ({report.report_type})")

specs = get_default_sections(report.report_type)
print(f"Found {len(specs)} default sections.")
expected_ids = [s.section_id for s in specs]

# Check existing chunks
existing = db.query(ReportChunk).filter(ReportChunk.report_id == report.id).all()
print(f"Existing chunks: {len(existing)}")
existing_ids = [c.section for c in existing]

missing = set(expected_ids) - set(existing_ids)
print(f"Missing chunks: {missing}")

if missing:
    print("Initializing missing chunks...")
    initialize_report_chunks(report, specs, db, reset=False)
    db.commit()
    print("Done.")
else:
    print("No chunks missing.")
