# ############################################################################
# AI_HEADER: MODULE_STELLIUM_ENGINE
# ROLE: Core astronomical calculation engine.
# DEPENDENCIES: stellium library.
# GRACE_ANCHORS: [ENGINE_MODELS, ENGINE_INIT, HOUSE_SYSTEM_LOGIC, NATAL_CALC, 
#                 FIXED_STARS, TRANSIT_ASPECTS, SOLAR_RETURN, SOLAR_ARC, 
#                 UTILITIES]
# ############################################################################

from stellium import ChartBuilder, ReturnBuilder, ChartLocation, FIXED_STARS_REGISTRY, get_fixed_star_info
from stellium.engines.houses import WholeSignHouses, PlacidusHouses, EqualHouses
from stellium.core.config import CalculationConfig
from datetime import datetime, timedelta
import math
import itertools
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# #START_BLOCK_ENGINE_MODELS
class StarConjunction(BaseModel):
    """Модель данных для соединения со звездой."""
    star: str
    planet: str
    orb: float
    star_lon: float

class TransitAspect(BaseModel):
    """Модель данных для транзитного аспекта."""
    transit: str
    natal: str
    type: str
    exact_diff: float
# #END_BLOCK_ENGINE_MODELS

# #START_BLOCK_ENGINE_INIT
class StelliumEngine:
    def __init__(self):
        """
        # PURPOSE: Инициализация движка.
        # CONTEXT: Базовый класс для всех астрологических расчетов.
        # ACTION: Создает экземпляр движка.
        # MEASURE: Объект StelliumEngine готов к работе.
        """
        pass
