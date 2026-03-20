# ############################################################################
# AI_HEADER: MODULE_MARKDOWN_HELPERS
# ROLE: Generate static JSON blocks from chart data.
############################################################################

import json

RU_SIGNS = {
    "Aries": "Овен ♈", "Taurus": "Телец ♉", "Gemini": "Близнецы ♊", "Cancer": "Рак ♋",
    "Leo": "Лев ♌", "Virgo": "Дева ♍", "Libra": "Весы ♎", "Scorpio": "Скорпион ♏",
    "Sagittarius": "Стрелец ♐", "Capricorn": "Козерог ♑", "Aquarius": "Водолей ♒", "Pisces": "Рыбы ♓"
}

RU_PLANETS = {
    "Sun": "☀️ Солнце", "Moon": "🌙 Луна", "Mercury": "☿ Меркурий", "Venus": "♀️ Венера",
    "Mars": "♂️ Марс", "Jupiter": "♃ Юпитер", "Saturn": "♄ Сатурн", "Uranus": "♅ Уран",
    "Neptune": "♆ Нептун", "Pluto": "♇ Плутон", "Chiron": "⚷ Хирон", "Lilith": "⚸ Лилит",
    "Selena": "🌟 Селена", "North Node": "☊ Сев. Узел", "South Node": "☋ Южн. Узел",
    "Mean Apogee": "⚸ Лилит", "True Node": "☊ Сев. Узел", "Part of Fortune": "⊗ Парс Фортуны",
    "ASC": "⬆️ ASC", "MC": "🏔️ MC", "DSC": "⬇️ DSC", "IC": "🏠 IC", "Vertex": "✴️ Вертекс",
    "Ceres": "Церера", "Pallas": "Паллада", "Juno": "Юнона", "Vesta": "Веста"
}

PLANET_MEANINGS = {
    "Солнце": ("Планета", "Ваше 'Я', эго, воля, сознание"),
    "Луна": ("Планета", "Душа, эмоции, подсознание, комфорт"),
    "Меркурий": ("Планета", "Мышление, речь, обучение, контакты"),
    "Венера": ("Планета", "Любовь, красота, деньги, выбор"),
    "Марс": ("Планета", "Действие, энергия, агрессия, страсть"),
    "Юпитер": ("Планета", "Расширение, удача, мудрость, социум"),
    "Сатурн": ("Планета", "Ограничения, дисциплина, карьера, время"),
    "Уран": ("Планета", "Свобода, озарения, реформы, будущее"),
    "Нептун": ("Планета", "Интуиция, мечты, иллюзии, духовность"),
    "Плутон": ("Планета", "Трансформация, власть, кризисы, магия"),
    "Хирон": ("Астероид", "Ключ, парадокс, целительство, двойственность"),
    "Лилит": ("Фиктивная точка", "Искушение, скрытая сила, теневая сторона"),
    "Селена": ("Фиктивная точка", "Светлая карма, защита, ангел-хранитель"),
    "Сев. Узел": ("Фиктивная точка", "Вектор развития, цель жизни"),
    "Южн. Узел": ("Фиктивная точка", "Наработанный опыт, прошлое, база"),
    "Церера": ("Астероид", "Принцип заботы, воспитания, урожай"),
    "Паллада": ("Астероид", "Творческий интеллект, стратегия, мудрость"),
    "Юнона": ("Астероид", "Партнерство, брак, обязательства"),
    "Веста": ("Астероид", "Фокус, преданность делу, внутренний огонь"),
    "Парс Фортуны": ("Фиктивная точка", "Точка удачи и личного счастья"),
    "Вертекс": ("Фиктивная точка", "Точка судьбоносных встреч"),
    "ASC": ("Угловая точка", "Маска, имидж, физическое тело"),
    "MC": ("Угловая точка", "Цель жизни, карьера, статус"),
    "IC": ("Угловая точка", "Корни, дом, семья, опора"),
    "DSC": ("Угловая точка", "Партнеры, враги, зеркало"),
}

RU_ASPECTS = {
    "conjunction": "Соединение (0°)", "opposition": "Оппозиция (180°)",
    "trine": "Трин (120°)", "square": "Квадрат (90°)", "sextile": "Секстиль (60°)"
}

