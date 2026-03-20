import json
import unittest
from datetime import datetime
from difflib import SequenceMatcher
from types import SimpleNamespace
from unittest.mock import patch
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base
from backend.app.llm.orchestrator import (
    LLMBlockContractError,
    SectionResult,
    SectionSpec,
    _repair_section_content,
    validate_section_content,
)
from backend.app.main import ReportWorkflowRequest
from backend.app.models import Client, Report, ReportChunk, User
from backend.app.services import report_workflow
from backend.app.services.report_workflow import (
    build_section_validation_fallback_content,
    generate_section_content,
    generate_report_sections,
)


class TestValidationTemplateFallback(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

        user = User(telegram_id=123456789, username="test", full_name="Test User")
        client = Client(
            full_name="Test Client",
            birth_datetime=datetime.utcnow(),
            birth_location="Moscow",
        )
        report = Report(client=client, user=user, report_type="custom", status="pending")
        self.session.add_all([user, client, report])
        self.session.commit()

        self.report = report
        self.payload = SimpleNamespace(
            report_type="custom",
            sections=[
                SectionSpec(section_id="healthy", title="Healthy", prompt="test"),
                SectionSpec(section_id="broken", title="Broken", prompt="test"),
            ],
        )

    def tearDown(self):
        self.session.close()

    @patch("backend.app.services.report_workflow.build_chart_data", return_value={})
    @patch(
        "backend.app.services.report_workflow.build_report_context",
        return_value={
            "client": {"name": "Tester", "note": "", "report_type": "custom"},
            "facts": {"v": "facts_v1", "pos": [], "houses": [], "aspects": []},
        },
    )
    @patch("backend.app.services.report_workflow.generate_section_content")
    async def test_validation_errors_use_template_fallback(
        self,
        mock_generate_section_content,
        mock_build_report_context,
        mock_build_chart_data,
    ):
        def side_effect(spec, *_args, **_kwargs):
            if spec.section_id == "broken":
                raise LLMBlockContractError("invalid block type: markdown")
            return SectionResult(
                section_id=spec.section_id,
                title=spec.title,
                content='[{"type":"paragraph","text":"Достаточно длинный валидный блок для теста."}]',
            )

        mock_generate_section_content.side_effect = side_effect

        sections, _chart = await generate_report_sections(
            self.report,
            self.payload,
            self.session,
            llm_client=MagicMock(),
            llm_mode="openrouter",
            reset_chunks=True,
            raise_on_error=False,
        )

        broken_chunk = (
            self.session.query(ReportChunk)
            .filter(ReportChunk.report_id == self.report.id, ReportChunk.section == "broken")
            .first()
        )

        self.assertEqual(self.report.status, "completed")
        self.assertEqual(len(sections), 2)
        self.assertIsNotNone(broken_chunk)
        self.assertNotIn("Ошибка генерации", broken_chunk.content)

        blocks = json.loads(broken_chunk.content)
        self.assertTrue(isinstance(blocks, list) and blocks)
        self.assertIn(blocks[0]["type"], {"header", "callout"})

    def test_natal_validation_fallback_preserves_list_based_insights(self):
        spec = SectionSpec(section_id="executive_summary", title="Главное", prompt="test")
        context = {
            "section_context": {
                "insight_pack": {
                    "strengths_score": [{"label": "структурная выдержка и умение держать курс"}],
                    "risk_score": [{"label": "перегруз контролем и поздний контакт с усталостью"}],
                    "relationship_theme": "отношения раскрываются через честные границы",
                    "money_theme": "деньги растут через длинный горизонт и репутацию",
                    "development_focus": "снижать внутренний пресс до того, как он становится жесткостью",
                    "best_mode_of_action": "двигаться ритмом, а не рывком",
                    "scene_seeds": [{"seed": "человек, который сначала собирает хаос в систему, а потом проверяет, не превратился ли порядок в перегруз"}],
                }
            }
        }

        content = build_section_validation_fallback_content(spec, context)
        blocks = json.loads(content)
        flat = json.dumps(blocks, ensure_ascii=False)

        self.assertIn("структурная выдержка и умение держать курс", flat)
        self.assertIn("перегруз контролем и поздний контакт с усталостью", flat)
        self.assertIn("двигаться ритмом, а не рывком", flat)
        self.assertIn("Человек, который сначала собирает хаос в систему", flat)
        self.assertNotIn("Главное по карте", flat)
        self.assertNotIn("О чем этот блок", flat)
        self.assertNotIn("Дополнено автоматически", flat)

    def test_final_synthesis_validation_fallback_keeps_compact_chart_specific_callout(self):
        spec = SectionSpec(section_id="final_synthesis", title="Финальная сборка", prompt="test")
        context = {
            "section_context": {
                "insight_pack": {
                    "final_motto_seed": {"label": "слушай глубину, приземляй образ в факты"},
                    "one_sentence_advice": {
                        "text": "Ставь рядом с интуицией критерии, сроки и проверку реальностью. В работе держи систему и ритм; в близости сохраняй бережный темп."
                    },
                    "top_conflict_vs_top_resource": {
                        "resource": {"label": "эмпатия и глубина"},
                        "conflict": {"label": "образ без конкретики"},
                    },
                }
            }
        }

        content = build_section_validation_fallback_content(spec, context)
        blocks = json.loads(content)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "callout")
        self.assertEqual(blocks[0]["variant"], "success")
        self.assertIn("Слушай глубину, приземляй образ в факты", blocks[0]["content"])
        self.assertIn("В работе держи систему и ритм", blocks[0]["content"])
        self.assertNotIn("top_conflict_vs_top_resource", blocks[0]["content"])

    def test_timed_final_synthesis_validation_fallback_polishes_scaffold_without_losing_anchors(self):
        spec = SectionSpec(section_id="final_synthesis", title="Финальная сборка", prompt="test")
        context = {
            "client": {"birth_time_known": True},
            "section_context": {
                "insight_pack": {
                    "final_motto_seed": {
                        "label": "эмпатия, интуиция и чувство подводных процессов; режим карты — сначала почувствовать тон процесса, затем приземлить это в конкретный шаг"
                    },
                    "one_sentence_advice": {
                        "text": "Режим карты — сначала почувствовать тон процесса, затем приземлить это в конкретный шаг. Ставь рядом с интуицией критерии, сроки и проверку реальностью."
                    },
                    "integration_focus": {
                        "label": "твоя сила максимальна, когда чувствительность получает форму, а не туман (Луна, в Рак, дом 7); большой образ должен получать критерии, срок и форму (Нептун трин Солнце (4.8°))"
                    },
                    "closing_bridge": {
                        "work_line": "держи систему, стандарт и длинный горизонт с ясным ритмом и накоплением статуса (10 дом в Скорпион, управитель Плутон в Весы, дом 9)",
                        "love_line": "сохраняй медленный безопасный темп с общей целью и уважением к надежности (Луна, в Рак, дом 7)",
                    },
                }
            },
        }

        content = build_section_validation_fallback_content(spec, context)
        blocks = json.loads(content)
        flat = blocks[0]["content"]

        self.assertEqual(len(blocks), 1)
        self.assertIn("Зрелый ход этой карты", flat)
        self.assertIn("Сильная версия этой карты раскрывается", flat)
        self.assertIn("Большому образу важно сразу давать", flat)
        self.assertIn("10 дом в Скорпион", flat)
        self.assertIn("Луна, в Рак, дом 7", flat)
        self.assertNotIn("форму).", flat)
        self.assertNotIn("Режим карты —", flat)

    def test_summary_repairs_do_not_append_visible_warning_blocks(self):
        cases = [
            (
                SectionSpec(section_id="executive_summary", title="Главное", prompt="test"),
                "natal executive missing money",
            ),
            (
                SectionSpec(section_id="final_synthesis", title="Финальная сборка", prompt="test"),
                "natal final missing advice",
            ),
        ]

        raw_content = json.dumps(
            [{"type": "paragraph", "text": "Почти валидный summary без нужного якоря."}],
            ensure_ascii=False,
        )

        for spec, error in cases:
            with self.subTest(section=spec.section_id):
                repaired = _repair_section_content(spec, raw_content, error)
                self.assertEqual(repaired, raw_content)
                self.assertNotIn("Дополнено автоматически", repaired)

    async def test_final_synthesis_uses_deterministic_insight_pack_without_llm_call(self):
        spec = SectionSpec(section_id="final_synthesis", title="Финальная сборка", prompt="test")
        context = {
            "client": {"name": "Ты", "report_type": "natal_master"},
            "facts": {"v": "facts_v1"},
            "section_context": {
                "insight_pack": {
                    "final_motto_seed": {"label": "слушай глубину, приземляй образ в факты"},
                    "one_sentence_advice": {
                        "text": "Ставь рядом с интуицией критерии и сроки. В работе держи систему; в близости не уходи в дистанцию."
                    },
                }
            },
        }
        llm_client = MagicMock()

        result = await generate_section_content(
            spec,
            context,
            chart_data={},
            llm_client=llm_client,
            fallback_models=[],
            retry_attempts=1,
            use_template=False,
        )

        self.assertIn("Слушай глубину, приземляй образ в факты", result.content)
        self.assertIn("В работе держи систему", result.content)
        llm_client.generate.assert_not_called()

    async def test_executive_summary_uses_deterministic_insight_pack_without_llm_call(self):
        spec = SectionSpec(section_id="executive_summary", title="Главное", prompt="test")
        context = {
            "client": {"name": "Ты", "report_type": "natal_master"},
            "facts": {"v": "facts_v1"},
            "section_context": {
                "insight_pack": {
                    "strengths_score": [{"label": "структурная выдержка и умение держать курс"}],
                    "risk_score": [{"label": "перегруз контролем и поздний контакт с усталостью"}],
                    "relationship_theme": "отношения раскрываются через честные границы",
                    "money_theme": "деньги растут через длинный горизонт и репутацию",
                    "development_focus": "снижать внутренний пресс до того, как он становится жесткостью",
                    "best_mode_of_action": "двигаться ритмом, а не рывком",
                    "what_to_do": {"items": ["назначать себе ясные критерии завершения"]},
                    "scene_seeds": [{"seed": "человек, который сначала собирает хаос в систему, а потом проверяет, не превратился ли порядок в перегруз"}],
                }
            },
        }
        llm_client = MagicMock()

        result = await generate_section_content(
            spec,
            context,
            chart_data={},
            llm_client=llm_client,
            fallback_models=[],
            retry_attempts=1,
            use_template=False,
        )

        self.assertIn("структурная выдержка и умение держать курс", result.content)
        self.assertIn("перегруз контролем и поздний контакт с усталостью", result.content)
        self.assertIn("растут через длинный горизонт и репутацию", result.content)
        self.assertNotIn("Дополнено автоматически", result.content)
        validate_section_content(spec, result.content)
        llm_client.generate.assert_not_called()

    async def test_timed_executive_summary_uses_deterministic_insight_pack_without_llm_call(self):
        spec = SectionSpec(section_id="executive_summary", title="Главное", prompt="test")
        context = {
            "client": {
                "name": "Ты",
                "report_type": "natal_master",
                "birth_time_known": True,
            },
            "facts": {"v": "facts_v1"},
            "section_context": {
                "insight_pack": {
                    "strengths_score": [{"label": "структурная выдержка и умение держать высокий стандарт"}],
                    "risk_score": [{"label": "самопрессинг и поздний контакт с усталостью"}],
                    "relationship_theme": {"label": "близость раскрывается через честный разговор, границы и предсказуемый темп"},
                    "money_theme": {"label": "лучше всего приходят через длинный горизонт, репутацию и понятные правила игры"},
                    "development_focus": {"label": "переводить напряжение в ясный ритм, а не в жесткость"},
                    "best_mode_of_action": {"label": "— сначала собирать систему, потом усиливать темп"},
                    "scene_seeds": [{"seed": "человек, который раньше других собирает хаос в рабочую систему"}],
                    "stress_manifestation": {"label": "контроль начинает подменять живой контакт с собой"},
                }
            },
        }
        llm_client = MagicMock()

        result = await generate_section_content(
            spec,
            context,
            chart_data={},
            llm_client=llm_client,
            fallback_models=[],
            retry_attempts=1,
            use_template=False,
        )

        blocks = json.loads(result.content)
        self.assertEqual([block["type"] for block in blocks], ["paragraph", "list", "paragraph"])
        self.assertIn("структурная выдержка", result.content)
        self.assertIn("Отношения держатся на том, что честный разговор", result.content)
        self.assertIn("Деньги и реализация растут через длинный горизонт", result.content)
        self.assertNotIn("работает лучше всего", result.content)
        self.assertNotIn("растут через лучше всего", result.content)
        self.assertNotIn("режим здесь — —", result.content)
        self.assertNotIn("Дополнено автоматически", result.content)
        validate_section_content(spec, result.content)
        llm_client.generate.assert_not_called()

    async def test_full_report_path_keeps_timed_executive_summary_clean(self):
        natal_report = Report(client=self.report.client, user=self.report.user, report_type="natal_master", status="pending")
        self.session.add(natal_report)
        self.session.commit()
        self.session.refresh(natal_report)

        payload = ReportWorkflowRequest(
            client_name="Timed Clean",
            client_note="",
            birth_date="1976-02-14T05:30:00",
            birth_location="Khabarovsk, Russia",
            birth_lat=48.48,
            birth_lon=135.08,
            birth_timezone="Asia/Vladivostok",
            report_type="natal_master",
            birth_time_known=True,
            house_system="placidus",
            include_fixed_stars=True,
            llm_mode="openrouter",
        )
        llm_client = MagicMock()
        original_generate = report_workflow.generate_section_content

        async def selective_side_effect(spec, context, chart_data, passed_llm_client, fallback_models, retry_attempts, use_template):
            if spec.section_id == "executive_summary":
                return await original_generate(
                    spec,
                    context,
                    chart_data,
                    passed_llm_client,
                    fallback_models,
                    retry_attempts,
                    use_template,
                )
            return SectionResult(
                section_id=spec.section_id,
                title=spec.title,
                content='[{"type":"paragraph","text":"Достаточно длинный заглушечный блок для полного прогона без вызова LLM."}]',
            )

        with patch("backend.app.services.report_workflow.generate_section_content", side_effect=selective_side_effect):
            sections, _chart = await generate_report_sections(
                natal_report,
                payload,
                self.session,
                llm_client=llm_client,
                llm_mode="openrouter",
                reset_chunks=True,
                raise_on_error=False,
            )

        executive_summary = next(item for item in sections if item.section_id == "executive_summary")
        self.assertNotIn("Дополнено автоматически", executive_summary.content)
        self.assertIn("Отношения держатся", executive_summary.content)
        self.assertIn("Деньги и реализация", executive_summary.content)
        llm_client.generate.assert_not_called()

        stored_chunk = (
            self.session.query(ReportChunk)
            .filter(
                ReportChunk.report_id == natal_report.id,
                ReportChunk.section == "executive_summary",
            )
            .first()
        )
        self.assertIsNotNone(stored_chunk)
        self.assertNotIn("Дополнено автоматически", stored_chunk.content)

    async def test_timed_final_synthesis_full_path_stays_chart_specific(self):
        spec = SectionSpec(section_id="final_synthesis", title="Финальная сборка", prompt="test")
        llm_client = MagicMock()
        rendered = {}

        payloads = {
            "timed_a": ReportWorkflowRequest(
                client_name="Timed A",
                client_note="",
                birth_date="1976-02-14T05:30:00",
                birth_location="Khabarovsk, Russia",
                birth_lat=48.48,
                birth_lon=135.08,
                birth_timezone="Asia/Vladivostok",
                report_type="natal_master",
                birth_time_known=True,
                house_system="placidus",
                include_fixed_stars=True,
            ),
            "timed_b": ReportWorkflowRequest(
                client_name="Timed B",
                client_note="",
                birth_date="1988-09-04T22:15:00",
                birth_location="Novosibirsk, Russia",
                birth_lat=55.03,
                birth_lon=82.92,
                birth_timezone="Asia/Novosibirsk",
                report_type="natal_master",
                birth_time_known=True,
                house_system="placidus",
                include_fixed_stars=True,
            ),
        }

        for case_id, payload in payloads.items():
            chart = report_workflow.build_chart_data(payload)
            context = report_workflow.build_report_context(payload, chart)
            scoped_context = report_workflow.build_section_context("final_synthesis", context, chart)
            result = await generate_section_content(
                spec,
                scoped_context,
                chart,
                llm_client=llm_client,
                fallback_models=[],
                retry_attempts=1,
                use_template=False,
            )
            validate_section_content(spec, result.content)
            rendered[case_id] = result.content

        similarity = round(SequenceMatcher(None, rendered["timed_a"], rendered["timed_b"]).ratio(), 3)

        self.assertIn("Зрелый ход этой карты", rendered["timed_a"])
        self.assertIn("Зрелый ход этой карты", rendered["timed_b"])
        self.assertIn("10 дом", rendered["timed_a"])
        self.assertIn("10 дом", rendered["timed_b"])
        self.assertNotIn("Режим карты —", rendered["timed_a"])
        self.assertNotIn("Режим карты —", rendered["timed_b"])
        self.assertIn("Солнце", rendered["timed_a"])
        self.assertIn("Луна", rendered["timed_a"])
        self.assertIn("ASC /", rendered["timed_a"])
        self.assertIn("Солнце", rendered["timed_b"])
        self.assertIn("Луна", rendered["timed_b"])
        self.assertIn("ASC /", rendered["timed_b"])
        self.assertLess(similarity, 0.62)
        llm_client.generate.assert_not_called()

    def test_executive_summary_validation_fallback_mentions_deterministic_anchors_for_timed_chart(self):
        spec = SectionSpec(section_id="executive_summary", title="Главное", prompt="test")
        context = {
            "client": {"birth_time_known": True},
            "section_context": {
                "insight_pack": {
                    "strengths_score": [{"label": "видеть систему целиком"}, {"label": "держать эмоциональный ритм"}],
                    "risk_score": [{"label": "уходить в контроль"}, {"label": "затягивать решение"}],
                    "relationship_theme": {"label": "нужна честность и ясный темп"},
                    "money_theme": {"label": "рост через стратегию и репутацию"},
                    "development_focus": {"label": "соединять глубину с проверяемым действием"},
                    "best_mode_of_action": {"label": "сначала прочитать контекст, потом зафиксировать шаг"},
                    "sun_vector": {"label": "Солнце в Рыбах держит курс через образ и смысл"},
                    "moon_vector": {"label": "Луна в Деве собирает эмоции через порядок и наблюдение"},
                    "asc_mc_axis": {"label": "ASC в Скорпионе и MC во Льве требуют точности подачи и сильной позиции"},
                }
            },
        }

        content = build_section_validation_fallback_content(spec, context)
        flat = content
        self.assertIn("Солнце в Рыбах", flat)
        self.assertIn("Луна в Деве", flat)
        self.assertIn("ASC в Скорпионе", flat)
        self.assertNotIn("Дополнено автоматически", flat)

    def test_untimed_executive_summary_validation_fallback_avoids_angle_anchors(self):
        spec = SectionSpec(section_id="executive_summary", title="Главное", prompt="test")
        context = {
            "client": {"birth_time_known": False},
            "section_context": {
                "insight_pack": {
                    "strengths_score": [{"label": "чувствовать скрытый тон ситуации"}],
                    "risk_score": [{"label": "идеализировать сигнал"}],
                    "relationship_theme": {"label": "доверие строится через прямой разговор"},
                    "money_theme": {"label": "деньги любят спокойный ритм и навык"},
                    "development_focus": {"label": "сначала собирать факт, потом усиливать чувство"},
                    "best_mode_of_action": {"label": "двигаться от наблюдения к решению"},
                    "sun_vector": {"label": "Солнце в Скорпионе требует глубины"},
                    "moon_vector": {"label": "Луна в Тельце держит устойчивость"},
                    "scene_seeds": [{"seed": "рано считывает подтекст"}],
                }
            },
        }

        content = build_section_validation_fallback_content(spec, context)
        self.assertIn("Солнце в Скорпионе", content)
        self.assertIn("Луна в Тельце", content)
        self.assertNotIn("ASC", content)
        self.assertNotIn("MC", content)
        self.assertNotIn("Дополнено автоматически", content)

    async def test_untimed_final_synthesis_fallback_stays_clean_and_fact_specific(self):
        spec = SectionSpec(section_id="final_synthesis", title="Финальная сборка", prompt="test")
        context = {
            "client": {
                "name": "Ты",
                "report_type": "natal_master",
                "birth_time_known": False,
            },
            "facts": {"v": "facts_v1"},
            "section_context": {
                "insight_pack": {
                    "final_motto_seed": {"label": "держи внутренний нерв карты в проверяемом ритме"},
                    "one_sentence_advice": {"text": "не путай интенсивность переживания с точностью выбора"},
                    "sun_vector": {"label": "Солнце в Скорпионе требует глубины и честности"},
                    "moon_vector": {"label": "Луна в Деве ищет опору в порядке и наблюдении"},
                    "closing_bridge": {"label": "сначала собирай факты, затем усиливай эмоциональную ставку"},
                }
            },
        }
        llm_client = MagicMock()

        result = await generate_section_content(
            spec,
            context,
            chart_data={},
            llm_client=llm_client,
            fallback_models=[],
            retry_attempts=1,
            use_template=False,
        )

        self.assertIn("Солнце в Скорпионе", result.content)
        self.assertIn("Луна в Деве", result.content)
        self.assertNotIn("Дополнено автоматически", result.content)
        validate_section_content(spec, result.content)
        llm_client.generate.assert_not_called()

    async def test_untimed_executive_summary_uses_deterministic_insight_pack_without_llm_call(self):
        spec = SectionSpec(section_id="executive_summary", title="Главное", prompt="test")
        context = {
            "client": {
                "name": "Ты",
                "report_type": "natal_master",
                "birth_time_known": False,
            },
            "facts": {"v": "facts_v1"},
            "section_context": {
                "insight_pack": {
                    "strengths_score": [{"label": "чувствительность к скрытым нюансам"}],
                    "risk_score": [{"label": "идеализация и туман"}],
                    "relationship_theme": {"label": "доверие и честный разговор"},
                    "money_theme": {"label": "спокойная стратегия и репутация"},
                    "development_focus": {"label": "проверять сильные чувства фактами"},
                    "best_mode_of_action": {"label": "сначала чувствовать процесс, потом приземлять"},
                    "scene_seeds": [{"seed": "человек, который рано чувствует скрытые процессы"}],
                }
            },
        }
        llm_client = MagicMock()

        result = await generate_section_content(
            spec,
            context,
            chart_data={},
            llm_client=llm_client,
            fallback_models=[],
            retry_attempts=1,
            use_template=False,
        )

        self.assertIn("чувствительность к скрытым нюансам", result.content)
        self.assertIn("идеализация и туман", result.content)
        self.assertIn("спокойная стратегия и репутация", result.content)
        self.assertNotIn("Дополнено автоматически", result.content)
        validate_section_content(spec, result.content)
        llm_client.generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
