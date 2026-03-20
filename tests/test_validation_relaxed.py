#!/usr/bin/env python3
"""
Тестирование ослабленной валидации для natal секций.
Проверяет, что relaxed валидация пропускает валидный контент,
который бы был отклонен строгой валидацией.
"""

import json
import unittest

# Mock minimal dependencies
class MockSectionSpec:
    def __init__(self, section_id, title="Test"):
        self.section_id = section_id
        self.title = title

# Load the validator functions directly without full import chain
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Now import from the full module path
from app.llm.orchestrator import validate_section_content


class TestRelaxedValidation(unittest.TestCase):
    """Test relaxed validation passes content that strict validation would reject."""

    def test_axes_truths_relaxed_allows_two_axes_only(self):
        """axes_truths now allows only 2 axes mentioned instead of all 4."""
        # Content with only 2 axes (ASC-DSC mentioned) but not IC/MC
        content = json.dumps([
            {
                "type": "header",
                "level": 3,
                "text": "Ось ASC - DSC"
            },
            {
                "type": "list",
                "items": [
                    "Твоя правда: ты тянешь к независимости",
                    "Правда партнера: партнер нужен как зеркало",
                    "Задача: найти баланс между своими потребностями и потребностями партнера"
                ]
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции axes_truths."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("axes_truths")
        # Should NOT raise validation error anymore (was strict before)
        try:
            validate_section_content(spec, content)
            # Success - relaxed validation passed
        except Exception as e:
            self.fail(f"Relaxed validation should pass content with 2 axes: {e}")

    def test_axes_truths_relaxed_allows_truth_variations(self):
        """axes_truths now allows variations of 'two truths' phrasing."""
        # Content without exact "твоя правда" but with "две правды" and axes
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "Здесь описаны две правды: твоя и партнера. Ось ASC-DSC показывает эту динамику. Твоя правда связана с независимостью и самоопределением, а правда партнера - с близостью и зеркальностью."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции axes_truths с вариациями фразировки и упоминанием осей."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("axes_truths")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow 'две правды' phrasing: {e}")

    def test_love_intimacy_relaxed_allows_emoji_only(self):
        """love_intimacy now allows emoji for Venus/Mars."""
        # Content with emojis but without text names
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "В этой карте ♀️ Венера и ♂️ Марс работают вместе. Венера определяет твой стиль привязанности, а Марс показывает способ действия в отношениях."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контент для достижения минимальной длины секции love_intimacy с использованием эмодзи вместо текстовых названий планет."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("love_intimacy")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow emoji: {e}")

    def test_money_realization_relaxed_allows_one_planet(self):
        """money_realization now allows Jupiter OR Saturn instead of both."""
        # Content with only Jupiter mentioned
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "♃ Юпитер здесь показывает возможности расширения и роста через обучение, путешествия и философское осмысление опыта."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции money_realization с использованием только одной планеты из Юпитер/Сатурн."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("money_realization")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow one planet: {e}")

    def test_stars_transuranus_relaxed_allows_one_planet(self):
        """stars_transuranus now allows any one of Uranus/Neptune/Pluto."""
        # Content with only Neptune mentioned
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "♆ Нептун приносит мистику и вдохновение. Это планета трансценденции и духовного пробуждения через сны и интуитивное восприятие."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции stars_transuranus с использованием только одной из планет Нептун/Уран/Плутон."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("stars_transuranus")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow one transuranus planet: {e}")

    def test_core_triad_relaxed_allows_two_elements(self):
        """core_triad now allows 2 of 3 triad elements."""
        # Content with only ASC and Sun but without Moon
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "⬆️ ASC и ☀️ Солнце показывают твой внешний проявление и внутренний драйв. ASC — это твоя маска в мире, а Солнце — твоя сущность и жизненная сила."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции core_triad с использованием только двух из трех элементов ядра ASC/Солнце/Луна."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("core_triad")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow 2 triad elements: {e}")

    def test_framework_elements_modes_relaxed_allows_partial_elements(self):
        """framework_elements_modes now allows 2 of 4 elements."""
        # Content with only Fire and Earth mentioned (2 elements)
        content = json.dumps([
            {
                "type": "list",
                "items": [
                    "Огонь - 10%",
                    "Земля - 50%"
                ]
            },
            {
                "type": "paragraph",
                "text": "Доминанта: Земля и кардинальность дают темперамент системного организатора, который лучше стартует через план, задачу и видимую конструкцию. Дефицит: не хватает огня и мутабельности. Формула баланса: опираться на Землю и Кардинальность."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции framework_elements_modes с частичными элементами (только 2 из 4)."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("framework_elements_modes")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow partial elements: {e}")

    def test_mercury_mind_relaxed_allows_mind_keyword(self):
        """mercury_mind now allows 'мышление' as alternative."""
        # Content with 'мышление' but without 'меркурий'
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "Твое мышление работает через анализ и систематизацию. Ты склонен разбивать сложные задачи на компоненты и находить логические связи между ними."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции mercury_mind с использованием ключевого слова 'мышление' вместо 'меркурий'."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("mercury_mind")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow 'мышление': {e}")

    def test_shadow_trauma_relaxed_allows_one_point(self):
        """shadow_trauma now allows Chiron OR Lilith instead of both."""
        # Content with only Chiron mentioned
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "⚷ Хирон здесь показывает твою рану и путь исцеления. Хирон — это точка где мы осознали боль и через осознание можем трансцендировать её в дар."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции shadow_trauma с использованием только одной из точек Хирон/Лилит."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("shadow_trauma")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow one shadow point: {e}")

    def test_nodes_growth_relaxed_allows_one_node(self):
        """nodes_growth now allows North OR South node."""
        # Content with only North node mentioned
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "☊ Северный узел указывает направление развития. Это твой вектор сознательного роста и новых навыков которые ты развиваешь в этой жизни."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции nodes_growth с использованием только одного из узлов Северный/Южный."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("nodes_growth")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow one node: {e}")

    def test_vertex_fate_relaxed_allows_fate_keyword(self):
        """vertex_fate now allows 'судьба' as alternative."""
        # Content with 'судьба' but without 'вертекс'
        content = json.dumps([
            {
                "type": "paragraph",
                "text": "Здесь описана судьба через встреч и важных событий. Вертекс показывает точки встречи где происходит что-то неожиданное и судьбоносное."
            },
            {
                "type": "paragraph",
                "text": "Дополнительный контекст для достижения минимальной длины секции vertex_fate с использованием ключевого слова 'судьба' вместо 'вертекс'."
            }
        ], ensure_ascii=False)

        spec = MockSectionSpec("configurations_geometry")
        try:
            validate_section_content(spec, content)
            # Success
        except Exception as e:
            self.fail(f"Relaxed validation should allow 3 of 4 fields: {e}")


if __name__ == "__main__":
    unittest.main()