RU_PLANETS_SHORT = {
    "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
    "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн", "Uranus": "Уран",
    "Neptune": "Нептун", "Pluto": "Плутон", "Chiron": "Хирон", "Lilith": "Лилит",
    "Mean Apogee": "Лилит", "North Node": "Сев. Узел", "South Node": "Южн. Узел"
}

PATTERN_NAMES = {
    "Grand Trine": "Большой тригон",
    "T-square": "Т-квадрат",
    "Grand Cross": "Большой крест",
    "Yod": "Йод",
    "Kite": "Кайт",
}

def format_technical_appendix(chart_data: dict) -> str:
    blocks = []
    blocks.append({"type": "header", "level": 2, "text": "Координаты и дома"})

    positions = chart_data.get("positions", [])
    used_names = set()
    if positions:
        columns = [
            {"header": "Планета", "width": "30%"},
            {"header": "Знак", "width": "25%"},
            {"header": "Дом", "width": "15%", "align": "center"},
            {"header": "Градус", "width": "20%", "align": "right", "nowrap": True},
            {"header": "R", "width": "10%", "align": "center"},
        ]
        rows = []
        for p in positions:
            raw_name = p.get("name")
            if raw_name in ["RAMC", "Zero"]:
                continue
            name = RU_PLANETS.get(raw_name, raw_name or "-")
            clean_name = name.split(" ", 1)[-1] if " " in name else name
            used_names.add(clean_name)
            sign = RU_SIGNS.get(p.get("sign"), p.get("sign", "-"))
            house = str(p.get("house", "-"))
            deg = int(p.get("sign_degree") or 0)
            minute = int(((p.get("sign_degree") or 0) - deg) * 60)
            deg_str = f"{deg}°{minute:02d}'"
            retro = "R" if p.get("is_retrograde") else ""
            rows.append([name, sign, house, deg_str, retro])

        blocks.append({"type": "table", "columns": columns, "rows": rows})
        blocks.append({
            "type": "callout",
            "variant": "info",
            "title": "R (Ретроградность)",
            "content": "Планета визуально движется назад. Это период пересборки ее тем.",
        })
    else:
        blocks.append({"type": "paragraph", "text": "Нет данных по координатам планет."})

    if used_names:
        rows = []
        for key in sorted(used_names):
            if key in PLANET_MEANINGS:
                ptype, pdesc = PLANET_MEANINGS[key]
                display_type = "" if ptype == "Планета" else ptype
                rows.append([key, display_type, pdesc])
        if rows:
            blocks.append({"type": "header", "level": 3, "text": "Расшифровка значений"})
            blocks.append({
                "type": "table",
                "columns": [
                    {"header": "Точка", "width": "30%"},
                    {"header": "Тип", "width": "20%"},
                    {"header": "Значение", "width": "50%"},
                ],
                "rows": rows,
            })

    blocks.append({"type": "header", "level": 2, "text": "Аспекты (орбисы)"})
    aspects = chart_data.get("aspects", [])
    if not aspects:
        blocks.append({"type": "paragraph", "text": "Аспекты не найдены."})
    else:
        sorted_aspects = sorted(aspects, key=lambda x: x.get("orb", 99))
        rows = []
        for a in sorted_aspects:
            p1 = RU_PLANETS_SHORT.get(a.get("p1", ""), a.get("p1", ""))
            p2 = RU_PLANETS_SHORT.get(a.get("p2", ""), a.get("p2", ""))
            atype = RU_ASPECTS.get(a.get("type"), a.get("type", ""))
            orb = a.get("orb", "?")
            rows.append([p1, atype, p2, f"{orb}°"])
        blocks.append({
            "type": "table",
            "columns": [
                {"header": "Планета 1", "width": "30%"},
                {"header": "Аспект", "width": "30%"},
                {"header": "Планета 2", "width": "30%"},
                {"header": "Орб", "width": "10%", "align": "right"},
            ],
            "rows": rows,
        })

    patterns = chart_data.get("patterns", [])
    if patterns:
        items = []
        for p in patterns:
            pts = [RU_PLANETS_SHORT.get(x, x) for x in p.get("points", [])]
            pts_str = ", ".join(pts)
            raw_type = p.get("type") or "Конфигурация"
            title = PATTERN_NAMES.get(raw_type, raw_type)
            items.append(f"{title}: {pts_str}" if pts_str else title)
        blocks.append({"type": "header", "level": 2, "text": "Фигуры Джонса и конфигурации"})
        blocks.append({"type": "list", "items": items, "ordered": False})
    else:
        blocks.append({"type": "paragraph", "text": "Конфигурации не найдены."})

    return json.dumps(blocks, ensure_ascii=False)

