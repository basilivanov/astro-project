import json
import unittest

from backend.app.llm.orchestrator import (
    LLMContentValidationError,
    SectionSpec,
    build_section_prompt,
    validate_section_content,
)
from backend.app.main import ReportWorkflowRequest
from backend.app.reporting.section_templates import get_default_sections
from backend.app.services.report_workflow import (
    build_chart_data,
    build_report_context,
    build_section_context,
)


BASE_PAYLOAD = {
    "client_name": "Test User",
    "birth_date": "1990-01-01T12:00:00",
    "birth_location": "Moscow",
    "birth_lat": 55.7558,
    "birth_lon": 37.6173,
    "birth_timezone": "Europe/Moscow",
    "house_system": "Placidus",
    "include_fixed_stars": False,
    "fixed_star_orb": 1.0,
    "report_type": "natal_master",
}


def _build_natal_context():
    request = ReportWorkflowRequest(**BASE_PAYLOAD)
    chart_data = build_chart_data(request)
    context = build_report_context(request, chart_data)
    return chart_data, context


class TestNatalSectionContext(unittest.TestCase):
    def test_mercury_section_context_is_trimmed(self):
        chart_data, context = _build_natal_context()

        section_context = build_section_context("mercury_mind", context, chart_data)

        self.assertIn("section_context", section_context)
        self.assertNotIn("partner", section_context)
        self.assertNotIn("solar", section_context)
        self.assertLess(
            len(json.dumps(section_context.get("chart", {}), ensure_ascii=False)),
            len(json.dumps(context.get("chart", {}), ensure_ascii=False)),
        )

        positions = {item["name"] for item in section_context["chart"]["positions"]}
        self.assertIn("Mercury", positions)
        self.assertNotIn("Sun", positions)
        self.assertEqual(
            section_context["section_context"]["relevant_points"],
            ["Mercury", "Moon", "Saturn", "Uranus"],
        )

    def test_balance_wheel_context_includes_house_pack(self):
        chart_data, context = _build_natal_context()

        section_context = build_section_context("balance_wheel_1_6", context, chart_data)

        self.assertIn("house_context", section_context["section_context"])
        self.assertIn("insight_pack", section_context["section_context"])
        self.assertIn("house_pack", section_context["section_context"]["insight_pack"])
        houses = [item["h"] for item in section_context["facts"]["houses"]]
        self.assertEqual(houses, [1, 2, 3, 4, 5, 6])
        self.assertEqual(
            [item["house"] for item in section_context["section_context"]["insight_pack"]["house_pack"]],
            [1, 2, 3, 4, 5, 6],
        )

    def test_facts_first_sections_include_deterministic_insight_pack(self):
        chart_data, context = _build_natal_context()
        expected_fields = {
            "executive_summary": (
                "natal_v2_p0",
                [
                    "strengths_score",
                    "risk_score",
                    "relationship_theme",
                    "money_theme",
                    "development_focus",
                    "life_manifestations",
                    "stress_manifestation",
                    "self_sabotage_pattern",
                    "compensation_pattern",
                    "what_to_do",
                    "what_not_to_do",
                    "best_mode_of_action",
                    "scene_seeds",
                ],
            ),
            "framework_elements_modes": (
                "natal_v2_p4",
                [
                    "element_rank",
                    "mode_rank",
                    "dominant_signature",
                    "deficit_signature",
                    "lifestyle_vector",
                    "balance_formula",
                ],
            ),
            "synthesis": (
                "natal_v2_p0",
                [
                    "identity_vector",
                    "core_conflict",
                    "dominant_drives",
                    "map_metaphor_seed",
                    "core_life_story",
                    "life_manifestations",
                    "inner_conflict_dynamics",
                    "self_sabotage_pattern",
                    "compensation_pattern",
                    "what_to_do",
                    "what_not_to_do",
                    "best_mode_of_action",
                    "scene_seeds",
                ],
            ),
            "money_realization": (
                "natal_v2_p0",
                [
                    "career_vector",
                    "money_pattern",
                    "work_risk_flags",
                    "realization_mode",
                ],
            ),
            "love_intimacy": (
                "natal_v2_p0",
                [
                    "attachment_style",
                    "partnership_needs",
                    "conflict_style",
                    "intimacy_risk_flags",
                    "relationship_manifestations",
                    "relationship_triggers",
                    "self_sabotage_pattern",
                    "compensation_pattern",
                    "what_to_do",
                    "what_not_to_do",
                    "best_mode_of_action",
                    "scene_seeds",
                ],
            ),
            "final_synthesis": (
                "natal_v2_p0",
                [
                    "final_motto_seed",
                    "one_sentence_advice",
                    "top_conflict_vs_top_resource",
                    "integration_focus",
                    "closing_bridge",
                    "applied_cross_links",
                ],
            ),
            "dispositor_office": (
                "natal_v2_p1",
                [
                    "engine_summary",
                    "office_map",
                    "power_centers",
                    "final_bosses",
                    "decision_chains",
                    "office_metaphor_seed",
                ],
            ),
            "balance_wheel_1_6": (
                "natal_v2_p1",
                [
                    "house_pack",
                    "zone_summary",
                ],
            ),
            "balance_wheel_7_12": (
                "natal_v2_p1",
                [
                    "house_pack",
                    "zone_summary",
                ],
            ),
            "time_cycles": (
                "natal_v2_p1",
                [
                    "current_age",
                    "cycle_markers",
                    "maturity_cycle_summary",
                    "saturn_jupiter_phase",
                    "growth_tension",
                ],
            ),
            "axes_truths": (
                "natal_v2_p2",
                [
                    "axis_polarities",
                    "axis_tasks",
                    "dominant_axis_tension",
                ],
            ),
            "aspects_beginner": (
                "natal_v2_p2",
                [
                    "aspect_cards",
                    "selection_rule",
                ],
            ),
            "nodes_growth": (
                "natal_v2_p2",
                [
                    "south_node_habit",
                    "north_node_direction",
                    "bridge_task",
                    "node_drivers",
                ],
            ),
            "mercury_mind": (
                "natal_v2_p2",
                [
                    "thinking_style",
                    "processing_mode",
                    "cognitive_risks",
                    "mind_keys",
                ],
            ),
            "shadow_trauma": (
                "natal_v2_p2",
                [
                    "chiron_pattern",
                    "lilith_pattern",
                    "pain_points",
                    "compensation_modes",
                    "integration_task",
                ],
            ),
            "core_triad": (
                "natal_v2_p3",
                [
                    "asc_mask",
                    "solar_drive",
                    "lunar_need",
                    "triad_conflict",
                    "triad_integration",
                ],
            ),
            "configurations_geometry": (
                "natal_v2_p3",
                [
                    "configuration_cards",
                    "dominant_pattern",
                    "absence_summary",
                ],
            ),
            "vertex_fate": (
                "natal_v2_p3",
                [
                    "vertex_signature",
                    "encounter_triggers",
                    "relationship_vector",
                    "fated_lesson",
                ],
            ),
            "stars_transuranus": (
                "natal_v2_p3",
                [
                    "uranus_vector",
                    "neptune_vector",
                    "pluto_vector",
                    "collective_story",
                    "fixed_star_hooks",
                ],
            ),
        }

        for section_id, (version, fields) in expected_fields.items():
            with self.subTest(section_id=section_id):
                section_context = build_section_context(section_id, context, chart_data)
                insight_pack = section_context["section_context"].get("insight_pack")
                self.assertIsNotNone(insight_pack)
                self.assertEqual(insight_pack["version"], version)
                self.assertTrue(insight_pack.get("cross_links"))
                for field_name in fields:
                    self.assertIn(field_name, insight_pack)

        wheel_context = build_section_context("balance_wheel_7_12", context, chart_data)
        self.assertEqual(
            [item["house"] for item in wheel_context["section_context"]["insight_pack"]["house_pack"]],
            [7, 8, 9, 10, 11, 12],
        )

        time_cycles_context = build_section_context("time_cycles", context, chart_data)
        self.assertIn("years", time_cycles_context["section_context"]["insight_pack"]["current_age"])

        axes_context = build_section_context("axes_truths", context, chart_data)
        self.assertEqual(
            len(axes_context["section_context"]["insight_pack"]["axis_polarities"]),
            4,
        )

        aspects_context = build_section_context("aspects_beginner", context, chart_data)
        self.assertTrue(aspects_context["section_context"]["insight_pack"]["aspect_cards"])

        shadow_context = build_section_context("shadow_trauma", context, chart_data)
        self.assertIn(
            "anchor",
            shadow_context["section_context"]["insight_pack"]["chiron_pattern"],
        )
        shadow_positions = {
            item["name"] for item in shadow_context.get("chart", {}).get("positions", [])
        }
        self.assertIn("Lilith", shadow_positions)
        self.assertNotIn("Mean Apogee", shadow_positions)

        core_context = build_section_context("core_triad", context, chart_data)
        self.assertIn(
            "steps",
            core_context["section_context"]["insight_pack"]["triad_integration"],
        )

        framework_context = build_section_context("framework_elements_modes", context, chart_data)
        self.assertEqual(
            framework_context["section_context"]["insight_pack"]["dominant_signature"]["key"],
            "earth_cardinal",
        )

        executive_context = build_section_context("executive_summary", context, chart_data)
        self.assertTrue(
            executive_context["section_context"]["insight_pack"]["scene_seeds"]
        )
        self.assertIn(
            "items",
            executive_context["section_context"]["insight_pack"]["what_to_do"],
        )

        synthesis_context = build_section_context("synthesis", context, chart_data)
        self.assertIn(
            "triggers",
            synthesis_context["section_context"]["insight_pack"]["inner_conflict_dynamics"],
        )

        geometry_context = build_section_context("configurations_geometry", context, chart_data)
        self.assertTrue(
            geometry_context["section_context"]["insight_pack"]["configuration_cards"]
        )
        self.assertIn(
            "question",
            geometry_context["section_context"]["insight_pack"]["configuration_cards"][0],
        )

        vertex_context = build_section_context("vertex_fate", context, chart_data)
        self.assertTrue(
            vertex_context["section_context"]["insight_pack"]["encounter_triggers"]
        )

        transuranus_context = build_section_context("stars_transuranus", context, chart_data)
        self.assertIn(
            "gift",
            transuranus_context["section_context"]["insight_pack"]["uranus_vector"],
        )

        final_context = build_section_context("final_synthesis", context, chart_data)
        self.assertTrue(
            final_context["section_context"]["insight_pack"]["applied_cross_links"]
        )
        self.assertIn(
            "work_line",
            final_context["section_context"]["insight_pack"]["closing_bridge"],
        )

        non_target_section = build_section_context("mercury_mind", context, chart_data)
        self.assertIn("insight_pack", non_target_section["section_context"])

    def test_facts_first_prompt_contract_and_validation(self):
        sections = {item.section_id: item for item in get_default_sections("natal_master")}

        executive_spec = sections["executive_summary"]
        framework_spec = sections["framework_elements_modes"]
        synthesis_spec = sections["synthesis"]
        love_spec = sections["love_intimacy"]
        final_spec = sections["final_synthesis"]

        self.assertIn("section_context.insight_pack", executive_spec.prompt)
        self.assertIn("section_context.insight_pack", framework_spec.prompt)
        self.assertIn("scene_seeds", executive_spec.prompt)
        self.assertIn("inner_conflict_dynamics", synthesis_spec.prompt)
        self.assertIn("relationship_triggers", love_spec.prompt)
        self.assertIn("closing_bridge", final_spec.prompt)
        self.assertIn("applied_cross_links", final_spec.prompt)
        self.assertIn("70% премиальный художественный нарратив", executive_spec.prompt)
        self.assertIn("КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО начинать с общих заходов", executive_spec.prompt)
        self.assertIn("не используй двоеточия внутри `list.items`", executive_spec.prompt)
        self.assertIn("сцена -> механизм -> зрелый ход", synthesis_spec.prompt)
        self.assertIn("Не строй текст по схеме '♀️ Венера значит..., ♂️ Марс значит...'", love_spec.prompt)

        prompt = build_section_prompt(
            framework_spec,
            {
                "section_context": {
                    "insight_pack": {"dominant_signature": {"label": "stub dominant"}}
                }
            },
        )
        self.assertIn("канонический детерминированный", prompt)

        synthesis_prompt = build_section_prompt(
            synthesis_spec,
            {
                "section_context": {
                    "insight_pack": {"map_metaphor_seed": "stub scene"}
                }
            },
        )
        self.assertIn("STYLE_CONTRACT.md (canonical natal tone)", synthesis_prompt)
        self.assertIn("сцена -> механизм -> зрелый ход", synthesis_prompt)

        executive_runtime_prompt = build_section_prompt(
            executive_spec,
            {
                "section_context": {
                    "insight_pack": {
                        "strengths_score": [{"label": "структурная выдержка"}],
                        "risk_score": [{"label": "идеализация и туман"}],
                        "relationship_theme": {"label": "доверие, границы и честный разговор"},
                        "money_theme": {"label": "деньги через длинную стратегию и репутацию"},
                        "development_focus": {"label": "проверять сильные чувства фактами"},
                        "best_mode_of_action": {"label": "сначала чувствовать процесс, потом приземлять"},
                        "scene_seeds": [{"seed": "человек, который рано чувствует скрытые нюансы"}],
                    }
                }
            },
        )
        self.assertIn("точным life-first логлайном", executive_runtime_prompt)
        self.assertIn("без повторяющихся префиксов и без двоеточий", executive_runtime_prompt)
        self.assertIn("EXECUTIVE SUMMARY RUNTIME CONTRACT", executive_runtime_prompt)
        self.assertIn("структурная выдержка", executive_runtime_prompt)
        self.assertIn("деньги через длинную стратегию и репутацию", executive_runtime_prompt)
        self.assertIn("не своди секцию к набору общих команд", executive_runtime_prompt)

        executive_ok = json.dumps(
            [
                {
                    "type": "list",
                    "items": [
                        "Сильная сторона: есть собранность, выдержка и умение держать высокий стандарт без лишней суеты.",
                        "Сильная сторона: карта даёт практичность, трезвость и способность доводить важное до результата.",
                        "Риск: можно перегружать себя контролем и поздно замечать усталость.",
                        "Риск: иногда эмоции уходят в фон, а решение становится слишком жёстким.",
                        "Ключ к отношениям: отношения работают лучше там, где есть честный разговор и ясные границы.",
                        "Ключ к деньгам: деньги растут через дисциплину, длинный горизонт и репутацию.",
                        "Главный фокус развития: вовремя замечать перегруз и переводить напряжение в конкретный разговор.",
                    ],
                    "ordered": False,
                },
                {
                    "type": "paragraph",
                    "text": "Этот executive summary deliberately содержит все facts-first опорные зоны: сильные стороны, риски, отношения, деньги и фокус развития, чтобы validator проверял именно contract секции, а не случайный набор слов.",
                },
            ],
            ensure_ascii=False,
        )
        validate_section_content(executive_spec, executive_ok)

        executive_narrative_ok = json.dumps(
            [
                {
                    "type": "paragraph",
                    "text": "Эта карта лучше всего раскрывается там, где высокий стандарт держится не на самопрессинге, а на ясной внутренней конструкции: ты умеешь собирать сложное в рабочий каркас, но перегиб начинается, когда контроль становится единственным способом чувствовать опору.",
                },
                {
                    "type": "list",
                    "items": [
                        "Опора здесь в собранности, трезвости и умении держать длинную дистанцию без лишней суеты.",
                        "Ловушка включается там, где перегруз и самосаботаж маскируются под ответственность.",
                        "В отношениях тебе легче раскрываться там, где есть честный разговор, границы и предсказуемость.",
                        "В деньгах и работе сильнее всего работает длинный горизонт, репутация и понятные правила игры.",
                        "Зрелый режим здесь не рывок, а спокойная стратегия с заранее оговоренными рамками.",
                        "Полезно заранее называть критерий завершения и оставлять паузу до того, как усталость превратится в жесткость.",
                        "Следующий вектор роста — не усиливать контроль, а переводить напряжение в ясный разговор и настройку ритма.",
                    ],
                    "ordered": False,
                },
                {
                    "type": "paragraph",
                    "text": "Когда внутренний стандарт перестает быть кнутом и становится системой, карта раскрывает не сухость, а надежность.",
                },
            ],
            ensure_ascii=False,
        )
        validate_section_content(executive_spec, executive_narrative_ok)

        executive_editorial_ok = json.dumps(
            [
                {
                    "type": "paragraph",
                    "text": "У этой карты дорогая цена за надежность: чем выше внутренний стандарт, тем важнее не превращать его во внутренний пресс.",
                },
                {
                    "type": "list",
                    "items": [
                        "Высокий стандарт работает как опора, пока не становится единственным способом держать себя в руках.",
                        "Перегруз начинается там, где контроль подменяет контакт с усталостью и чувствами.",
                        "В отношениях важнее честный темп и ясные границы, чем мгновенное слияние.",
                        "Деньги и работа охотнее отвечают на длинный горизонт, репутацию и тихую дисциплину.",
                        "Полезно заранее назвать критерий завершения и оставить паузу до жесткого решения.",
                    ],
                    "ordered": False,
                },
                {
                    "type": "paragraph",
                    "text": "Лучший режим здесь — не жестче давить, а точнее настраивать ритм, нагрузку и способ разговора с собой.",
                },
            ],
            ensure_ascii=False,
        )
        validate_section_content(executive_spec, executive_editorial_ok)

        executive_live_like_ok = json.dumps(
            [
                {
                    "type": "paragraph",
                    "text": "Жизнь полна противоречий, и ты умеешь чувствовать скрытые нюансы раньше других. В отношениях и в работе ты стремишься к безопасности и устойчивости, но перегиб начинается там, где идеализация затуманивает реальные обстоятельства.",
                },
                {
                    "type": "list",
                    "items": [
                        "Чувствительность к подтексту и раннее считывание атмосферы здесь работают как сильная сторона.",
                        "Риск включается там, где красивая картина начинает подменять факты и сроки.",
                        "В отношениях тебе нужен не шум эмоций, а доверие, ясные границы и возможность говорить прямо.",
                        "Деньги и работа лучше отвечают на спокойную стратегию, репутацию и понятный ритм.",
                        "Полезно проверять сильные чувства фактами и оставлять место для восстановления до перегруза.",
                    ],
                    "ordered": False,
                },
                {
                    "type": "paragraph",
                    "text": "Зрелый режим здесь в том, чтобы сначала почувствовать тон процесса, а затем приземлить его в конкретные шаги и договоренности.",
                },
            ],
            ensure_ascii=False,
        )
        validate_section_content(executive_spec, executive_live_like_ok)

        executive_bad = json.dumps(
            [
                {
                    "type": "paragraph",
                    "text": "Сильная сторона здесь описана подробно, риск тоже назван, но этот пример намеренно оставляет только две базовые корзины без остальных обязательных секционных опор.",
                }
            ],
            ensure_ascii=False,
        )
        with self.assertRaises(LLMContentValidationError):
            validate_section_content(executive_spec, executive_bad)

        framework_ok = json.dumps(
            [
                {
                    "type": "list",
                    "items": [
                        "Огонь - 10%",
                        "Земля - 50%",
                        "Воздух - 20%",
                        "Вода - 20%",
                    ],
                    "ordered": False,
                },
                {
                    "type": "paragraph",
                    "text": "Доминанта: Земля и кардинальность дают темперамент системного организатора, который лучше стартует через план, задачу и видимую конструкцию.",
                },
                {
                    "type": "paragraph",
                    "text": "Дефицит: не хватает огня и мутабельности, поэтому важно сознательно тренировать право на старт и гибкую перенастройку маршрута без самообвинения.",
                },
                {
                    "type": "paragraph",
                    "text": "Стиль жизни: лучший ритм строится циклами с ясным запуском, но с заранее подготовленными паузами, чтобы кардинальность не съедала ресурс.",
                },
                {
                    "type": "paragraph",
                    "text": "Формула баланса: опираться на Землю, Кардинальность, Фиксированность и при этом подпитывать Огонь, Воздух, Воду и Мутабельность через осознанные бытовые и эмоциональные практики.",
                },
            ],
            ensure_ascii=False,
        )
        validate_section_content(framework_spec, framework_ok)

        framework_bad = json.dumps(
            [
                {
                    "type": "list",
                    "items": [
                        "Огонь - 10%",
                        "Земля - 50%",
                        "Воздух - 20%",
                        "Вода - 20%",
                    ],
                    "ordered": False,
                },
                {
                    "type": "paragraph",
                    "text": "Темперамент описан общо, но тут нет явной доминанты, дефицита, стиля жизни и формулы баланса, поэтому validator должен это зарубить.",
                },
            ],
            ensure_ascii=False,
        )
        with self.assertRaises(LLMContentValidationError):
            validate_section_content(framework_spec, framework_bad)

        balance_wheel_spec = SectionSpec(
            section_id="balance_wheel_7_12",
            title="14. Колесо баланса (Дома 7-12)",
            prompt="test",
        )
        balance_wheel_ok = json.dumps(
            [
                {
                    "type": "header",
                    "level": 2,
                    "text": "14. Колесо баланса (Дома 7-12)",
                },
                {
                    "type": "paragraph",
                    "text": "Внутри дома 7 важна эмоциональная безопасность и качество договоренностей: этот дом показывает, как отношения становятся опорой, а не полем вечной проверки. Здесь полезно удерживать заботу и границы одновременно, чтобы близость не превращалась в тревожный контроль или зависание в старых обидах.",
                },
                {
                    "type": "header",
                    "level": 2,
                    "text": "Дом 8",
                },
                {
                    "type": "paragraph",
                    "text": "Дом 8 поднимает тему доверия, общих ресурсов и глубины контакта. В зрелом режиме эта зона просит не драматизировать уязвимость, а переводить сложные разговоры в честный обмен правилами, желаниями и ответственностью.",
                },
                {
                    "type": "header",
                    "level": 2,
                    "text": "Дом 9",
                },
                {
                    "type": "paragraph",
                    "text": "Дом 9 добавляет горизонт, мировоззрение и смысл: здесь важно не спорить ради правоты, а собирать личную философию, которая выдерживает и рост, и разницу взглядов. Такой формат intentionally использует живой паттерн 'Дом 8 / Дом 9', чтобы validator принимал реальную форму live-output, а не только шаблон '8 Дом'.",
                },
            ],
            ensure_ascii=False,
        )
        validate_section_content(balance_wheel_spec, balance_wheel_ok)

        balance_wheel_bad = json.dumps(
            [
                {
                    "type": "header",
                    "level": 2,
                    "text": "14. Колесо баланса (Дома 7-12)",
                },
                {
                    "type": "paragraph",
                    "text": "Это длинный, но намеренно размытый текст про отношения, доверие, общие ресурсы, смысл и карьеру без явных отдельных упоминаний нескольких домов. Он нужен, чтобы validator не пропускал просто большую общую простыню без реальной house-level структуры и не принимал один section title за достаточное доказательство раскрытия колеса баланса.",
                },
            ],
            ensure_ascii=False,
        )
        with self.assertRaises(LLMContentValidationError):
            validate_section_content(balance_wheel_spec, balance_wheel_bad)

    def test_final_synthesis_insight_pack_differs_between_charts(self):
        payload_a = ReportWorkflowRequest(
            client_name="Timed A",
            birth_date="1976-02-14T05:30:00",
            birth_location="Khabarovsk, Russia",
            birth_lat=48.48,
            birth_lon=135.08,
            birth_timezone="Asia/Vladivostok",
            report_type="natal_master",
            include_fixed_stars=False,
        )
        payload_b = ReportWorkflowRequest(
            client_name="Timed B",
            birth_date="1988-09-04T22:15:00",
            birth_location="Novosibirsk, Russia",
            birth_lat=55.03,
            birth_lon=82.92,
            birth_timezone="Asia/Novosibirsk",
            report_type="natal_master",
            include_fixed_stars=False,
        )

        chart_a = build_chart_data(payload_a)
        chart_b = build_chart_data(payload_b)
        context_a = build_report_context(payload_a, chart_a)
        context_b = build_report_context(payload_b, chart_b)

        pack_a = build_section_context("final_synthesis", context_a, chart_a)["section_context"]["insight_pack"]
        pack_b = build_section_context("final_synthesis", context_b, chart_b)["section_context"]["insight_pack"]

        self.assertNotEqual(pack_a["final_motto_seed"]["label"], pack_b["final_motto_seed"]["label"])
        self.assertNotEqual(pack_a["one_sentence_advice"]["text"], pack_b["one_sentence_advice"]["text"])
        self.assertNotEqual(pack_a["closing_bridge"]["label"], pack_b["closing_bridge"]["label"])

    def test_final_synthesis_validation_requires_single_success_callout(self):
        final_spec = next(
            item for item in get_default_sections("natal_master") if item.section_id == "final_synthesis"
        )
        content = json.dumps(
            [
                {
                    "type": "paragraph",
                    "text": "Короткая сборка здесь нарочно сделана длиннее минимального порога, чтобы validator дошел до проверки формата и не остановился только на content too short.",
                },
                {
                    "type": "callout",
                    "variant": "success",
                    "title": "Девиз",
                    "content": "слушай глубину и проверяй ее реальностью, даже если образ кажется очень убедительным и эмоционально заряженным",
                },
            ],
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(LLMContentValidationError, "natal final"):
            validate_section_content(final_spec, content)


if __name__ == "__main__":
    unittest.main()
