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
    assert coder["packet_type"] == "execution"
    assert verifier["packet_type"] == "execution"
    assert coder['grace_feature_ref'] == 'feature:FEAT-PLAN-CONTRACT'
    assert coder['grace_wave_ref'] == 'feature:FEAT-PLAN-CONTRACT:wave:W01'
    assert coder['grace_packet_ref'].endswith(f":packet:{coder['packet_id']}")
    assert isinstance(verifier["verification_profile"], dict)
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
                            'observability_scope': 'wave_final',
                            'canonical_flow_commands': [
                                'python3 scripts/verify_api_responses.py',
                                'python3 tests/verify_week_forecast.py',
                            ],
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
    assert hints['runner'] == 'codex'
    assert hints['touches_frontend'] is True
    assert hints['requires_frontend_visual'] is True
    assert hints['artifact_globs'] == ['frontend/test-results/**/*']
    assert hints['frontend_commands'] == [
        'corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx',
        './scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts',
    ]
    assert hints['observability_scope'] == 'wave_final'
    assert hints['canonical_flow_commands'] == [
        'python3 scripts/verify_api_responses.py',
        'python3 tests/verify_week_forecast.py',
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
    assert stored["packet_type"] == "gate_decision"


def test_rework_bundle_preserves_execution_hints_and_explicit_target(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path / 'state'
    packets_dir = Path('/opt/astro-project/prefect_grace/packets') / 'FEAT-REWORK-HINTS'
    if packets_dir.exists():
        import shutil
        shutil.rmtree(packets_dir)

    seeded = seed_test_feature(
        feature_id='FEAT-REWORK-HINTS',
        title='Rework hints feature',
        summary='Preserve sandbox and IDs through rework packets',
        implementation_title='Implementation',
        implementation_summary='Implementation summary',
        agent_sandbox='danger-full-access',
        verifier_observability_profile='read-only',
    )

    from prefect_grace.tasks.review_router import create_rework_bundle_from_review, create_direct_rework_from_architect

    coder = next(packet for packet in seeded['packets']['generated'] if packet['role'] == 'coder')
    verifier = next(packet for packet in seeded['packets']['generated'] if packet['role'] == 'verifier')
    reviewer = next(packet for packet in seeded['packets']['generated'] if packet['role'] == 'reviewer')
    assert verifier['execution_hints']['sandbox'] == 'danger-full-access'

    bundle = create_rework_bundle_from_review(
        packet_id=coder['packet_id'],
        reviewer_packet_id=reviewer['packet_id'],
        reasons=['Need localized rework'],
    )

    rework = bundle['rework']
    rework_verifier = bundle['verifier']
    rework_reviewer = bundle['reviewer']

    assert rework['execution_hints']['sandbox'] == 'danger-full-access'
    assert rework_verifier['execution_hints']['sandbox'] == 'danger-full-access'
    assert rework_reviewer['execution_hints']['sandbox'] == 'danger-full-access'
    assert rework_reviewer['review_target_packet_id'] == rework['packet_id']
    assert rework['grace_feature_ref'] == 'feature:FEAT-REWORK-HINTS'
    assert rework['grace_wave_ref'] == 'feature:FEAT-REWORK-HINTS:wave:W01'

    direct_rework = create_direct_rework_from_architect(
        coder['packet_id'],
        ['Need bounded architect-first rework'],
    )
    assert direct_rework['execution_hints']['sandbox'] == 'danger-full-access'
    assert direct_rework['review_target_packet_id'] == coder['packet_id']

    light_rework = create_direct_rework_from_architect(
        coder['packet_id'],
        ['Small packet-local fix'],
        rework_mode='light_resume',
        title='Light Rework Main Slice',
    )
    assert light_rework['rework_mode'] == 'light_resume'
    assert light_rework['execution_hints']['resume_strategy'] == 'packet_parent'
    assert light_rework['execution_hints']['resume_parent_packet_id'] == coder['packet_id']
    assert light_rework['packet_id'] == coder['packet_id']
    assert light_rework['execution_hints']['light_resume_stage'] is True
    assert light_rework["packet_type"] == "execution"

    downgraded_rework = create_direct_rework_from_architect(
        coder['packet_id'],
        ['Needs planner because packet graph changes', 'Also requires business decision'],
        rework_mode='light_resume',
        title='Too Broad For Light Resume',
    )
    assert downgraded_rework['packet_id'] != coder['packet_id']
    assert downgraded_rework['requested_rework_mode'] == 'light_resume'
    assert downgraded_rework['rework_mode'] == 'bounded_fresh'
    assert downgraded_rework['light_resume_downgrade_reason']
    assert downgraded_rework["packet_type"] == "rework"

    seeded_alias = seed_test_feature(
        feature_id='FEAT-REWORK-HINTS-ALIAS',
        title='Rework hints alias feature',
        summary='Verify small_fix alias maps to packet-level light resume',
        implementation_title='Implementation',
        implementation_summary='Implementation summary',
        agent_sandbox='danger-full-access',
        verifier_observability_profile='read-only',
    )
    alias_coder = next(packet for packet in seeded_alias['packets']['generated'] if packet['role'] == 'coder')
    small_fix_rework = create_direct_rework_from_architect(
        alias_coder['packet_id'],
        ['Fix one narrow typo'],
        rework_mode='small_fix',
        title='Small Fix Main Slice',
    )
    assert small_fix_rework['packet_id'] == alias_coder['packet_id']
    assert small_fix_rework['requested_rework_mode'] == 'light_resume'
    assert small_fix_rework['rework_mode'] == 'light_resume'
    assert small_fix_rework["packet_type"] == "execution"


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
                        "observability_scope": "wave_final",
                        "canonical_flow_commands": [
                            "python3 scripts/verify_api_responses.py",
                            "python3 tests/verify_week_forecast.py",
                        ],
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
            "runner": "codex",
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
    assert hints["observability_scope"] == "wave_final"
    assert hints["canonical_flow_commands"] == [
        "python3 scripts/verify_api_responses.py",
        "python3 tests/verify_week_forecast.py",
    ]
    assert hints["observability_commands"] == ["python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"]
    assert hints["artifact_globs"] == ["frontend/test-results/**/*"]
    assert "frontend_profile" not in hints
    assert "observability_profile" not in hints


def test_normalize_planner_contract_rejects_invalid_observability_scope() -> None:
    contract = default_wave_plan_contract(
        feature_id="FEAT-X",
        implementation_title="Impl",
        implementation_summary="Summary",
    )
    contract["packets"][1]["verification_profile"]["execution"] = {
        "observability_scope": "broad",
    }
    try:
        normalize_wave_plan_contract(contract)
    except ValueError as exc:
        assert "Unsupported observability_scope" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid observability scope")


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
