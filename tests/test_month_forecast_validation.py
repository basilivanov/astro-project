import unittest

from backend.app.llm.orchestrator import (
    LLMContentValidationError,
    SectionSpec,
    validate_section_content,
)


class TestMonthForecastValidation(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = SectionSpec(
            section_id="month_full_forecast",
            title="Прогноз на месяц",
            prompt="test",
        )

    def test_month_forecast_accepts_weekly_campaign_structure(self) -> None:
        content = """
        [
          {"type": "header", "level": 2, "text": "📅 ПРОГНОЗ НА МЕСЯЦ"},
          {"type": "callout", "variant": "warning", "title": "СТАТУС МЕСЯЦА", "content": "Месяц неровный, но рабочий: переговоры и документы потребуют второй проверки. Главная задача — держать рабочий ритм и не дробить повестку."},
          {"type": "header", "level": 2, "text": "Ключевые события"},
          {"type": "list", "items": ["02.04 - Полнолуние в Весах - пора закрыть зависший разговор", "18.04 - Новолуние в Тельце - запускай одну главную ставку"], "ordered": false},
          {"type": "header", "level": 2, "text": "Стратегия по неделям"},
          {"type": "paragraph", "text": "Месяц идет как длинная партия: сначала собираешь курс, потом двигаешь только то, что реально дает ход."},
          {"type": "header", "level": 3, "text": "Неделя 1 (01.04-07.04)"},
          {"type": "list", "items": ["**Фокус:** Собери главную ставку месяца.", "**Что продвигать:** Переговоры и рабочие договоренности.", "**Где не форсировать:** Не открывай лишние фронты."], "ordered": false},
          {"type": "header", "level": 3, "text": "Неделя 2 (08.04-14.04)"},
          {"type": "list", "items": ["**Фокус:** Проверь стыки и слабые места.", "**Что продвигать:** Документы, сроки, сборку процесса.", "**Где не форсировать:** Не обещай больше, чем успеешь перепроверить."], "ordered": false},
          {"type": "header", "level": 3, "text": "Неделя 3 (15.04-21.04)"},
          {"type": "list", "items": ["**Фокус:** Удержи темп вокруг одной центральной темы.", "**Что продвигать:** Решающие разговоры и запуск.", "**Где не форсировать:** Не разгоняй конфликт."], "ordered": false},
          {"type": "header", "level": 3, "text": "Неделя 4 (22.04-28.04)"},
          {"type": "list", "items": ["**Фокус:** Зафиксируй результат и подготовь следующий шаг.", "**Что продвигать:** Завершение и упаковку результата.", "**Где не форсировать:** Не штурмуй финал из суеты."], "ordered": false},
          {"type": "header", "level": 2, "text": "Итог месяца"},
          {"type": "key_value", "items": [{"key": "Финансы", "value": "Лучше один просчитанный шаг, чем серия импульсных трат."}, {"key": "Отношения", "value": "Работают ясные короткие договоренности."}, {"key": "Энергия", "value": "Темп держится на режиме и паузах."}]},
          {"type": "callout", "variant": "success", "title": "Практический ход", "content": "Одна ставка месяца, один еженедельный чекпоинт и никакой суеты вокруг."}
        ]
        """
        validate_section_content(self.spec, content)

    def test_month_forecast_rejects_generic_month_paragraph(self) -> None:
        content = """
        [
          {"type": "header", "level": 2, "text": "📅 ПРОГНОЗ НА МЕСЯЦ"},
          {"type": "callout", "variant": "success", "title": "СТАТУС МЕСЯЦА", "content": "Месяц будет успешным и откроет новые возможности."},
          {"type": "header", "level": 2, "text": "Ключевые события"},
          {"type": "list", "items": ["02.04 - Полнолуние в Весах - завершение сюжета"], "ordered": false},
          {"type": "header", "level": 2, "text": "Стратегия месяца"},
          {"type": "paragraph", "text": "Не распыляйся, избегай конфликтов и береги силы. Используй возможности и верь в себя."},
          {"type": "header", "level": 2, "text": "Итог месяца"},
          {"type": "key_value", "items": [{"key": "Финансы", "value": "Будет рост."}, {"key": "Отношения", "value": "Все сложится."}, {"key": "Энергия", "value": "Не переутомляйся."}]}
        ]
        """
        with self.assertRaises(LLMContentValidationError):
            validate_section_content(self.spec, content)


if __name__ == "__main__":
    unittest.main()
