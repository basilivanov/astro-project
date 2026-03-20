# ############################################################################
# AI_HEADER: MODULE_HORARY_CORE
# ROLE: Bridge between Astronomy Engine and Report Logic.
# DEPENDENCIES: stellium_engine, adapters.
# ############################################################################

from typing import Dict, Any
from stellium_engine import StelliumEngine
from .adapters import HORARY_ADAPTERS

class HoraryCore:
    def __init__(self, engine: StelliumEngine):
        self.engine = engine
        self.rus_names = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн",
            "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон"
        }

    def resolve_roles(self, chart, adapter: dict) -> Dict[str, str]:
        """
        Map adapter roles (querent=1, judge=10) to actual planets.
        """
        house_map = adapter.get("houses", {})
        rulers = self.engine.get_house_rulers(chart) # {1: "Mars", ...}
        
        roles = {}
        for role_key, house_num in house_map.items():
            planet_name = rulers.get(house_num, "Unknown")
            planet_ru = self.rus_names.get(planet_name, planet_name)
            roles[role_key] = {
                "role": role_key,
                "house": house_num,
                "planet_en": planet_name,
                "planet_ru": planet_ru,
                "description": f"Управитель {house_num} дома ({planet_ru})"
            }
            
        # Always add Moon
        roles["moon"] = {
            "role": "moon",
            "house": "N/A",
            "planet_en": "Moon",
            "planet_ru": "Луна",
            "description": "Луна (Соуправитель кверента / Ход событий)"
        }
        
        return roles

    def analyze(self, chart, adapter_id: str) -> Dict[str, Any]:
        """
        Full analysis package for LLM.
        """
        adapter = HORARY_ADAPTERS.get(adapter_id, HORARY_ADAPTERS["default"])
        
        roles = self.resolve_roles(chart, adapter)
        
        # Technicals
        dignities = self.engine.calculate_dignities(chart)
        aspects = self.engine.find_horary_aspects(chart)
        radicality = self.engine.check_radicality(chart)
        
        # Filter aspects for relevant roles only (optional optimization)
        # For now return all major aspects to let LLM decide or filter later.
        
        return {
            "adapter_name": adapter["name"],
            "roles": roles,
            "dignities": dignities,
            "aspects": aspects,
            "radicality": radicality,
            "config": adapter
        }
