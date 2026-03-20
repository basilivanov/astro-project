# ############################################################################
# AI_HEADER: MODULE_TEST_JSON_PIPELINE
# ROLE: Integration test for JSON blocks pipeline.
# DEPENDENCIES: backend.app.services.report_workflow, backend.app.db
# ############################################################################

import pytest
import json
import uuid
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base
from backend.app.models import User, Client, Report, ReportChunk
from backend.app.services.report_workflow import generate_report_sections, build_section_specs

# Setup In-Memory DB
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def mock_user(db_session):
    user = User(telegram_id=12345, username="test", full_name="Test User")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def mock_client(db_session):
    client = Client(
        full_name="Test Client", 
        birth_datetime=datetime.now(),
        birth_location="London"
    )
    db_session.add(client)
    db_session.commit()
    return client

class MockPayload:
    def __init__(self, report_type="natal_master", sections=None):
        self.report_type = report_type
        self.sections = sections
        self.client_name = "Test Client"
        self.birth_date = "1990-01-01"
        self.birth_time = "12:00"
        self.birth_location = "London"
        self.birth_lat = 51.5
        self.birth_lon = -0.12
        self.birth_timezone = "Europe/London"
        self.birth_place_id = "mock_place_id"
        self.house_system = "Placidus"
        self.client_note = ""
        self.partner_name = None
        self.partner_birth_date = None
        self.partner_birth_timezone = None
        self.partner_birth_location = None
        self.partner_birth_lat = None
        self.partner_birth_lon = None
        self.partner_birth_place_id = None
        self.solar_current_location = "London"
        self.solar_current_lat = 51.5
        self.solar_current_lon = -0.12
        self.solar_current_timezone = "Europe/London"
        self.solar_current_place_id = "mock_place_id"
        self.solar_next_location = None
        self.solar_next_lat = None
        self.solar_next_lon = None
        self.solar_next_timezone = None
        self.solar_next_place_id = None
        self.include_fixed_stars = False
        self.fixed_star_orb = 1.0

def test_json_pipeline_template_mode(db_session, mock_user, mock_client):
    """
    # SCENARIO: Verify that 'mock' mode generates valid JSON blocks.
    """
    # 1. Setup Report
    report = Report(
        client_id=mock_client.id,
        user_id=mock_user.id,
        report_type="natal_master",
        status="pending"
    )
    db_session.add(report)
    db_session.commit()

    # 2. Run Generation in 'mock' mode (uses templates)
    payload = MockPayload(report_type="natal_master")
    
    # We expect templates to return JSON strings now
    sections, chart = asyncio.run(
        generate_report_sections(
            report,
            payload,
            db_session,
            llm_client=None,
            llm_mode="mock",
            reset_chunks=True,
            raise_on_error=True,
        )
    )

    # 3. Verify Chunks
    chunks = db_session.query(ReportChunk).filter(ReportChunk.report_id == report.id).all()
    assert len(chunks) > 0
    
    # Check regular sections (not input_frame or final_markdown)
    data_chunks = [c for c in chunks if c.section not in ["input_frame", "final_markdown", "technical_appendix"]]
    assert len(data_chunks) > 0
    
    for chunk in data_chunks:
        assert chunk.content is not None
        # Try parse
        try:
            blocks = json.loads(chunk.content)
            assert isinstance(blocks, list), f"Section {chunk.section} content is not a list"
            if len(blocks) > 0:
                assert "type" in blocks[0], f"Block in {chunk.section} missing 'type'"
        except json.JSONDecodeError:
            pytest.fail(f"Section {chunk.section} content is not valid JSON: {chunk.content[:100]}...")

    # Check input_frame (it is static JSON)
    input_frame = next((c for c in chunks if c.section == "input_frame"), None)
    if input_frame:
        blocks = json.loads(input_frame.content)
        assert isinstance(blocks, list)
        assert blocks[0]["type"] == "callout" # Intro text

    print("JSON Pipeline Verified: All template sections return valid JSON blocks.")
