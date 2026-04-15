from pathlib import Path

from prefect_grace.tasks import state_store
from prefect_grace.tasks.business_intake import enqueue_feature_job_from_brief, load_business_feature_brief
from prefect_grace.tasks.job_queue import list_jobs


def test_load_business_feature_brief_defaults(tmp_path: Path) -> None:
    brief_path = tmp_path / 'brief.yaml'
    brief_path.write_text(
        '\n'.join([
            'feature_id: FEAT-BRIEF-1',
            'title: Brief feature',
            'summary: Convert brief into queue job',
            'scope:',
            '  - Add strict logs',
            'acceptance_criteria:',
            '  - Logs are structured',
            'non_goals:',
            '  - Full redesign',
        ]),
        encoding='utf-8',
    )

    loaded = load_business_feature_brief(brief_path)
    assert loaded['feature_id'] == 'FEAT-BRIEF-1'
    assert loaded['verifier_backend_profile'] == 'backend_quick'
    assert loaded['touches_frontend'] is False
    assert loaded['impacted_surfaces'] == []
    assert 'Scope: Add strict logs.' in loaded['implementation_summary']
    assert 'Acceptance: Logs are structured.' in loaded['implementation_summary']


def test_enqueue_feature_job_from_brief_persists_business_context(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / 'state'
    brief_path = tmp_path / 'brief.yaml'
    brief_path.write_text(
        '\n'.join([
            'feature_id: FEAT-BRIEF-QUEUE',
            'title: Queue from brief',
            'summary: Use YAML brief as intake',
            'touches_frontend: true',
            'requires_frontend_visual: true',
            'visual_expectations:',
            '  - Button state must be visible',
            'verifier:',
            '  observability_profile: today-week',
            '  artifact_globs:',
            '    - frontend/test-results/**/*',
        ]),
        encoding='utf-8',
    )

    queued = enqueue_feature_job_from_brief(brief_path)
    assert queued['feature_id'] == 'FEAT-BRIEF-QUEUE'
    assert queued['brief_path'] == str(brief_path)
    assert queued['business_context']['visual_expectations'] == ['Button state must be visible']
    assert queued['verifier_requires_frontend_visual'] is True
    assert queued['business_context']['brief_path'] == str(brief_path)

    jobs = list_jobs()
    assert len(jobs) == 1
    assert jobs[0]['brief_path'] == str(brief_path)
    assert jobs[0]['business_context']['brief_path'] == str(brief_path)
    assert jobs[0]['business_context']['visual_expectations'] == ['Button state must be visible']
