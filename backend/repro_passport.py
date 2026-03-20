import asyncio
import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.getcwd())

from backend.app.services.report_workflow import generate_section_content
from backend.app.llm.orchestrator import SectionSpec

async def main():
    spec = SectionSpec(section_id="horary_00_passport", title="Passport", prompt="test")
    context = {"client": {"question": "test"}}
    chart_data = {"datetime_local": "2026-01-01T12:00:00", "location": {"name": "Moscow", "timezone": "Europe/Moscow"}}
    
    try:
        res = await generate_section_content(
            spec, context, chart_data, None, [], 1, False
        )
        print("SUCCESS")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
