from pathlib import Path

from prefect_grace.models import PacketStatus
from prefect_grace.tasks import state_store
from prefect_grace.tasks.agent_output_parser import parse_planner_wave_plan_message
from prefect_grace.tasks.feature_bootstrap import seed_test_feature
from prefect_grace.tasks.planner_contract import default_wave_plan_contract, materialize_planner_contract, normalize_wave_plan_contract
from prefect_grace.tasks.state_store import find_record


def test_parse_planner_wave_plan_message_from_markers() -> None:
    text = '''
FINAL_GRACE_WAVE_PLAN_JSON
{"waves":[{"wave_id":"W01","title":"Core wave","objective":"Implement first slice","exit_conditions":["done"]}],"packets":[{"key":"coder_main","wave_id":"W01","title":"Core coder","role":"coder","reasoning":"high","summary":"Do work","dependencies":[]}]} 
END_FINAL_GRACE_WAVE_PLAN_JSON
'''
    parsed = parse_planner_wave_plan_message(text)
    assert parsed["waves"][0]["wave_id"] == "W01"
    assert parsed["packets"][0]["key"] == "coder_main"


def test_materialize_planner_contract_creates_packets(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / 'state'
    packets_dir = Path('/opt/astro-project/prefect_grace/packets') / 'FEAT-PLAN-CONTRACT'
    if packets_dir.exists():
        import shutil
        shutil.rmtree(packets_dir)

    seeded = seed_test_feature(
        feature_id='FEAT-PLAN-CONTRACT',
        title='Planner Contract Feature',
        summary='Use fallback planner contract',
        implementation_title='Contract implementation',
        implementation_summary='Implement from planner contract',
        business_context={'scope': ['one slice']},
        planner_contract={
            'waves': [
                {'wave_id': 'W01', 'title': 'Wave 1', 'objective': 'Deliver first slice', 'exit_conditions': ['accepted']},
            ],
            'packets': [
                {
                    'key': 'coder_main',
                    'wave_id': 'W01',
                    'title': 'Backend packet',
                    'role': 'coder',
                    'reasoning': 'high',
                    'summary': 'Implement backend change',
                    'dependencies': [],
                    'write_scope': ['backend/app/*'],
                },
                {
                    'key': 'verifier_main',
                    'wave_id': 'W01',
                    'title': 'Verifier Evidence',
                    'role': 'verifier',
                    'reasoning': 'high',
                    'summary': 'Verify backend change',
                    'dependencies': ['coder_main'],
                },
                {
                    'key': 'reviewer_main',
                    'wave_id': 'W01',
                    'title': 'Reviewer Verdict',
                    'role': 'reviewer',
                    'reasoning': 'xhigh',
                    'summary': 'Review backend change',
                    'dependencies': ['coder_main', 'verifier_main'],
                    'review_target_key': 'coder_main',
                },
                {
                    'key': 'architect_wave_gate',
                    'wave_id': 'W01',
                    'title': 'Architect Wave Gate',
                    'role': 'architect',
                    'reasoning': 'xhigh',
                    'summary': 'Accept wave',
                    'dependencies': ['reviewer_main'],
                },
            ],
        },
    )
    generated = seeded['packets']['generated']
    assert len(generated) == 4
    coder = next(packet for packet in generated if packet['role'] == 'coder')
    verifier = next(packet for packet in generated if packet['role'] == 'verifier')
    assert verifier['dependencies'] == [coder['packet_id']]
    feature = find_record('features', 'features', 'feature_id', 'FEAT-PLAN-CONTRACT')
    assert feature['planner_contract']['waves'][0]['wave_id'] == 'W01'
    assert Path(feature['wave_plan_path']).exists()
    assert find_record('packets', 'packets', 'packet_id', coder['packet_id'])['status'] == PacketStatus.READY.value


def test_materialize_planner_contract_infers_verifier_hints_from_profile(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / 'state'
    packets_dir = Path('/opt/astro-project/prefect_grace/packets') / 'FEAT-PLAN-HINTS'
    if packets_dir.exists():
        import shutil
        shutil.rmtree(packets_dir)

    seeded = seed_test_feature(
        feature_id='FEAT-PLAN-HINTS',
        title='Planner Hints Feature',
        summary='Infer verifier execution hints from planner profile text',
        implementation_title='Contract implementation',
        implementation_summary='Implement from planner contract',
        verifier_frontend_profile='frontend_quick',
        verifier_observability_profile='today-week',
        verifier_touches_frontend=True,
        verifier_requires_frontend_visual=True,
        verifier_artifact_globs=['frontend/test-results/**/*'],
        planner_contract={
            'waves': [
                {'wave_id': 'W01', 'title': 'Wave 1', 'objective': 'Deliver first slice', 'exit_conditions': ['accepted']},
            ],
            'packets': [
                {
                    'key': 'coder_main',
                    'wave_id': 'W01',
                    'title': 'Backend packet',
                    'role': 'coder',
                    'reasoning': 'high',
                    'summary': 'Implement backend change',
                    'dependencies': [],
                },
                {
                    'key': 'verifier_main',
                    'wave_id': 'W01',
                    'title': 'Verifier Evidence',
                    'role': 'verifier',
                    'reasoning': 'high',
                    'summary': 'Verify backend change',
                    'dependencies': ['coder_main'],
                    'verification_profile': {
                        'backend': 'not required',
                        'frontend': 'Run `corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx` and `./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts`',
                        'observability': 'Run `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md`',
                        'execution': {
                            'frontend_commands': [
                                'corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx',
                                './scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts',
                            ],
                            'observability_commands': [
                                'python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'
                            ],
                            'touches_frontend': True,
                            'requires_frontend_visual': True,
                            'artifact_globs': ['frontend/test-results/**/*'],
                        },
                    },
                },
            ],
        },
    )
    verifier = next(packet for packet in seeded['packets']['generated'] if packet['role'] == 'verifier')
    hints = verifier['execution_hints']
    assert hints['runner'] == 'verifier'
    assert hints['touches_frontend'] is True
    assert hints['requires_frontend_visual'] is True
    assert hints['artifact_globs'] == ['frontend/test-results/**/*']
    assert hints['frontend_commands'] == [
        'corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx',
        './scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts',
    ]
    assert hints['observability_commands'] == [
        'python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'
    ]


def test_materialize_planner_contract_sets_explicit_review_target(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / 'state'
    packets_dir = Path('/opt/astro-project/prefect_grace/packets') / 'FEAT-PLAN-REVIEW-TARGET'
    if packets_dir.exists():
        import shutil
        shutil.rmtree(packets_dir)

    seeded = seed_test_feature(
        feature_id='FEAT-PLAN-REVIEW-TARGET',
        title='Planner Review Target',
        summary='Require explicit reviewer target',
        implementation_title='Contract implementation',
        implementation_summary='Implement from planner contract',
        planner_contract={
            'waves': [{'wave_id': 'W01', 'title': 'Wave 1', 'objective': 'Deliver slice', 'exit_conditions': ['accepted']}],
            'packets': [
                {'key': 'coder_main', 'wave_id': 'W01', 'title': 'Coder', 'role': 'coder', 'reasoning': 'high', 'summary': 'Do work', 'dependencies': []},
                {'key': 'verifier_main', 'wave_id': 'W01', 'title': 'Verifier', 'role': 'verifier', 'reasoning': 'high', 'summary': 'Verify', 'dependencies': ['coder_main']},
                {'key': 'reviewer_main', 'wave_id': 'W01', 'title': 'Reviewer', 'role': 'reviewer', 'reasoning': 'xhigh', 'summary': 'Review', 'dependencies': ['coder_main', 'verifier_main'], 'review_target_key': 'coder_main'},
            ],
        },
    )
    reviewer = next(packet for packet in seeded['packets']['generated'] if packet['role'] == 'reviewer')
    coder = next(packet for packet in seeded['packets']['generated'] if packet['role'] == 'coder')
    stored = find_record('packets', 'packets', 'packet_id', reviewer['packet_id'])
    assert stored['review_target_packet_id'] == coder['packet_id']


def test_normalize_planner_contract_rejects_unknown_dependency() -> None:
    contract = default_wave_plan_contract(
        feature_id='FEAT-X',
        implementation_title='Impl',
        implementation_summary='Summary',
    )
    contract['packets'][1]['dependencies'] = ['missing_key']
    try:
        normalize_wave_plan_contract(contract)
    except ValueError as exc:
        assert 'unknown dependencies' in str(exc)
    else:
        raise AssertionError('Expected ValueError for unknown dependency')


def test_verifier_execution_overrides_default_profiles() -> None:
    state_store.STATE_DIR = Path("/tmp/pytest-prefect-grace-verify-override-state")
    if state_store.STATE_DIR.exists():
        import shutil
        shutil.rmtree(state_store.STATE_DIR)
    packets_dir = Path('/opt/astro-project/prefect_grace/packets') / 'FEAT-VERIFY-OVERRIDE'
    if packets_dir.exists():
        import shutil
        shutil.rmtree(packets_dir)
    seed_test_feature(
        feature_id='FEAT-VERIFY-OVERRIDE',
        title='Verify override feature',
        summary='Seed feature for direct materialization test',
        implementation_title='Seed implementation',
        implementation_summary='Seed implementation summary',
    )
    contract = {
        "waves": [{"wave_id": "W01", "title": "Wave", "objective": "Test"}],
        "packets": [
            {
                "key": "coder_main",
                "wave_id": "W01",
                "title": "Coder",
                "role": "coder",
                "summary": "Do work",
            },
            {
                "key": "verifier_main",
                "wave_id": "W01",
                "title": "Verifier",
                "role": "verifier",
                "summary": "Verify work",
                "dependencies": ["coder_main"],
                "verification_profile": {
                    "execution": {
                        "frontend_commands": ["./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts"],
                        "observability_commands": ["python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"],
                        "touches_frontend": True,
                        "requires_frontend_visual": True,
                        "artifact_globs": ["frontend/test-results/**/*"],
                    }
                },
            },
        ],
    }

    result = materialize_planner_contract(
        feature_id="FEAT-VERIFY-OVERRIDE",
        planner_packet_id="PLANNER",
        architect_packet_id="ARCH",
        contract=contract,
        default_verifier_execution_hints={
            "runner": "verifier",
            "backend_profile": "backend_quick",
            "frontend_profile": "frontend_quick",
            "frontend_commands": ["./scripts/run_e2e.sh e2e/quality.spec.ts -g \"today|day|dev|diagnostics\""],
            "observability_profile": "today-week",
            "observability_commands": [],
            "artifact_globs": ["test-results/**/*"],
            "touches_frontend": True,
            "requires_frontend_visual": True,
        },
    )

    verifier = next(packet for packet in result["packets"] if packet["role"] == "verifier")
    hints = verifier["execution_hints"]
    assert hints["frontend_commands"] == ["./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts"]
    assert hints["observability_commands"] == ["python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"]
    assert hints["artifact_globs"] == ["frontend/test-results/**/*"]
    assert "frontend_profile" not in hints
    assert "observability_profile" not in hints


def test_materialize_planner_contract_accepts_external_w00_dependencies() -> None:
    state_store.STATE_DIR = Path("/tmp/pytest-prefect-grace-verify-override-external-state")
    if state_store.STATE_DIR.exists():
        import shutil
        shutil.rmtree(state_store.STATE_DIR)
    packets_dir = Path('/opt/astro-project/prefect_grace/packets') / 'FEAT-VERIFY-OVERRIDE'
    if packets_dir.exists():
        import shutil
        shutil.rmtree(packets_dir)
    seed_test_feature(
        feature_id='FEAT-VERIFY-OVERRIDE',
        title='Verify override feature',
        summary='Seed feature for external dependency test',
        implementation_title='Seed implementation',
        implementation_summary='Seed implementation summary',
    )
    planner_packet_id = "FEAT-VERIFY-OVERRIDE-W00-PLANNER-SLICING"
    architect_packet_id = "FEAT-VERIFY-OVERRIDE-W00-ARCHITECT-FORMALIZATION"
    contract = {
        "waves": [{"wave_id": "W01", "title": "Wave", "objective": "Test"}],
        "packets": [
            {
                "key": "FEAT-VERIFY-OVERRIDE-W01-CODER",
                "wave_id": "W01",
                "title": "Coder",
                "role": "coder",
                "summary": "Do work",
                "dependencies": [planner_packet_id],
            },
            {
                "key": "FEAT-VERIFY-OVERRIDE-W01-VERIFIER",
                "wave_id": "W01",
                "title": "Verifier",
                "role": "verifier",
                "summary": "Verify work",
                "dependencies": ["FEAT-VERIFY-OVERRIDE-W01-CODER"],
            },
            {
                "key": "FEAT-VERIFY-OVERRIDE-W01-REVIEWER",
                "wave_id": "W01",
                "title": "Reviewer",
                "role": "reviewer",
                "summary": "Review work",
                "dependencies": ["FEAT-VERIFY-OVERRIDE-W01-CODER", "FEAT-VERIFY-OVERRIDE-W01-VERIFIER"],
                "review_target_key": "FEAT-VERIFY-OVERRIDE-W01-CODER",
            },
        ],
    }

    result = materialize_planner_contract(
        feature_id="FEAT-VERIFY-OVERRIDE",
        planner_packet_id=planner_packet_id,
        architect_packet_id=architect_packet_id,
        contract=contract,
    )

    coder = next(packet for packet in result["packets"] if packet["role"] == "coder")
    reviewer = next(packet for packet in result["packets"] if packet["role"] == "reviewer")
    assert planner_packet_id in coder["dependencies"]
    assert reviewer["review_target_packet_id"] == coder["packet_id"]