# #END_BLOCK_ENGINE_INIT

    # #START_BLOCK_HOUSE_SYSTEM_LOGIC
    def _resolve_default_house_system(self, latitude: float):
        """
        # PURPOSE: Select house system based on latitude.
        # RULES: High latitudes (>= 60) -> WholeSign. Normal -> Placidus.
        """
        if abs(latitude) >= 60.0:
            return WholeSignHouses()
        return PlacidusHouses()
    # #END_BLOCK_HOUSE_SYSTEM_LOGIC

    # #START_BLOCK_NATAL_CALC
    def create_natal_chart(self, name: str, dt_str: str, location_str: str, house_system=None, birth_time_known: bool = True):
        """
        # PURPOSE: Создание натальной карты.
        # CONTEXT: Основная точка входа для натального анализа.
        # ACTION: Конфигурирует астероиды, выбирает систему домов и рассчитывает карту.
        # MEASURE: Возвращает объект Chart из библиотеки stellium.
        # """
        # Clean datetime string from timezone offset if present (Stellium parser fix)
        if isinstance(dt_str, str) and "+" in dt_str:
            dt_str = dt_str.split("+")[0]
            
        # If time is unknown, we set it to 12:00 (noon) to average the planetary position error.
        if not birth_time_known:
            if "T" in dt_str:
                date_part = dt_str.split("T")[0]
                dt_str = f"{date_part}T12:00:00"
            else:
                dt_str = f"{dt_str} 12:00:00"

        builder = ChartBuilder.from_details(dt_str, location_str, name=name)
        
        # Configure asteroids
        config = CalculationConfig()
        config.include_asteroids = ["Ceres", "Pallas", "Juno", "Vesta", "Chiron"]
        builder.with_config(config)
        
        if not house_system:
            # Prefer explicit latitude from payload to avoid builder API drift.
            lat = None
            if isinstance(location_str, dict):
                lat = location_str.get("latitude")
            if lat is None:
                resolved = getattr(builder, "location", None)
                lat = getattr(resolved, "latitude", None)
            
            if not birth_time_known:
                # For unknown time, houses are meaningless. 
                # We use WholeSign as a placeholder that doesn't depend on exact time (only sign).
                # Interpreters should ignore it based on birth_time_known flag.
                house_system = WholeSignHouses()
            elif lat is None:
                house_system = PlacidusHouses()
            else:
                house_system = self._resolve_default_house_system(lat)
            
        builder.with_house_systems([house_system])
            
        chart = builder.calculate()
        return chart
    # #END_BLOCK_NATAL_CALC

    # #START_BLOCK_HORARY_CALC
    def check_radicality(self, chart) -> Dict[str, Any]:
        """
        # PURPOSE: Проверка карты на радикальность (пригодность для суждения).
        """
        issues = []
        warnings = []
        score = 10
        
        # 1. ASC check
        asc = next((p for p in chart.positions if p.name == "ASC"), None)
        if asc:
            deg = asc.longitude % 30
            if deg < 3:
                issues.append(f"Ранний Асцендент ({deg:.1f}°). Ситуация еще не созрела.")
                score -= 3
            elif deg > 27:
                issues.append(f"Поздний Асцендент ({deg:.1f}°). Ситуация уже завершена или безнадежна.")
                score -= 3
                
        # 3. Saturn in 1st or 7th
        saturn = next((p for p in chart.positions if p.name == "Saturn"), None)
        if saturn:
            house = self.get_house_by_lon(chart, saturn.longitude)
            if house == 1:
                warnings.append("Сатурн в 1 доме. Кверент может быть подавлен или ошибаться.")
                score -= 2
            elif house == 7:
                warnings.append("Сатурн в 7 доме. Ошибки в суждении астролога или проблемы с партнером.")
                score -= 1 
                
        return {
            "score": max(0, score),
            "is_radical": score >= 5,
            "issues": issues,
            "warnings": warnings
        }

    def calculate_dignities(self, chart) -> Dict[str, Dict]:
        """
        # PURPOSE: Рассчитать эссенциальные и акцидентальные достоинства планет (RUS).
        """
        rus_names = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн",
            "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон"
        }
        
        rulers = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
            "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
            "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        exaltations = {
            "Aries": "Sun", "Taurus": "Moon", "Cancer": "Jupiter", "Virgo": "Mercury",
            "Libra": "Saturn", "Capricorn": "Mars", "Pisces": "Venus"
        }
        
        rus_signs = {
            "Aries": "Овен", "Taurus": "Телец", "Gemini": "Близнецы", "Cancer": "Рак",
            "Leo": "Лев", "Virgo": "Дева", "Libra": "Весы", "Scorpio": "Скорпион",
            "Sagittarius": "Стрелец", "Capricorn": "Козерог", "Aquarius": "Водолей", "Pisces": "Рыбы"
        }
        
        results = {}
        signs_list = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        major = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        
        for pos in chart.positions:
            name = getattr(pos, 'name', '')
            if name not in major: continue
            
            sign_idx = int(pos.longitude // 30)
            sign_en = signs_list[sign_idx]
            sign_ru = rus_signs[sign_en]
            
            house = self.get_house_by_lon(chart, pos.longitude)
            
            status = "Перегрин (Без особых сил)"
            score = 0
            
            if rulers.get(sign_en) == name:
                status = "Обитель (Хозяин положения)"
                score += 5
            elif exaltations.get(sign_en) == name:
                status = "Экзальтация (Максимальная сила)"
                score += 4
            else:
                opp_sign = signs_list[(sign_idx + 6) % 12]
                if rulers.get(opp_sign) == name:
                    status = "Изгнание (Слабость/Вред)"
                    score -= 5
                elif exaltations.get(opp_sign) == name:
                    status = "Падение (Ущербность)"
                    score -= 4
            
            accidental = []
            if house in [1, 4, 7, 10]: 
                accidental.append("Угловой (Действует активно)")
                score += 5
            elif house in [2, 5, 8, 11]:
                accidental.append("Срединный (Стабилен)")
                score += 2
            else:
                accidental.append("Падающий (Скрыт/Слаб)")
                score -= 2
                
            if pos.is_retrograde:
                accidental.append("Ретроградный (Задержки)")
                score -= 4
                
            results[rus_names.get(name, name)] = {
                "sign": sign_ru,
                "house": house,
                "status": status,
                "accidental": accidental,
                "score": score
            }
        return results

    def find_horary_aspects(self, chart) -> List[Dict]:
        """
        # PURPOSE: Найти хорарные аспекты с точным определением сходимости.
        # LOGIC: Сравнивает расстояние сейчас и через 1 час. Если уменьшается — сходящийся.
        """
        major = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", 
                 "Uranus", "Neptune", "Pluto", "North Node"]
                 
        rus_names = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн",
            "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон",
            "North Node": "Сев.Узел", "South Node": "Южн.Узел"
        }
        
        pos_now = {p.name: p.longitude for p in chart.positions if p.name in major}
        dt_plus = chart.datetime.utc_datetime + timedelta(hours=1)
        loc_input = {
            "latitude": chart.location.latitude,
            "longitude": chart.location.longitude,
            "name": chart.location.name
        }
        chart_plus = self.create_transit_chart(dt_plus.isoformat(), loc_input)
        pos_plus = {p.name: p.longitude for p in chart_plus.positions if p.name in major}
        
        aspects = []
        names = sorted(pos_now.keys())
        
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                l1 = pos_now[name1]
                l2 = pos_now[name2]
                
                diff = abs(l1 - l2)
                if diff > 180: diff = 360 - diff
                
                orb_limit = 6.0
                if "Moon" in [name1, name2]: orb_limit = 12.0
                
                aspect_type = None
                target = 0
                if diff <= orb_limit: aspect_type, target = "Conjunction", 0
                elif abs(diff - 60) <= orb_limit: aspect_type, target = "Sextile", 60
                elif abs(diff - 90) <= orb_limit: aspect_type, target = "Square", 90
                elif abs(diff - 120) <= orb_limit: aspect_type, target = "Trine", 120
                elif abs(diff - 180) <= orb_limit: aspect_type, target = "Opposition", 180
                
                if aspect_type:
                    l1_plus = pos_plus.get(name1, l1)
                    l2_plus = pos_plus.get(name2, l2)
                    diff_plus = abs(l1_plus - l2_plus)
                    if diff_plus > 180: diff_plus = 360 - diff_plus
                    
                    dist_now = abs(diff - target)
                    dist_plus = abs(diff_plus - target)
                    is_applying = dist_plus < dist_now
                    
                    aspects.append({
                        "p1": rus_names.get(name1, name1), 
                        "p2": rus_names.get(name2, name2),
                        "type": aspect_type,
                        "orb": round(dist_now, 2),
                        "is_applying": is_applying,
                        "status": "Applying (Сходящийся)" if is_applying else "Separating (Расходящийся)"
                    })
        return aspects

    def get_horary_meta(self, chart) -> Dict[str, str]:
        """
        # PURPOSE: Determine main significators for Horary (L1-L12).
        """
        rus_names = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн",
            "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон"
        }
        
        rulers = self.get_house_rulers(chart)
        meta = {"Moon": "Луна"}
        
        for i in range(1, 13):
            r_name = rulers.get(i, "Unknown")
            meta[f"L{i}"] = rus_names.get(r_name, r_name)
            
        return meta
    # #END_BLOCK_HORARY_CALC

    def calculate_solar_return_chart(self, natal_chart, year: int, location_str: str):
        """
        # PURPOSE: Calculate Solar Return chart for a specific year.
        """
        # We need the natal Sun longitude
        sun = next((p for p in natal_chart.positions if p.name == "Sun"), None)
        if not sun: raise ValueError("Natal Sun not found")
        
        # Approximate date: Birth month/day in target year
        # Stellium ReturnBuilder handles exact calculation
        # But we need to use ReturnBuilder correctly.
        # Assuming stellium has ReturnBuilder (imported at top)
        
        # If location is dict, convert? Builder expects object or string.
        # Let's try to use the raw location_str (which might be a dict from payload).
        
        builder = ReturnBuilder(natal_chart)
        # We want the return for 'year'. 
        # Stellium might expect 'start_date' to search from.
        search_start = datetime(year, 1, 1)
        
        # This part depends on stellium library specifics. 
        # Assuming standard pattern:
        ret_chart = builder.get_solar_return(year, location_str)
        return ret_chart

    def calculate_synastry_data(self, chart1, chart2) -> Dict:
        """
        # PURPOSE: Calculate rich synastry data (aspects, score, categories).
        """
        aspects = []
        major = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "ASC", "MC"]
        
        pos1 = {p.name: p for p in chart1.positions if p.name in major}
        pos2 = {p.name: p for p in chart2.positions if p.name in major}
        
        score = 50 # Base score
        
        categories = {
            "sexual": [], # Venus, Mars, Pluto
            "emotional": [], # Moon, Sun, Neptune
            "intellectual": [], # Mercury, Uranus
            "conflict": [], # Mars, Saturn, Pluto squares/oppositions
            "karmic": [] # Saturn, Nodes
        }
        
        for n1, p1 in pos1.items():
            for n2, p2 in pos2.items():
                diff = abs(p1.longitude - p2.longitude)
                if diff > 180: diff = 360 - diff
                
                orb = 3.5
                if "Sun" in [n1, n2] or "Moon" in [n1, n2]: orb = 6.0
                
                atype = None
                if diff <= orb: atype = "Conjunction"
                elif abs(diff - 60) <= orb: atype = "Sextile"
                elif abs(diff - 90) <= orb: atype = "Square"
                elif abs(diff - 120) <= orb: atype = "Trine"
                elif abs(diff - 180) <= orb: atype = "Opposition"
                
                if atype:
                    entry = {
                        "p1": n1, "p2": n2, "type": atype, "orb": round(abs(diff - (0 if atype=="Conjunction" else 180 if atype=="Opposition" else 90 if atype=="Square" else 120 if atype=="Trine" else 60)), 2)
                    }
                    aspects.append(entry)
                    
                    # Scoring
                    weight = 2 if (n1 in ["Sun", "Moon", "ASC"] or n2 in ["Sun", "Moon", "ASC"]) else 1
                    if atype in ["Trine", "Sextile"]:
                        score += 5 * weight
                    elif atype in ["Square", "Opposition"]:
                        score -= 5 * weight
                    elif atype == "Conjunction":
                        if n1 in ["Mars", "Saturn", "Pluto"] and n2 in ["Mars", "Saturn", "Pluto"]: # Malefics
                            score -= 3 * weight
                        else:
                            score += 4 * weight
                            
                    # Categorization
                    pair = {n1, n2}
                    if pair.intersection({"Venus", "Mars", "Pluto"}):
                        if len(pair.intersection({"Venus", "Mars", "Pluto"})) == 2:
                            categories["sexual"].append(entry)
                            
                    if pair.intersection({"Moon", "Sun", "Neptune"}):
                        if "Moon" in pair:
                            categories["emotional"].append(entry)
                            
                    if pair.intersection({"Mercury", "Uranus"}):
                        if "Mercury" in pair:
                            categories["intellectual"].append(entry)
                            
                    if atype in ["Square", "Opposition"] and (n1 in ["Mars", "Saturn"] or n2 in ["Mars", "Saturn"]):
                        categories["conflict"].append(entry)
                        
                    if "Saturn" in pair and ("Sun" in pair or "Moon" in pair):
                        categories["karmic"].append(entry)

        score = max(0, min(100, score))
        
        return {
            "aspects": aspects, 
            "score": score,
            "categories": categories
        }

    # #START_BLOCK_FIXED_STARS
    def get_fixed_star_conjunctions(self, chart, orb=1.0) -> List[Dict]:
        """
        # PURPOSE: Поиск соединений с неподвижными звездами.
        # CONTEXT: Натал или транзит.
        # ACTION: Сверяет координаты планет с координатами звезд из реестра.
        # MEASURE: Список словарей (звезда, планета, орбис).
        """
        target_stars = [
            "Aldebaran", "Regulus", "Antares", "Fomalhaut", # Royal
            "Algol", "Spica", "Sirius", "Vega", "Betelgeuse", 
            "Rigel", "Capella", "Procyon", "Altair", "Arcturus"
        ]
        
        conjunctions = []
        chart_objs = []
        for pos in chart.positions:
            name = getattr(pos, 'name', '') or str(pos.object)
            if hasattr(pos, 'longitude'):
                chart_objs.append({"name": name, "lon": pos.longitude})

        jd = chart.datetime.julian_day
        for star_name in target_stars:
            try:
                star_pos = get_fixed_star_info(star_name, jd)
                star_lon = star_pos.longitude
                for obj in chart_objs:
                    diff = abs(obj['lon'] - star_lon)
                    if diff > 180: diff = 360 - diff
                    if diff <= orb:
                        conjunctions.append({
                            "star": star_name,
                            "planet": obj['name'],
                            "orb": diff,
                            "star_lon": star_lon
                        })
            except: continue
        return conjunctions
    # #END_BLOCK_FIXED_STARS

    # #START_BLOCK_TRANSIT_ASPECTS
    def find_transit_aspects(self, natal_chart, transit_chart, orb=1.5) -> List[Dict]:
        """
        # PURPOSE: Расчет аспектов транзитов к наталу.
        # CONTEXT: Прогноз на день/неделю.
        # ACTION: Сравнивает долготы транзитных и натальных планет.
        # MEASURE: Список аспектов с указанием типа и точности.
        """
        aspects = []
        def get_diff(a, b):
            d = abs(a - b)
            if d > 180: d = 360 - d
            return d

        natal_points = {getattr(pos, 'name', '') or str(pos.object): pos.longitude 
                       for pos in natal_chart.positions if hasattr(pos, 'longitude')}

        for pos in transit_chart.positions:
            t_name = getattr(pos, 'name', '') or str(pos.object)
            if not hasattr(pos, 'longitude') or t_name in ["Moon", "Part of Fortune"]: continue
                
            t_lon = pos.longitude
            for n_name, n_lon in natal_points.items():
                diff = get_diff(t_lon, n_lon)
                aspect_name = ""
                if diff <= orb: aspect_name = "Соединение (0°)"
                elif abs(diff - 180) <= orb: aspect_name = "Оппозиция (180°)"
                elif abs(diff - 120) <= orb: aspect_name = "Тригон (120°)"
                elif abs(diff - 90) <= orb: aspect_name = "Квадрат (90°)"
                elif abs(diff - 60) <= orb: aspect_name = "Секстиль (60°)"
                
                if aspect_name:
                    aspects.append({
                        "transit": t_name,
                        "natal": n_name,
                        "type": aspect_name,
                        "exact_diff": diff
                    })
        return aspects

    def find_natal_aspects(self, chart, orb=6.0) -> List[Dict]:
        """
        # PURPOSE: Расчет внутренних аспектов натальной карты.
        # CONTEXT: Для отрисовки карты (SVG) и анализа личности.
        # ACTION: Сравнивает долготы планет внутри одной карты.
        # MEASURE: Список аспектов.
        """
        major_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        positions = [p for p in chart.positions if getattr(p, 'name', '') in major_planets and hasattr(p, 'longitude')]
        
        aspects = []
        for i, p1 in enumerate(positions):
            for p2 in positions[i+1:]:
                diff = abs(p1.longitude - p2.longitude)
                if diff > 180: diff = 360 - diff
                
                aspect_type = None
                target_angle = 0
                if diff <= 8.0: 
                    aspect_type = "conjunction"
                    target_angle = 0
                elif abs(diff - 180) <= 8.0: 
                    aspect_type = "opposition"
                    target_angle = 180
                elif abs(diff - 120) <= 8.0: 
                    aspect_type = "trine"
                    target_angle = 120
                elif abs(diff - 90) <= 8.0: 
                    aspect_type = "square"
                    target_angle = 90
                elif abs(diff - 60) <= 6.0: 
                    aspect_type = "sextile"
                    target_angle = 60
                
                if aspect_type:
                    aspects.append({
                        "p1": getattr(p1, 'name', ''),
                        "p2": getattr(p2, 'name', ''),
                        "type": aspect_type,
                        "angle": diff,
                        "orb": round(abs(diff - target_angle), 2)
                    })
        return aspects

    def calculate_pars_fortuna(self, chart) -> float:
        """ASC + Moon - Sun (Day) or ASC + Sun - Moon (Night). Using Day formula for now as generic or implement sect check."""
        # Simple sect check: Sun above horizon (House 7-12).
        # We need houses.
        asc = next((p for p in chart.positions if p.name == "ASC"), None)
        moon = next((p for p in chart.positions if p.name == "Moon"), None)
        sun = next((p for p in chart.positions if p.name == "Sun"), None)
        
        if not (asc and moon and sun): return 0.0
        
        # Determine sect: if Sun is in house 7,8,9,10,11,12 -> Day.
        # But we need house of Sun.
        # Let's use simple formula: Part = ASC + Moon - Sun.
        # This is standard Ptyolemy.
        pars = (asc.longitude + moon.longitude - sun.longitude) % 360
        return pars
    # #END_BLOCK_TRANSIT_ASPECTS

    # #START_BLOCK_SOLAR_RETURN
    def create_solar_return(self, natal_chart, year: int, location_str: str = None, house_system=None):
        """
        # PURPOSE: Расчет Соляра (Солнечного возвращения).
        # CONTEXT: Прогноз на год.
        # ACTION: Находит момент возвращения Солнца и строит карту на указанную локацию.
        # MEASURE: Объект Chart (Solar Return).
        """
        loc = natal_chart.location
        if location_str:
             dummy_builder = ChartBuilder.from_details("2000-01-01", location_str)
             dummy_builder.with_house_systems([WholeSignHouses()])
             dummy = dummy_builder.calculate()
             loc = dummy.location

        builder = ReturnBuilder.solar(natal_chart, year, location=loc)
        if house_system: builder.with_house_systems([house_system])
        return builder.calculate()
    # #END_BLOCK_SOLAR_RETURN

    # #START_BLOCK_SOLAR_ARC
    def calculate_solar_arc_directions(self, natal_chart, target_date_dt):
        """
        # PURPOSE: Расчет дирекций солнечных дуг.
        # CONTEXT: Стратегический прогноз (10 лет).
        # ACTION: Сдвигает все натальные точки на дугу прогрессивного Солнца.
        # MEASURE: Словарь с величиной дуги и новыми позициями планет.
        """
        birth_dt = natal_chart.datetime.utc_datetime
        diff = target_date_dt - birth_dt
        age_years = diff.days / 365.2425
        prog_date = birth_dt + timedelta(days=age_years)
        
        prog_builder = ChartBuilder.from_details(prog_date, natal_chart.location.name or "Greenwich")
        prog_builder.with_house_systems([WholeSignHouses()])
        prog_chart = prog_builder.calculate()
        
        natal_sun = self.get_object_data(natal_chart, "Sun")
        prog_sun = self.get_object_data(prog_chart, "Sun")
        
        if not natal_sun or not prog_sun: return {}
            
        arc = (prog_sun.longitude - natal_sun.longitude) % 360
        directed_positions = {getattr(pos, 'name', '') or str(pos.object): (pos.longitude + arc) % 360 
                             for pos in natal_chart.positions}
            
        return {"arc": arc, "positions": directed_positions}
    # #END_BLOCK_SOLAR_ARC

    # #START_BLOCK_UTILITIES
    def get_house_by_lon(self, chart, lon):
        """
        # PURPOSE: Определение номера дома по долготе.
        # CONTEXT: Хелпер для анализа положений планет.
        # ACTION: Сверяет долготу с куспидами домов карты.
        # MEASURE: Номер дома (1-12) или "?".
        """
        try:
            hc = chart.get_houses()
            cusps = hc.cusps
            for i in range(12):
                c1, c2 = cusps[i], cusps[(i + 1) % 12]
                if c1 < c2:
                    if c1 <= lon < c2: return i + 1
                else:
                    if lon >= c1 or lon < c2: return i + 1
            return "?"
        except: return "?"

    def get_object_data(self, chart, obj_name):
        for pos in chart.positions:
            name = (getattr(pos, 'name', '') or str(pos.object)).lower()
            if name == obj_name.lower(): return pos
        return None

    def dms(self, deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = int(((deg - d) * 60 - m) * 60)
        return f"{d}°{m:02d}'{s:02d}\""
    # #END_BLOCK_UTILITIES

    def create_transit_chart(self, dt_str, location_str, house_system=None):
        """
        # PURPOSE: Создание транзитной карты на заданную дату и локацию.
        # CONTEXT: Прогнозы, хорары и динамические расчеты.
        # ACTION: Конфигурирует астероиды, выбирает систему домов и рассчитывает карту.
        # MEASURE: Возвращает объект Chart из библиотеки stellium.
        """
        # Clean datetime string from timezone offset if present
        if isinstance(dt_str, str) and "+" in dt_str:
            dt_str = dt_str.split("+")[0]

        builder = ChartBuilder.from_details(dt_str, location_str, name="Transit")

        config = CalculationConfig()
        config.include_asteroids = ["Ceres", "Pallas", "Juno", "Vesta", "Chiron"]
        builder.with_config(config)

        if not house_system:
            lat = None
            if isinstance(location_str, dict):
                lat = location_str.get("latitude")
            if lat is None:
                resolved = getattr(builder, "location", None)
                lat = getattr(resolved, "latitude", None)
            if lat is None:
                house_system = PlacidusHouses()
            else:
                house_system = self._resolve_default_house_system(lat)

        builder.with_house_systems([house_system])
        return builder.calculate()

    def find_all_patterns(self, chart, orb=6.0):
        """
        # PURPOSE: Поиск базовых конфигураций аспектов (фигур) в карте.
        # CONTEXT: Используется для вывода "Фигур" в универсальном анализаторе.
        # ACTION: Строит карту аспектов и выделяет трины/квадраты/оппозиции.
        # MEASURE: Список словарей с типом фигуры и списком точек.
        """
        major = {
            "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter",
            "Saturn", "Uranus", "Neptune", "Pluto",
            "North Node", "South Node", "Chiron"
        }
        aliases = {
            "True Node": "North Node",
        }
        points = {}
        for pos in chart.positions:
            raw_name = getattr(pos, "name", "") or str(pos.object)
            name = aliases.get(raw_name, raw_name)
            if name in major and hasattr(pos, "longitude"):
                points[name] = pos.longitude

        names = sorted(points.keys())
        
        # Build aspect graph
        aspects = {
            "conjunction": set(), "opposition": set(), "trine": set(), 
            "square": set(), "sextile": set()
        }

        def pair_key(a, b):
            return tuple(sorted((a, b)))

        for a, b in itertools.combinations(names, 2):
            diff = abs(points[a] - points[b])
            if diff > 180: diff = 360 - diff
            
            if diff <= orb + 2: aspects["conjunction"].add(pair_key(a, b)) # Conjunction needs tighter orb usually? Let's use standard.
            elif abs(diff - 180) <= orb: aspects["opposition"].add(pair_key(a, b))
            elif abs(diff - 120) <= orb: aspects["trine"].add(pair_key(a, b))
            elif abs(diff - 90) <= orb: aspects["square"].add(pair_key(a, b))
            elif abs(diff - 60) <= orb - 1: aspects["sextile"].add(pair_key(a, b)) # Sextile usually tighter

        patterns = []
        seen = set()

        # Iterate triplets
        for a, b, c in itertools.combinations(names, 3):
            # Grand Trine
            if (pair_key(a, b) in aspects["trine"] and 
                pair_key(a, c) in aspects["trine"] and 
                pair_key(b, c) in aspects["trine"]):
                key = ("Большой тригон", tuple(sorted([a, b, c])))
                if key not in seen:
                    seen.add(key)
                    patterns.append({"type": "Большой тригон", "points": [a, b, c]})

            # T-Square (Opposition + 2 Squares)
            # Find opposition pair first
            opp_pairs = [p for p in [pair_key(a, b), pair_key(a, c), pair_key(b, c)] if p in aspects["opposition"]]
            for opp in opp_pairs:
                apex = list(set([a, b, c]) - set(opp))[0]
                if (pair_key(opp[0], apex) in aspects["square"] and 
                    pair_key(opp[1], apex) in aspects["square"]):
                    key = ("Т-квадрат", tuple(sorted([a, b, c])))
                    if key not in seen:
                        seen.add(key)
                        patterns.append({"type": "Т-квадрат", "points": [a, b, c]})

            # Bisextile (Trine + 2 Sextiles)
            # Find trine pair
            trine_pairs = [p for p in [pair_key(a, b), pair_key(a, c), pair_key(b, c)] if p in aspects["trine"]]
            for trine in trine_pairs:
                apex = list(set([a, b, c]) - set(trine))[0]
                if (pair_key(trine[0], apex) in aspects["sextile"] and 
                    pair_key(trine[1], apex) in aspects["sextile"]):
                    key = ("Бисекстиль", tuple(sorted([a, b, c])))
                    if key not in seen:
                        seen.add(key)
                        patterns.append({"type": "Бисекстиль", "points": [a, b, c]})

        # Iterate quadruplets for Grand Cross and Kite
        for a, b, c, d in itertools.combinations(names, 4):
            # Grand Cross (4 squares + 2 oppositions)
            # Simplified: just check if it contains 2 oppositions and squares connect them
            # Actually easier: check if it's 2 T-Squares sharing opposition?
            # Or direct check:
            pairs = [pair_key(*p) for p in itertools.combinations([a, b, c, d], 2)]
            opp_count = sum(1 for p in pairs if p in aspects["opposition"])
            square_count = sum(1 for p in pairs if p in aspects["square"])
            if opp_count >= 2 and square_count >= 4:
                key = ("Большой крест", tuple(sorted([a, b, c, d])))
                if key not in seen:
                    seen.add(key)
                    patterns.append({"type": "Большой крест", "points": [a, b, c, d]})
            
            # Kite (Grand Trine + Bisextile sharing a Trine side)
            # Structure: Grand Trine (A,B,C) + Planet D making sextiles to A and B, and opposition to C.
            # Check for Grand Trine subset
            triplets = itertools.combinations([a, b, c, d], 3)
            grand_trine = None
            for t in triplets:
                if (pair_key(t[0], t[1]) in aspects["trine"] and 
                    pair_key(t[0], t[2]) in aspects["trine"] and 
                    pair_key(t[1], t[2]) in aspects["trine"]):
                    grand_trine = t
                    break
            
            if grand_trine:
                apex = list(set([a, b, c, d]) - set(grand_trine))[0]
                # Check if apex makes sextiles to 2 points of trine and opposition to 1
                sextile_count = 0
                opposition_count = 0
                for p in grand_trine:
                    pk = pair_key(apex, p)
                    if pk in aspects["sextile"]: sextile_count += 1
                    if pk in aspects["opposition"]: opposition_count += 1
                
                if sextile_count >= 2 and opposition_count >= 1:
                    key = ("Парус", tuple(sorted([a, b, c, d])))
                    if key not in seen:
                        seen.add(key)
                        patterns.append({"type": "Парус", "points": [a, b, c, d]})

        # Stellium (3+ in conjunction or sign) - Simplified conjunction check
        # Checking pure conjunction chain is complex graph problem.
        # Simple heuristic: 3 planets within orb*2 of each other?
        # Or just use sign stellium.
        # Let's stick to geometric patterns for now.

        return patterns

    def find_horary_aspects(self, chart) -> List[Dict]:
        """
        # PURPOSE: Найти хорарные аспекты с точным определением сходимости.
        # LOGIC: Сравнивает расстояние сейчас и через 1 час. Если уменьшается — сходящийся.
        """
        major = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", 
                 "Uranus", "Neptune", "Pluto", "North Node"]
                 
        rus_names = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн",
            "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон",
            "North Node": "Сев.Узел", "South Node": "Южн.Узел"
        }
        
        # 1. Get current positions map
        pos_now = {p.name: p.longitude for p in chart.positions if p.name in major}
        
        # 2. Calculate T+1 hour positions
        dt_plus = chart.datetime.utc_datetime + timedelta(hours=1)
        # We need a location string or object. chart.location has lat/lon.
        loc_input = {
            "latitude": chart.location.latitude,
            "longitude": chart.location.longitude,
            "name": chart.location.name
        }
        # Use existing method to create chart
        # Note: We need to use 'self' to call create_transit_chart, but this method uses 'house_system'. 
        # We can just use default houses as we only need planetary positions.
        chart_plus = self.create_transit_chart(dt_plus.isoformat(), loc_input)
        pos_plus = {p.name: p.longitude for p in chart_plus.positions if p.name in major}
        
        aspects = []
        names = sorted(pos_now.keys())
        
        for i, name1 in enumerate(names):
            for name2 in names[i+1:]:
                l1 = pos_now[name1]
                l2 = pos_now[name2]
                
                diff = abs(l1 - l2)
                if diff > 180: diff = 360 - diff
                
                orb_limit = 6.0
                if "Moon" in [name1, name2]: orb_limit = 12.0
                
                aspect_type = None
                target = 0
                
                if diff <= orb_limit: aspect_type, target = "Conjunction", 0
                elif abs(diff - 60) <= orb_limit: aspect_type, target = "Sextile", 60
                elif abs(diff - 90) <= orb_limit: aspect_type, target = "Square", 90
                elif abs(diff - 120) <= orb_limit: aspect_type, target = "Trine", 120
                elif abs(diff - 180) <= orb_limit: aspect_type, target = "Opposition", 180
                
                if aspect_type:
                    # Check convergence
                    l1_plus = pos_plus.get(name1, l1)
                    l2_plus = pos_plus.get(name2, l2)
                    
                    diff_plus = abs(l1_plus - l2_plus)
                    if diff_plus > 180: diff_plus = 360 - diff_plus
                    
                    # We compare distance to exact aspect (target)
                    dist_now = abs(diff - target)
                    dist_plus = abs(diff_plus - target)
                    
                    is_applying = dist_plus < dist_now
                    
                    aspects.append({
                        "p1": name1, 
                        "p2": name2,
                        "type": aspect_type,
                        "orb": round(dist_now, 2),
                        "is_applying": is_applying, # True/False
                        "status": "Applying (Сходящийся)" if is_applying else "Separating (Расходящийся)"
                    })
        return aspects
        """
        # PURPOSE: Проверка карты на радикальность (пригодность для суждения).
        """
        issues = []
        warnings = []
        score = 10
        
        # 1. ASC check
        asc = next((p for p in chart.positions if p.name == "ASC"), None)
        if asc:
            deg = asc.longitude % 30
            if deg < 3:
                issues.append(f"Ранний Асцендент ({deg:.1f}°). Ситуация еще не созрела.")
                score -= 3
            elif deg > 27:
                issues.append(f"Поздний Асцендент ({deg:.1f}°). Ситуация уже завершена или безнадежна.")
                score -= 3
                
        # 2. Moon VOC (Void of Course)
        # Simplified check: is Moon making applying major aspects before leaving sign?
        # This requires checking future aspects. 
        # For now, let's use a simpler check if implemented or skip.
        # Let's verify Moon position relative to next sign ingress.
        
        # 3. Saturn in 1st or 7th
        saturn = next((p for p in chart.positions if p.name == "Saturn"), None)
        if saturn:
            house = self.get_house_by_lon(chart, saturn.longitude)
            if house == 1:
                warnings.append("Сатурн в 1 доме. Кверент может быть подавлен или ошибаться.")
                score -= 2
            elif house == 7:
                warnings.append("Сатурн в 7 доме. Ошибки в суждении астролога или проблемы с партнером.")
                score -= 1 # Less critical for judgment itself unless astrologer asks
                
        return {
            "score": max(0, score),
            "is_radical": score >= 5,
            "issues": issues,
            "warnings": warnings
        }

    def calculate_dignities(self, chart) -> Dict[str, Dict]:
        """
        # PURPOSE: Рассчитать эссенциальные и акцидентальные достоинства планет.
        """
        rulers = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
            "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
            "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        exaltations = {
            "Aries": "Sun", "Taurus": "Moon", "Cancer": "Jupiter", "Virgo": "Mercury",
            "Libra": "Saturn", "Capricorn": "Mars", "Pisces": "Venus"
        }
        falls = {
            "Aries": "Saturn", "Taurus": "Uranus", "Cancer": "Mars", "Virgo": "Venus",
            "Libra": "Sun", "Capricorn": "Jupiter", "Pisces": "Mercury"
        } 
        # Detriment is opposite to Ruler.
        
        results = {}
        signs_list = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        major = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        
        for pos in chart.positions:
            name = getattr(pos, 'name', '')
            if name not in major: continue
            
            sign_idx = int(pos.longitude // 30)
            sign = signs_list[sign_idx]
            house = self.get_house_by_lon(chart, pos.longitude)
            
            status = "Peregrine"
            score = 0
            
            # Essential
            if rulers.get(sign) == name:
                status = "Domicile (Обитель)"
                score += 5
            elif exaltations.get(sign) == name:
                status = "Exaltation (Экзальтация)"
                score += 4
            else:
                # Check detriment (opposite sign ruler)
                opp_sign = signs_list[(sign_idx + 6) % 12]
                if rulers.get(opp_sign) == name:
                    status = "Detriment (Изгнание)"
                    score -= 5
                # Check fall (opposite exaltation)
                elif exaltations.get(opp_sign) == name:
                    status = "Fall (Падение)"
                    score -= 4
            
            # Accidental (House)
            accidental = []
            if house in [1, 4, 7, 10]: 
                accidental.append("Angular (Угловой)")
                score += 5
            elif house in [2, 5, 8, 11]:
                accidental.append("Succedent (Срединный)")
                score += 2
            else:
                accidental.append("Cadent (Падающий)")
                score -= 2
                
            if pos.is_retrograde:
                accidental.append("Retrograde")
                score -= 4
            if getattr(pos, 'speed', 0) < 0.5: # Slow? Need average speeds.
                pass 
                
            results[name] = {
                "sign": sign,
                "house": house,
                "status": status,
                "accidental": accidental,
                "score": score
            }
            
        return results
        from stellium.core.models import ChartDateTime
        from stellium.engines.ephemeris import SwissEphemerisEngine
        from stellium.utils.time import julian_day_to_datetime

        dt_utc = julian_day_to_datetime(julian_day)
        chart_dt = ChartDateTime(utc_datetime=dt_utc, julian_day=julian_day, local_datetime=dt_utc)
        location = ChartLocation(latitude=0.0, longitude=0.0, name="Greenwich", timezone="UTC")

        ephem = SwissEphemerisEngine()
        positions = ephem.calculate_positions(chart_dt, location, objects=["Mean Apogee"])
        if not positions:
            raise ValueError("Selena calculation failed")

        apogee_lon = positions[0].longitude
        return (apogee_lon + 180.0) % 360

    def get_combustion_status(self, chart):
        """Checks if planets are combust, under rays, or in cazimi."""
        sun_pos = next((p for p in chart.positions if getattr(p, 'name', '') == 'Sun'), None)
        if not sun_pos: return {}
        
        results = {}
        for pos in chart.positions:
            name = getattr(pos, 'name', '')
            if name in ["Sun", "ASC", "MC", "Vertex"]: continue
            if not hasattr(pos, 'longitude'): continue
            
            diff = abs(pos.longitude - sun_pos.longitude)
            if diff > 180: diff = 360 - diff
            
            if diff <= 0.28: # 17 minutes
                results[name] = "🔥 КАЗИМИ (В сердце Солнца - Сверхсила)"
            elif diff <= 8.5:
                results[name] = "💨 СОЖЖЕНИЕ (Ослабление функций)"
            elif diff <= 17.0:
                results[name] = "🌤 ПОД ЛУЧАМИ (Скрытая деятельность)"
        return results

    def get_antiscia(self, longitude):
        """Calculates Antiscia (reflection across 0 Cancer/Cap axis)."""
        # Antiscia = 90 - (lon - 90) = 180 - lon
        # But relative to Cancer/Cap axis
        # Formula: 90 - (longitude - 90) = 180 - longitude
        # Correct formula for Solstice points:
        anti = (90 - (longitude - 90)) % 360
        # Contra-antiscia is opposite to Antiscia
        contra = (anti + 180) % 360
        return anti, contra

    def get_midpoints(self, chart, pairs=[("Sun", "Moon"), ("ASC", "MC"), ("Venus", "Mars")]):
        """Calculates specific midpoints."""
        points = {getattr(p, 'name', ''): p.longitude for p in chart.positions if hasattr(p, 'longitude')}
        results = {}
        for p1, p2 in pairs:
            if p1 in points and p2 in points:
                l1, l2 = points[p1], points[p2]
                # Midpoint calculation handling circular wrap
                if abs(l1 - l2) > 180:
                    mid = (l1 + l2 + 360) / 2 % 360
                else:
                    mid = (l1 + l2) / 2 % 360
                results[f"{p1}/{p2}"] = mid
        return results

    def get_septener_ruler(self, sign_name):
        """Returns the traditional ruler of a sign."""
        rulers = {
            "Овен": "Mars", "Телец": "Venus", "Близ": "Mercury", "Рак": "Moon",
            "Лев": "Sun", "Дева": "Mercury", "Весы": "Venus", "Скорп": "Mars",
            "Стрел": "Jupiter", "Козер": "Saturn", "Водол": "Saturn", "Рыбы": "Jupiter"
        }
        return rulers.get(sign_name)

    def get_house_rulers(self, chart):
        """Returns a map of house index (1-12) to its ruling planet name."""
        cusps = chart.get_houses().cusps
        rulers = {}
        for i, lon in enumerate(cusps):
            sign = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", 
                    "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"][int(lon // 30)]
            rulers[i + 1] = self.get_septener_ruler(sign)
        return rulers

    # #START_BLOCK_FORECAST_DATA
    def calculate_forecast_year_data(self, natal_chart, target_year: int, location_str: str) -> Dict[str, Any]:
        """
        # PURPOSE: Calculate full astronomical data for a year forecast.
        # INPUT: natal_chart, target_year, location_str.
        # OUTPUT: Dict with keys: profection, solar_return, solar_arcs, months (list).
        # CONTEXT: Used by Year Forecast report type.
        """
        RUS_NAMES = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн", "Uranus": "Уран",
            "Neptune": "Нептун", "Pluto": "Плутон", "Chiron": "Хирон",
            "True Node": "Сев.Узел", "South Node": "Южн.Узел", "Mean Apogee": "Лилит",
            "ASC": "ASC", "MC": "MC", "Vertex": "Вертекс", "Part of Fortune": "Фортуна"
        }
        
        # 1. Profection (Time Lord)
        birth_dt = natal_chart.datetime.utc_datetime
        age = target_year - birth_dt.year
        prof_house = (age % 12) + 1
        lord_name = self.get_house_rulers(natal_chart).get(prof_house, "?")
        profection = {
            "house": prof_house,
            "lord": RUS_NAMES.get(lord_name, lord_name),
            "age": age
        }
        
        # 2. Solar Return
        solar_return = {}
        try:
            sr_chart = self.create_solar_return(natal_chart, target_year - 1, location_str=location_str, house_system=WholeSignHouses())
            asc_pos = next((p for p in sr_chart.positions if p.name == "ASC"), None)
            sun_pos = next((p for p in sr_chart.positions if p.name == "Sun"), None)
            
            sr_asc_sign = ""
            if asc_pos:
                signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
                sr_asc_sign = signs[int(asc_pos.longitude // 30)]
            
            solar_return = {
                "datetime": sr_chart.datetime.local_datetime.isoformat(),
                "asc_sign": sr_asc_sign,
                "sun_house": self.get_house_by_lon(sr_chart, sun_pos.longitude) if sun_pos else "?"
            }
        except Exception:
            pass
            
        # 3. Solar Arcs
        arcs = []
        try:
            arc_data = self.calculate_solar_arc_directions(natal_chart, datetime(target_year, 6, 15))
            for d_name, d_lon in arc_data.get("positions", {}).items():
                if d_name not in RUS_NAMES and d_name not in ["ASC", "MC"]: continue
                for n_pos in natal_chart.positions:
                    n_n = getattr(n_pos, 'name', '')
                    if n_n in RUS_NAMES or n_n in ["ASC", "MC"]:
                        diff = abs(d_lon - n_pos.longitude)
                        if diff > 180: diff = 360 - diff
                        if diff <= 1.0:
                            arcs.append({
                                "direction": RUS_NAMES.get(d_name, d_name),
                                "natal": RUS_NAMES.get(n_n, n_n),
                                "orb": diff
                            })
        except Exception:
            pass
            
        # 4. Monthly Transits
        months_data = []
        for m in range(1, 13):
            # Mid-month snapshot
            t_chart = self.create_transit_chart(f"{target_year}-{m:02d}-15 12:00", location_str)
            hits = self.find_transit_aspects(natal_chart, t_chart, orb=1.5)
            
            important_hits = []
            for h in hits:
                # Filter for major transits
                if h['transit'] in ["Moon"]: continue # Skip fast Moon
                if h['transit'] in ["Sun", "Mercury", "Venus"] and h['natal'] not in ["Sun", "Moon", "ASC", "MC"]: continue # Skip fast unless to lights
                
                important_hits.append({
                    "transit": RUS_NAMES.get(h['transit'], h['transit']),
                    "natal": RUS_NAMES.get(h['natal'], h['natal']),
                    "aspect": h['type'],
                    "orb": h['exact_diff']
                })
            
            # Tension Index
            tension_hits = [h for h in hits if h['transit'] in ["Saturn", "Pluto", "Mars"] and h['type'] in ["Квадрат (90°)", "Оппозиция (180°)"]]
            tension_score = len(tension_hits)
            status = "GREEN"
            if tension_score >= 2: status = "YELLOW"
            if tension_score >= 4: status = "RED"
            
            months_data.append({
                "month": m,
                "status": status,
                "tension_index": tension_score,
                "aspects": important_hits
            })
            
        return {
            "target_year": target_year,
            "profection": profection,
            "solar_return": solar_return,
            "solar_arcs": arcs,
            "months": months_data
        }
    # #END_BLOCK_FORECAST_DATA

    # #START_BLOCK_WEEKLY_DATA
    def calculate_forecast_week_data(self, natal_chart, start_date, location_str: str) -> Dict[str, Any]:
        """
        # PURPOSE: Calculate daily transits for a week with Traffic Light metrics.
        # INPUT: natal_chart, start_date (str/datetime), location_str.
        # OUTPUT: Dict with 'days' list and 'summary'.
        """
        RUS_NAMES = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн", "Uranus": "Уран",
            "Neptune": "Нептун", "Pluto": "Плутон", "Chiron": "Хирон",
            "True Node": "Сев.Узел", "South Node": "Южн.Узел", "Mean Apogee": "Лилит",
            "ASC": "ASC", "MC": "MC", "Vertex": "Вертекс", "Part of Fortune": "Фортуна"
        }

        if isinstance(start_date, str):
            try:
                start_dt = datetime.fromisoformat(start_date)
            except:
                start_dt = datetime.now()
        else:
            start_dt = start_date

        days_data = []
        total_tension = 0.0
        
        for d in range(7):
            day_dt = start_dt + timedelta(days=d)
            dt_str = day_dt.strftime("%Y-%m-%d %H:%M")
            tc = self.create_transit_chart(dt_str, location_str)
            
            # Moon Phase & Sign
            tm = next((p for p in tc.positions if p.name == "Moon"), None)
            ts = next((p for p in tc.positions if p.name == "Sun"), None)
            moon_info = {}
            void_of_course = False
            
            if tm and ts:
                diff = (tm.longitude - ts.longitude) % 360
                phase = "Новолуние" if diff < 15 else "Полнолуние" if 170 < diff < 190 else "Растущая" if diff < 180 else "Убывающая"
                
                sign_idx = int(tm.longitude // 30)
                signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
                # Simple Void check: late degree
                void_of_course = (tm.longitude % 30) > 28
                moon_info = {
                    "phase": phase,
                    "sign": signs[sign_idx],
                    "degree": tm.longitude % 30,
                    "void_of_course": void_of_course
                }

            # Ingresses
            ingresses = []
            prev_dt = day_dt - timedelta(days=1)
            prev_tc = self.create_transit_chart(prev_dt.strftime("%Y-%m-%d %H:%M"), location_str)
            for fp in ["Mercury", "Venus", "Mars", "Sun"]:
                c_p = next((p for p in tc.positions if getattr(p, 'name', '') == fp), None)
                p_p = next((p for p in prev_tc.positions if getattr(p, 'name', '') == fp), None)
                if c_p and p_p:
                    c_sign = int(c_p.longitude // 30)
                    p_sign = int(p_p.longitude // 30)
                    if c_sign != p_sign:
                        signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
                        ingresses.append(f"{RUS_NAMES.get(fp, fp)} -> {signs[c_sign]}")

            # Aspects & Tension Calculation
            aspects = []
            daily_tension = 0.0
            hits = self.find_transit_aspects(natal_chart, tc, orb=1.0)
            
            for da in hits:
                # Only consider aspects to personal points
                if da['natal'] in ["Sun", "Moon", "ASC", "MC", "Venus", "Mars", "Mercury"]:
                    aspects.append({
                        "transit": RUS_NAMES.get(da['transit'], da['transit']),
                        "natal": RUS_NAMES.get(da['natal'], da['natal']),
                        "aspect": da['type']
                    })
                    
                    # Tension scoring
                    t_planet = da['transit']
                    aspect_type = da['type']
                    
                    weight = 0
                    if "Квадрат" in aspect_type or "Оппозиция" in aspect_type:
                        if t_planet in ["Mars", "Saturn", "Pluto", "Uranus"]:
                            weight = 2.0 # Heavy hit
                        else:
                            weight = 1.0
                    elif "Соединение" in aspect_type:
                        if t_planet in ["Mars", "Saturn", "Pluto", "South Node"]:
                            weight = 1.5
                        elif t_planet in ["Jupiter", "Venus", "Sun"]:
                            weight = -1.0 # Bonus
                    elif "Тригон" in aspect_type or "Секстиль" in aspect_type:
                        weight = -0.5 # Mitigation
                        
                    daily_tension += weight

            if void_of_course:
                daily_tension += 0.5

            # Traffic Light Logic
            if daily_tension >= 2.0:
                traffic = "RED"
                traffic_desc = "🔴 Шторм"
            elif daily_tension >= 0.5:
                traffic = "YELLOW"
                traffic_desc = "🟡 Внимание"
            else:
                traffic = "GREEN"
                traffic_desc = "🟢 Зеленый"

            total_tension += daily_tension

            days_data.append({
                "date": day_dt.strftime("%Y-%m-%d"),
                "weekday": day_dt.strftime("%A"),
                "moon": moon_info,
                "ingresses": ingresses,
                "aspects": aspects,
                "traffic_light": traffic,
                "traffic_desc": traffic_desc,
                "tension_score": round(daily_tension, 1)
            })

        # Weekly Summary
        avg_tension = total_tension / 7
        if avg_tension >= 1.5:
            week_traffic = "RED"
        elif avg_tension >= 0.3:
            week_traffic = "YELLOW"
        else:
            week_traffic = "GREEN"

        return {
            "days": days_data, 
            "summary": {
                "traffic_light": week_traffic,
                "avg_tension": round(avg_tension, 1)
            }
        }
    # #END_BLOCK_WEEKLY_DATA

    # #START_BLOCK_MONTHLY_DATA
    def calculate_forecast_month_data(self, natal_chart, start_date, location_str: str) -> Dict[str, Any]:
        """
        # PURPOSE: Calculate key events for a month (transits, lunations, ingresses).
        # INPUT: natal_chart, start_date, location_str.
        # OUTPUT: Dict with monthly overview.
        """
        RUS_NAMES = {
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн", "Uranus": "Уран",
            "Neptune": "Нептун", "Pluto": "Плутон", "Chiron": "Хирон",
            "True Node": "Сев.Узел", "South Node": "Южн.Узел", "Mean Apogee": "Лилит",
            "ASC": "ASC", "MC": "MC", "Vertex": "Вертекс", "Part of Fortune": "Фортуна"
        }
        
        if isinstance(start_date, str):
            try:
                start_dt = datetime.fromisoformat(start_date)
            except:
                start_dt = datetime.now()
        else:
            start_dt = start_date
            
        events = {
            "lunations": [],
            "ingresses": [],
            "major_transits": [],
            "retrogrades": []
        }
        
        # Scan 32 days
        prev_tc = None
        for d in range(32):
            day_dt = start_dt + timedelta(days=d)
            dt_str = day_dt.strftime("%Y-%m-%d %H:%M")
            tc = self.create_transit_chart(dt_str, location_str)
            
            if not prev_tc:
                prev_tc = tc
                continue
                
            # 1. Lunations
            tm = next((p for p in tc.positions if p.name == "Moon"), None)
            ts = next((p for p in tc.positions if p.name == "Sun"), None)
            if tm and ts:
                diff = (tm.longitude - ts.longitude) % 360
                # Check crossing 0 (New) or 180 (Full)
                prev_tm = next((p for p in prev_tc.positions if p.name == "Moon"), None)
                prev_ts = next((p for p in prev_tc.positions if p.name == "Sun"), None)
                
                if prev_tm and prev_ts:
                    prev_diff = (prev_tm.longitude - prev_ts.longitude) % 360
                    
                    if prev_diff > 300 and diff < 50: # Crossing 0
                        sign_idx = int(tm.longitude // 30)
                        signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
                        events["lunations"].append(f"{day_dt.strftime('%d.%m')} Новолуние в {signs[sign_idx]}")
                        
                    if prev_diff < 180 and diff >= 180: # Crossing 180
                        sign_idx = int(tm.longitude // 30)
                        signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
                        events["lunations"].append(f"{day_dt.strftime('%d.%m')} Полнолуние в {signs[sign_idx]}")

            # 2. Ingresses (Sun, Mercury, Venus, Mars, Jupiter)
            for pname in ["Sun", "Mercury", "Venus", "Mars", "Jupiter"]:
                curr_p = next((p for p in tc.positions if p.name == pname), None)
                prev_p = next((p for p in prev_tc.positions if p.name == pname), None)
                
                if curr_p and prev_p:
                    c_sign = int(curr_p.longitude // 30)
                    p_sign = int(prev_p.longitude // 30)
                    if c_sign != p_sign:
                        signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
                        events["ingresses"].append(f"{day_dt.strftime('%d.%m')} {RUS_NAMES.get(pname, pname)} -> {signs[c_sign]}")
                        
            # 3. Retrogrades (Stationary points)
            for pname in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
                curr_p = next((p for p in tc.positions if p.name == pname), None)
                prev_p = next((p for p in prev_tc.positions if p.name == pname), None)
                if curr_p and prev_p:
                    if curr_p.is_retrograde != prev_p.is_retrograde:
                        state = "R (Ретро)" if curr_p.is_retrograde else "D (Директ)"
                        events["retrogrades"].append(f"{day_dt.strftime('%d.%m')} {RUS_NAMES.get(pname, pname)} -> {state}")

            # 4. Aspects (Major only)
            # Scan only once every 3 days to save CPU? Or check tight orbs.
            # Let's check everyday but filter duplicate hits.
            hits = self.find_transit_aspects(natal_chart, tc, orb=1.0)
            for da in hits:
                # Filter: Slow transits to Personal planets
                if da['transit'] in ["Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                    if da['natal'] in ["Sun", "Moon", "Mercury", "Venus", "Mars", "ASC", "MC"]:
                        # avoid duplicates (crude logic: if same aspect not logged recently)
                        # For MVP, just list all hits, LLM will summarize.
                        aspect_str = f"{day_dt.strftime('%d.%m')} {RUS_NAMES.get(da['transit'])} {da['type']} {RUS_NAMES.get(da['natal'])}"
                        if not any(e.endswith(aspect_str.split(' ', 1)[1]) for e in events["major_transits"]):
                             events["major_transits"].append(aspect_str)

            prev_tc = tc
            
        # Month Tension Summary
        tension_score = 0
        for aspect in events["major_transits"]:
            if any(planet in aspect for planet in ["Марс", "Сатурн", "Плутон", "Уран"]) and any(aspect_type in aspect for aspect_type in ["Квадрат", "Оппозиция"]):
                tension_score += 1
        
        status = "GREEN"
        if tension_score >= 2: status = "YELLOW"
        if tension_score >= 4: status = "RED"
        
        events["status"] = status
        events["tension_index"] = tension_score
            
        return events
    # #END_BLOCK_MONTHLY_DATA

    # #START_BLOCK_DECADE_DATA
    def calculate_forecast_decade_data(self, natal_chart, start_year: int, location_str: str) -> Dict[str, Any]:
        """
        # PURPOSE: Calculate long-term transits for 10 years.
        # FOCUS: Jupiter, Saturn, Uranus, Neptune, Pluto.
        """
        RUS_NAMES = {
            "Jupiter": "Юпитер", "Saturn": "Сатурн", "Uranus": "Уран",
            "Neptune": "Нептун", "Pluto": "Плутон",
            "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
            "Mars": "Марс", "ASC": "ASC", "MC": "MC"
        }
        
        slow_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
        personal_points = ["Sun", "Moon", "Mercury", "Venus", "Mars", "ASC", "MC"]
        
        years_data = {}
        
        # Scan with 15-day step to catch slow transits without heavy load
        # Optimization: Just check monthly (1st of each month)
        
        current_hits = {} # key: "Transit Aspect Natal", value: {start, end}
        
        for offset in range(120): # 10 years * 12 months
            month_dt = datetime(start_year, 1, 1) + timedelta(days=offset*30) # Approximate
            dt_str = month_dt.strftime("%Y-%m-%d 12:00")
            
            try:
                tc = self.create_transit_chart(dt_str, location_str)
                hits = self.find_transit_aspects(natal_chart, tc, orb=1.5) # Wider orb for long trends
                
                year_key = month_dt.year
                if year_key not in years_data:
                    years_data[year_key] = set()
                
                for da in hits:
                    if da['transit'] in slow_planets and da['natal'] in personal_points:
                        # Aspect string
                        aspect_name = f"{RUS_NAMES.get(da['transit'])} {da['type']} {RUS_NAMES.get(da['natal'])}"
                        years_data[year_key].add(aspect_name)
            except:
                continue

        # Convert sets to sorted lists
        result = {}
        for y, aspects in years_data.items():
            result[str(y)] = sorted(list(aspects))
            
        return {"years": result}
    # #END_BLOCK_DECADE_DATA
