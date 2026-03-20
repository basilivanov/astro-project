import importlib.util
import pathlib
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "live_quality_benchmark.py"
SPEC = importlib.util.spec_from_file_location("live_quality_benchmark", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class LiveQualityBenchmarkTests(unittest.TestCase):
    def test_resolve_case_llm_mode_requires_explicit_mode(self) -> None:
        case = {"id": "timed_a", "report_type": "natal_master"}
        with self.assertRaisesRegex(ValueError, "explicit llm_mode"):
            MODULE.resolve_case_llm_mode(case, cli_llm_mode=None, allow_stub_benchmark=False)

    def test_resolve_case_llm_mode_rejects_stub_by_default(self) -> None:
        case = {"id": "timed_a", "llm_mode": "stub"}
        with self.assertRaisesRegex(ValueError, "allow-stub-benchmark"):
            MODULE.resolve_case_llm_mode(case, cli_llm_mode=None, allow_stub_benchmark=False)

    def test_build_comparison_record_captures_compared_sections(self) -> None:
        comparison = {
            "id": "timed_a_vs_timed_b",
            "left": "timed_a",
            "right": "timed_b",
        }
        case_states = {
            "timed_a": {
                "section_texts": {
                    "input_frame": "technical A",
                    "executive_summary": "alpha",
                    "final_synthesis": "omega",
                }
            },
            "timed_b": {
                "section_texts": {
                    "executive_summary": "beta",
                    "final_synthesis": "omega",
                    "technical_appendix": "technical B",
                }
            },
        }

        record = MODULE.build_comparison_record(
            comparison,
            case_states,
            default_excludes=["input_frame", "technical_appendix"],
        )

        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["compared_sections"], ["executive_summary", "final_synthesis"])
        self.assertEqual(record["excluded_sections"], ["input_frame", "technical_appendix"])
        self.assertEqual(record["missing_in_left"], ["technical_appendix"])
        self.assertEqual(record["missing_in_right"], ["input_frame"])
        self.assertIsInstance(record["report_similarity"], float)

    def test_build_case_payload_appends_benchmark_tag(self) -> None:
        case = {
            "id": "timed_a",
            "report_type": "natal_master",
            "client_name": "Timed A",
            "client_note": "Original note",
        }
        payload = MODULE.build_case_payload(case, requested_llm_mode="openrouter", run_id="run-1")
        self.assertEqual(payload["llm_mode"], "openrouter")
        self.assertTrue(payload["is_test"])
        self.assertIn("[benchmark:run-1:timed_a]", payload["client_note"])


if __name__ == "__main__":
    unittest.main()