def format_house_context(chart_data: dict) -> str:
    lines = []
    houses = chart_data.get("houses", [])
    positions = chart_data.get("positions", [])
    
    rulers = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
        "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Pluto",
        "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Uranus", "Pisces": "Neptune"
    }
    
    house_tenants = {i: [] for i in range(1, 13)}
    for p in positions:
        h = p.get("house")
        name = p.get("name")
        if h and isinstance(h, int) and 1 <= h <= 12:
            house_tenants[h].append(name)
            
    for h in houses:
        h_num = h["house"]
        sign = h["sign"]
        ruler_name = rulers.get(sign, "Unknown")
        ruler_pos = next((p for p in positions if p["name"] == ruler_name), None)
        ruler_info = f"{ruler_name}"
        if ruler_pos:
            ruler_info += f" in {ruler_pos['sign']} ({ruler_pos.get('house', '?')} house)"
            
        tenants = ", ".join(house_tenants[h_num]) if house_tenants[h_num] else "Empty"
        lines.append(f"House {h_num}: Cusp in {sign}. Ruler: {ruler_info}. Planets in house: {tenants}.")
        
    return "\n".join(lines)

def get_chart_facts_json(chart_data: dict) -> dict:
    """
    # PURPOSE: Generate a compact structured JSON summary of chart facts for LLM.
    # SCHEMA: facts_v1 (optimized for token count)
    """
    res = {
        "v": "facts_v1",
        "tz": chart_data.get("location", {}).get("timezone", "UTC"),
        "pos": [],
        "houses": [],
        "aspects": [],
        "balance": chart_data.get("balances", {})
    }
    
    # 1. Positions (Essential only)
    essential = {
        "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", 
        "Uranus", "Neptune", "Pluto", "Chiron", "North Node", "True Node",
        "ASC", "MC", "DSC", "IC", "Vertex", "South Node"
    }
    for p in chart_data.get("positions", []):
        if p["name"] not in essential: continue
        res["pos"].append({
            "p": p["name"],
            "s": p["sign"],
            "deg": int(p["sign_degree"]),
            "h": p.get("house"),
            "r": p.get("is_retrograde", False)
        })
        
    # 2. Houses
    for h in chart_data.get("houses", []):
        res["houses"].append({
            "h": h["house"],
            "s": h["sign"],
            "deg": int(h["sign_degree"])
        })
        
    # 3. Aspects (Major only, tight 5.0 orb for context economy)
    for a in chart_data.get("aspects", []):
        if a.get("orb", 99) <= 5.0:
            res["aspects"].append({
                "p1": a["p1"],
                "t": a["type"],
                "p2": a["p2"],
                "o": round(a["orb"], 1)
            })

    # 4. Patterns (compact)
    res["patterns"] = []
    for p in chart_data.get("patterns", []):
        res["patterns"].append({
            "t": p.get("type"),
            "pts": p.get("points", []),
        })
            
    return res

def format_chart_facts(chart_data: dict) -> str:
    """
    # PURPOSE: Generate a compact textual summary of chart facts for LLM context.
    """
    lines = []
    
    # 1. Positions
    positions = chart_data.get("positions", [])
    essential = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron", "North Node", "ASC", "MC"}
    lines.append("### POSITIONS")
    for p in positions:
        if p["name"] not in essential: continue
        retro = "R" if p.get("is_retrograde") else ""
        lines.append(f"- {p['name']}: {p['sign']} {int(p['sign_degree'])}°, H{p.get('house','?')}{retro}")
        
    # 2. Houses
    lines.append("\n### HOUSES")
    for h in chart_data.get("houses", []):
        lines.append(f"- H{h['house']}: {h['sign']} {int(h['sign_degree'])}°")
        
    # 3. Aspects
    aspects = chart_data.get("aspects", [])
    if aspects:
        lines.append("\n### ASPECTS")
        for a in aspects:
            if a.get("orb", 99) <= 4.0: # Even tighter for text
                lines.append(f"- {a['p1']} {a['type']} {a['p2']} ({a['orb']}°)")
                
    return "\n".join(lines)
