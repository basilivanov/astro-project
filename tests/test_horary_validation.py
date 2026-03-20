import unittest

from backend.app.llm.orchestrator import LLMContentValidationError, SectionSpec, validate_section_content


class TestHoraryValidation(unittest.TestCase):
    def test_horary_skips_generic_structure(self) -> None:
        spec = SectionSpec(
            section_id="horary_01_verdict",
            title="1. Ответ сразу",
            prompt="test",
        )
        content = (
            "**Вердикт:** ✅ Да.\n"
            "**Причина:** Есть сходящийся аспект.\n"
            "**Срок:** 2 недели.\n"
            "**Главный риск:** Ретроградность.\n"
        )
        validate_section_content(spec, content)

    def test_horary_rejects_latin_words(self) -> None:
        spec = SectionSpec(
            section_id="horary_05_mechanics",
            title="5. Механика исхода",
            prompt="test",
        )
        content = (
            "**Анализ:**\n"
            "1. **Аспект:** administrative decision.\n"
            "2. **Передача света:** нет.\n"
            "3. **Препятствия:** нет.\n"
        )
        with self.assertRaises(LLMContentValidationError):
            validate_section_content(spec, content)


if __name__ == "__main__":
    unittest.main()
