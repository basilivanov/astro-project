from pathlib import Path

from prefect_grace.tasks import state_store
from prefect_grace.tasks.business_intake import load_business_feature_brief, submit_feature_run_from_brief
from prefect_grace.tasks.feature_bootstrap import bootstrap_feature


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
    assert loaded['run_planner'] is None
    assert loaded['impacted_surfaces'] == []
    assert 'Scope: Add strict logs.' in loaded['implementation_summary']
    assert 'Acceptance: Logs are structured.' in loaded['implementation_summary']

def test_load_business_feature_brief_accepts_optional_run_planner(tmp_path: Path) -> None:
    brief_path = tmp_path / 'brief-run-planner.yaml'
    brief_path.write_text(
        '\n'.join([
            'feature_id: FEAT-BRIEF-PLANNER',
            'title: Planner brief',
            'summary: Opt into planner when decomposition is complex',
            'run_planner: true',
        ]),
        encoding='utf-8',
    )

    loaded = load_business_feature_brief(brief_path)
    assert loaded['run_planner'] is True


def test_submit_feature_run_from_brief_creates_prefect_submission(monkeypatch, tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / 'state'
    brief_path = tmp_path / 'brief-submit.yaml'
    brief_path.write_text(
        '\n'.join([
            'feature_id: FEAT-BRIEF-SUBMIT',
            'title: Submit from brief',
            'summary: Create scheduled Prefect run from YAML brief',
        ]),
        encoding='utf-8',
    )

    submitted: list[dict] = []
    notified: list[dict] = []
    monkeypatch.setattr(
        'prefect_grace.tasks.business_intake.submit_feature_flow_run',
        lambda **kwargs: submitted.append(kwargs) or {
            'flow_run_id': 'flow-1',
            'deployment_id': 'dep-1',
            'feature_id': 'FEAT-BRIEF-SUBMIT',
            'title': 'Submit from brief',
            'status': 'Scheduled',
            'scheduled_for': '2026-04-16T18:00:00+00:00',
            'work_queue_name': 'grace-live',
            'tags': ['grace'],
        },
    )
    monkeypatch.setattr(
        'prefect_grace.tasks.business_intake.notify_submission_event',
        lambda **kwargs: notified.append(kwargs) or True,
    )

    record = submit_feature_run_from_brief(brief_path)

    assert record['flow_run_id'] == 'flow-1'
    assert record['brief_path'] == str(brief_path)
    assert submitted
    assert submitted[0]['parameters']['feature_id'] == 'FEAT-BRIEF-SUBMIT'
    assert submitted[0]['scheduled_for'] is None
    assert notified
    assert notified[0]['flow_run_id'] == 'flow-1'


def test_bootstrap_feature_rewrites_feature_brief_when_business_context_arrives(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / 'state'
    import prefect_grace.tasks.feature_bootstrap as feature_bootstrap
    feature_bootstrap.FEATURES_DIR = tmp_path / 'packets'

    feature_id = 'FEAT-BRIEF-REWRITE'
    bootstrap_feature(feature_id, 'Rewrite brief', 'Initial summary', business_context=None)
    bootstrap_feature(
        feature_id,
        'Rewrite brief',
        'Initial summary',
        business_context={
            'scope': ['Scoped change'],
            'acceptance_criteria': ['Acceptance line'],
            'visual_expectations': ['Visual line'],
        },
    )

    brief_path = feature_bootstrap.FEATURES_DIR / feature_id / 'feature-brief.md'
    text = brief_path.read_text(encoding='utf-8')
    assert 'Scoped change' in text
    assert 'Acceptance line' in text
    assert 'Visual line' in text
