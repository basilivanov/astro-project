# ############################################################################
# AI_HEADER: MODULE_UNIVERSAL_ANALYZER
# ROLE: Interpretative layer for astronomical data. FULL ORIGINAL LOGIC RESTORED.
# DEPENDENCIES: stellium_engine.py
# GRACE_ANCHORS: [NAMES_MAPPING, SIGN_LOGIC, DIGNITY_ENGINE, FORECAST_ORCHESTRATOR,
#                 NATAL_SECTION, STRATEGY_10Y_SECTION, YEAR_TACTIC_SECTION, 
#                 WEEKLY_PLAN_SECTION, MONTH_MODE_SECTION]
# ############################################################################

import sys
from stellium_engine import StelliumEngine
from stellium.engines.houses import WholeSignHouses
from datetime import datetime, timedelta

# #START_BLOCK_NAMES_MAPPING
RUS_NAMES = {
    "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
    "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн", "Uranus": "Уран",
    "Neptune": "Нептун", "Pluto": "Плутон", "Chiron": "Хирон",
    "True Node": "Сев.Узел", "South Node": "Южн.Узел", "Mean Apogee": "Лилит",
    "ASC": "ASC", "MC": "MC", "Vertex": "Вертекс", "Part of Fortune": "Фортуна"
}
# #END_BLOCK_NAMES_MAPPING

# #START_BLOCK_SIGN_LOGIC
def get_sign(lon):
    signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", 
             "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
    return signs[int(lon // 30)]
# #END_BLOCK_SIGN_LOGIC

# #START_BLOCK_DIGNITY_ENGINE
def get_dignity(planet_name, sign_name):
    """
    Возвращает статус силы планеты: Обитель, Экзальтация, Изгнание, Падение.
    """
    dignities = {
        "Sun": {"dom": ["Лев"], "exalt": ["Овен"], "detr": ["Водол"], "fall": ["Весы"]},
        "Moon": {"dom": ["Рак"], "exalt": ["Телец"], "detr": ["Козер"], "fall": ["Скорп"]},
        "Mercury": {"dom": ["Близ", "Дева"], "exalt": ["Дева"], "detr": ["Стрел", "Рыбы"], "fall": ["Рыбы"]},
        "Venus": {"dom": ["Телец", "Весы"], "exalt": ["Рыбы"], "detr": ["Скорп", "Овен"], "fall": ["Дева"]},
        "Mars": {"dom": ["Овен", "Скорп"], "exalt": ["Козер"], "detr": ["Весы", "Телец"], "fall": ["Рак"]},
        "Jupiter": {"dom": ["Стрел", "Рыбы"], "exalt": ["Рак"], "detr": ["Близ", "Дева"], "fall": ["Козер"]},
        "Saturn": {"dom": ["Козер", "Водол"], "exalt": ["Весы"], "detr": ["Рак", "Лев"], "fall": ["Овен"]},
        "Uranus": {"dom": ["Водол"], "exalt": ["Скорп"], "detr": ["Лев"], "fall": ["Телец"]},
        "Neptune": {"dom": ["Рыбы"], "exalt": ["Рак"], "detr": ["Дева"], "fall": ["Козер"]},
        "Pluto": {"dom": ["Скорп"], "exalt": ["Лев"], "detr": ["Телец"], "fall": ["Водол"]},
    }
    p_data = dignities.get(planet_name)
    if not p_data: return ""
    if sign_name in p_data["dom"]: return " [👑 Обитель]"
    if sign_name in p_data["exalt"]: return " [🔥 Экзальтация]"
    if sign_name in p_data["detr"]: return " [☠️ Изгнание]"
    if sign_name in p_data["fall"]: return " [🕳 Падение]"
    return ""
# #END_BLOCK_DIGNITY_ENGINE

# #START_BLOCK_FORECAST_ORCHESTRATOR
def run_universal_forecast(name, birth_date, birth_loc, current_loc=None, target_year=2026, mode="all", target_month=1, is_time_precise=False):
    """
    # PURPOSE: Генерация комплексного астрологического анализа.
    # CONTEXT: Основной оркестратор. Включает проверку точности времени для мидпойнтов.
    """
    if current_loc is None: current_loc = birth_loc
    engine = StelliumEngine()
    print(f"\n🚀 ЗАПУСК КОМПЛЕКСНОГО АНАЛИЗА: {name.upper()}")
    print(f"👤 Рождение: {birth_date} | {birth_loc}")
    print(f"📍 Локация прогноза (Соляр/Транзит): {current_loc}")
    print(f"🎯 Целевой год: {target_year}")
    print("=" * 60)
    
    natal = engine.create_natal_chart(name, birth_date, birth_loc, house_system=WholeSignHouses())
    
    # #START_BLOCK_NATAL_SECTION
    if mode in ["all", "natal"]:
        print("\n🏛  1. ФУНДАМЕНТ (НАТАЛ)")
        for pos in natal.positions:
            n = getattr(pos, 'name', '')
            if n in RUS_NAMES: 
                s = get_sign(pos.longitude)
                dignity_str = get_dignity(n, s)
                print(f"{RUS_NAMES[n]:<10} в {s:<10} ({pos.longitude % 30:.2f}°){dignity_str}")

        try:
            selena_lon = engine.calculate_selena(natal.datetime.julian_day)
            print(f"Селена     в {get_sign(selena_lon):<10} ({selena_lon % 30:.2f}°)")
        except: pass

        print("\n🌪  ДОПОЛНИТЕЛЬНЫЕ ТОЧКИ (Астероиды)")
        for a_name in ["Ceres", "Pallas", "Juno", "Vesta"]:
            pos = next((p for p in natal.positions if getattr(p, 'name', '') == a_name), None)
            if pos: print(f"{a_name:<10} в {get_sign(pos.longitude):<10} ({pos.longitude % 30:.2f}°)")

        print("\n✨ НЕПОДВИЖНЫЕ ЗВЕЗДЫ")
        stars = engine.get_fixed_star_conjunctions(natal, orb=1.0)
        if stars:
            for s in stars: print(f"   ★ {s['star']} соед. {RUS_NAMES.get(s['planet'], s['planet'])} (орб {s['orb']:.2f}°)")
        else: print("   (Нет точных соединений с главными звездами)")

        print("\n📐 1.1. КОНФИГУРАЦИИ АСПЕКТОВ (Фигуры)")
        patterns = engine.find_all_patterns(natal)
        if patterns:
            for p in patterns: print(f"   🔸 {p['type']}: {', '.join([RUS_NAMES.get(x, x) for x in p['points']])}")
        else: print("   (Классических замкнутых фигур не найдено)")

        print("\n🏢 1.2. ДИСПОЗИТОРНАЯ ЛОГИКА (Цепочки)")
        RULERS = {"Овен": "Mars", "Телец": "Venus", "Близ": "Mercury", "Рак": "Moon", "Лев": "Sun", "Дева": "Mercury", "Весы": "Venus", "Скорп": "Pluto", "Стрел": "Jupiter", "Козер": "Saturn", "Водол": "Uranus", "Рыбы": "Neptune"}
        for pos in natal.positions:
            n = getattr(pos, 'name', '')
            if n in RUS_NAMES and n not in ["ASC", "MC", "True Node", "South Node", "Mean Apogee", "Chiron"]:
                s = get_sign(pos.longitude)
                ruler = RULERS.get(s, "?")
                print(f"   {RUS_NAMES[n]} ({s}) -> подчиняется -> {RUS_NAMES.get(ruler, ruler)}")

        print("\n🔥 1.4. СОСТОЯНИЯ (Фазы относительно Солнца)")
        combustion = engine.get_combustion_status(natal)
        if combustion:
            for p_name, status in combustion.items(): print(f"   {RUS_NAMES.get(p_name, p_name):<10}: {status}")
        else: print("   (Нет сожженных планет)")

        print("\n👻 1.5. ТЕНЕВЫЕ СВЯЗИ (Антисы)")
        points = {getattr(p, 'name', ''): p.longitude for p in natal.positions if hasattr(p, 'longitude')}
        for p1_name, p1_lon in points.items():
            if p1_name not in RUS_NAMES: continue
            a, _ = engine.get_antiscia(p1_lon)
            for p2_name, p2_lon in points.items():
                if p1_name != p2_name and p2_name in RUS_NAMES:
                    diff = abs(p2_lon - a)
                    if diff > 180: diff = 360 - diff
                    if diff <= 1.5: print(f"   🎭 {RUS_NAMES[p1_name]} <-> {RUS_NAMES[p2_name]} (через Антис)")

        print("\n🎯 1.6. МИДПОЙНТЫ (Точки баланса)")
        if is_time_precise:
            for pair, lon in engine.get_midpoints(natal).items(): print(f"   {pair:<10}: {get_sign(lon)} ({lon % 30:.2f}°)")
        else:
            print("   ⚠️  ОТКЛЮЧЕНО: Требуется точное время рождения для расчета мидпойнтов.")

        # #START_BLOCK_HOUSE_RELATIONS_SECTION
        print("\n🏠 1.7. СВЯЗИ ДОМОВ (Управители в домах)")
        h_rulers = engine.get_house_rulers(natal)
        for h_num in range(1, 13):
            ruler_name = h_rulers.get(h_num)
            ruler_pos = engine.get_object_data(natal, ruler_name)
            if ruler_pos:
                target_house = engine.get_house_by_lon(natal, ruler_pos.longitude)
                print(f"   🔹 Управитель {h_num}-го дома ({RUS_NAMES.get(ruler_name, ruler_name)}) в {target_house}-м доме")
        # #END_BLOCK_HOUSE_RELATIONS_SECTION
    # #END_BLOCK_NATAL_SECTION

    # #START_BLOCK_STRATEGY_10Y_SECTION
    if mode in ["all", "10years"]:
        print("\n🔭 2. СТРАТЕГИЯ 10 ЛЕТ (Сюжетные линии)")
        narratives = {"⚡️ ЛИЧНОСТЬ И ЦЕЛИ (Я, Карьера, Воля)": [], "💗 ОТНОШЕНИЯ И ДУША (Семья, Чувства, Дом)": [], "💰 ФИНАНСЫ И РЕСУРСЫ (Деньги, Инвестиции)": [], "🌀 СУДЬБА И КАРМА (Узлы, Затмения)": []}
        h_rulers = engine.get_house_rulers(natal)
        for y in range(0, 11):
            curr_y = target_year + y
            transit = engine.create_transit_chart(f"{curr_y}-06-15 12:00", birth_loc) 
            aspects = engine.find_transit_aspects(natal, transit, orb=2.5) 
            for m in aspects:
                if m['transit'] not in ["Pluto", "Neptune", "Uranus", "Saturn", "Jupiter"]: continue
                if m['transit'] == "Jupiter" and m['type'] not in ["Соединение (0°)", "Оппозиция (180°)"]: continue
                event_str = f"[{curr_y}] {RUS_NAMES.get(m['transit'], m['transit'])} {m['type']} {RUS_NAMES.get(m['natal'], m['natal'])}"
                if m['natal'] in ["Sun", "ASC", "MC", "Mars", "North Node"]: narratives["⚡️ ЛИЧНОСТЬ И ЦЕЛИ (Я, Карьера, Воля)"].append(event_str)
                if m['natal'] in ["Moon", "Venus", "DSC", "IC"]: narratives["💗 ОТНОШЕНИЯ И ДУША (Семья, Чувства, Дом)"].append(event_str)
                if m['natal'] in [h_rulers.get(2), h_rulers.get(8), "Jupiter", "Pluto"]: narratives["💰 ФИНАНСЫ И РЕСУРСЫ (Деньги, Инвестиции)"].append(event_str)

            t_node = next((p for p in transit.positions if getattr(p, 'name', '') == 'True Node'), None)
            if t_node:
                n_node_pos = next((p for p in natal.positions if getattr(p, 'name', '') == 'True Node'), None)
                if n_node_pos:
                    d_nodes = abs(t_node.longitude - n_node_pos.longitude)
                    if d_nodes > 180: d_nodes = 360 - d_nodes
                    if d_nodes <= 5.0: narratives["🌀 СУДЬБА И КАРМА (Узлы, Затмения)"].append(f"[{curr_y}] 🔄 Возврат Узлов")
                    elif abs(d_nodes - 180) <= 5.0: narratives["🌀 СУДЬБА И КАРМА (Узлы, Затмения)"].append(f"[{curr_y}] ⚖️ Противофаза Узлов")
                for imp in ["Sun", "Moon", "ASC", "MC"]:
                    imp_pos = next((p for p in natal.positions if getattr(p, 'name', '') == imp), None)
                    if imp_pos:
                        d_imp = abs(t_node.longitude - imp_pos.longitude)
                        if d_imp > 180: d_imp = 360 - d_imp
                        if d_imp <= 5.0: narratives["🌀 СУДЬБА И КАРМА (Узлы, Затмения)"].append(f"[{curr_y}] 🌑 Затмения на точке {RUS_NAMES.get(imp, imp)}")

        for theme, events in narratives.items():
            if events:
                print(f"\n   {theme}:")
                for ev in sorted(list(set(events))): print(f"      {ev}")
            else: print(f"\n   {theme}: Спокойный период")

        print("\n   🌱 ВНУТРЕННИЙ СЕЗОН (Прогрессивная Луна):")
        try:
            def get_prog_moon_sign(target_date):
                age_years = (target_date - natal.datetime.utc_datetime).days / 365.2425
                p_chart = engine.create_transit_chart((natal.datetime.utc_datetime + timedelta(days=age_years)).strftime("%Y-%m-%d %H:%M"), birth_loc)
                m = next((p for p in p_chart.positions if getattr(p, 'name', '') == 'Moon'), None)
                return get_sign(m.longitude) if m else None
            sm, em = get_prog_moon_sign(datetime(target_year, 1, 1)), get_prog_moon_sign(datetime(target_year + 10, 1, 1))
            print(f"      Начало десятилетия: {sm} | Конец десятилетия: {em}")
        except: pass
    # #END_BLOCK_STRATEGY_10Y_SECTION

    # #START_BLOCK_YEAR_TACTIC_SECTION
    if mode in ["all", "year"]:
        print(f"\n📅 3. ТАКТИКА ГОДА ({target_year})")
        birth_dt = natal.datetime.utc_datetime
        age = target_year - birth_dt.year
        prof_house = (age % 12) + 1
        lord_name = engine.get_house_rulers(natal).get(prof_house, "?")
        print(f"   👑 ТАЙМ-ЛОРД ГОДА (Профекция): {RUS_NAMES.get(lord_name, lord_name)} (Дом {prof_house})")

        try:
            solar = engine.create_solar_return(natal, target_year-1, location_str=current_loc, house_system=WholeSignHouses()) 
            print(f"☀️ Соляр: {solar.datetime.local_datetime}")
            asc_pos = next((p for p in solar.positions if p.name == "ASC"), None)
            if asc_pos: print(f"🔑 Асцендент года: {get_sign(asc_pos.longitude)}")
        except: pass

        print(f"\n🏹 ДИРЕКЦИИ (Solar Arcs) на {target_year}:")
        try:
            arc_data = engine.calculate_solar_arc_directions(natal, datetime(target_year, 6, 15))
            for d_name, d_lon in arc_data.get("positions", {}).items():
                if d_name not in RUS_NAMES and d_name not in ["ASC", "MC"]: continue
                for n_pos in natal.positions:
                    n_n = getattr(n_pos, 'name', '')
                    if n_n in RUS_NAMES or n_n in ["ASC", "MC"]:
                        diff = abs(d_lon - n_pos.longitude)
                        if diff > 180: diff = 360 - diff
                        if diff <= 1.0: print(f"   🔥 {d_name} -> {n_n} (орб {diff:.2f}°)")
        except: pass

        print(f"\n🌱 ПРОГРЕССИИ (Внутренний сезон):")
        try:
            prog_chart = engine.create_transit_chart((birth_dt + timedelta(days=age)).strftime("%Y-%m-%d %H:%M"), birth_loc)
            p_moon = next((p for p in prog_chart.positions if getattr(p, 'name', '') == 'Moon'), None)
            if p_moon:
                h_num = engine.get_house_by_lon(natal, p_moon.longitude)
                print(f"   🌙 Прогр. Луна: {get_sign(p_moon.longitude)} ({p_moon.longitude % 30:.2f}°), {h_num}-й дом")
        except: pass

        retro_tracker = {"Mercury": [], "Venus": [], "Mars": []}
        for m in range(1, 13):
            t_chart = engine.create_transit_chart(f"{target_year}-{m:02d}-15 12:00", current_loc)
            for rp in retro_tracker:
                p_pos = next((p for p in t_chart.positions if getattr(p, 'name', '') == rp), None)
                if p_pos: retro_tracker[rp].append(get_sign(p_pos.longitude))
            
            hits = engine.find_transit_aspects(natal, t_chart, orb=1.5)
            for h in hits:
                if h['natal'] in ["Sun", "Moon", "ASC", "MC"] or h['natal'] == lord_name or h['transit'] in ["Mars", "Jupiter", "Saturn"]:
                    prefix = "      🔥" if h['natal'] in ["Sun", "Moon", "ASC", "MC"] else "      📌"
                    print(f"   🗓 Месяц {m}: {prefix} {RUS_NAMES.get(h['transit'], h['transit'])} {h['type']} {RUS_NAMES.get(h['natal'], h['natal'])}")

        print("\n   🔄 РЕТРОГРАДНЫЕ ПЕТЛИ ГОДА:")
        from itertools import groupby
        for p, signs in retro_tracker.items():
            for k, g in groupby(signs):
                duration = len(list(g))
                if duration >= 3: print(f"      ⚠️ {RUS_NAMES.get(p, p)} застревает в знаке {k} на {duration} мес.")
    # #END_BLOCK_YEAR_TACTIC_SECTION

    # #START_BLOCK_WEEKLY_PLAN_SECTION
    if mode in ["all", "week"]:
        print(f"\n📆 4. ПЛАН НА НЕДЕЛЮ")
        now = datetime.now()
        for d in range(7):
            day_dt = now + timedelta(days=d)
            tc = engine.create_transit_chart(day_dt.strftime("%Y-%m-%d %H:%M"), current_loc)
            tm, ts = next((p for p in tc.positions if p.name == "Moon"), None), next((p for p in tc.positions if p.name == "Sun"), None)
            if tm and ts:
                diff = (tm.longitude - ts.longitude) % 360
                phase = "Новолуние" if diff < 15 else "Полнолуние" if 170 < diff < 190 else "Растущая" if diff < 180 else "Убывающая"
                voc = " ⚠️ Луна на выходе" if (tm.longitude % 30) > 25 else ""
                print(f"   📎 {day_dt.strftime('%A (%d.%m)')}: Луна в {get_sign(tm.longitude)} ({phase}){voc}")
            
            prev_tc = engine.create_transit_chart((day_dt - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), current_loc)
            for fp in ["Mercury", "Venus", "Mars"]:
                c_p, p_p = next((p for p in tc.positions if getattr(p, 'name', '') == fp), None), next((p for p in prev_tc.positions if getattr(p, 'name', '') == fp), None)
                if c_p and p_p and get_sign(c_p.longitude) != get_sign(p_p.longitude):
                    print(f"      🔄 {RUS_NAMES.get(fp, fp)} переходит в {get_sign(c_p.longitude)}")
            
            for da in engine.find_transit_aspects(natal, tc, orb=1.0):
                if da['natal'] in ["Sun", "Moon", "ASC", "MC"]:
                    print(f"      👉 {RUS_NAMES.get(da['transit'], da['transit'])} {da['type']} {RUS_NAMES.get(da['natal'], da['natal'])}")
    # #END_BLOCK_WEEKLY_PLAN_SECTION

    # #START_BLOCK_MONTH_MODE_SECTION
    if mode == "month":
        print(f"\n📊 АСТРОЛОГИЧЕСКИЙ ОТЧЕТ: {target_month:02d}.{target_year}")
        t_chart = engine.create_transit_chart(f"{target_year}-{target_month:02d}-15 12:00", current_loc)
        hits = engine.find_transit_aspects(natal, t_chart, orb=2.0)
        tension = sum(1 for h in hits if h['transit'] in ["Saturn", "Pluto", "Mars"] and h['type'] in ["Квадрат (90°)", "Оппозиция (180°)"])
        print(f"СТАТУС: {'🔴 КРАСНЫЙ' if tension >= 4 else '🟡 ЖЕЛТЫЙ' if tension >= 2 else '🟢 ЗЕЛЕНЫЙ'} (Индекс: {tension})")
        t_sun = next(p for p in t_chart.positions if p.name == "Sun")
        print(f"ФОКУС: {engine.get_house_by_lon(natal, t_sun.longitude)}-й дом")
        
        print("ГЛАВНЫЕ АКТИВАТОРЫ:")
        important = [h for h in hits if h['transit'] in ["Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "True Node"] and h['natal'] in ["Sun", "Moon", "Mercury", "Venus", "Mars", "ASC", "MC"]]
        for i, h in enumerate(sorted(important, key=lambda x: x['exact_diff'])[:5]):
            print(f"   {i+1}. {h['transit']} {h['type']} {h['natal']} ({h['exact_diff']:.2f}°)")
    # #END_BLOCK_MONTH_MODE_SECTION

if __name__ == "__main__":
    run_universal_forecast("Vasily", "1980-10-30 19:50", "Monchegorsk, Russia", current_loc="Sochi, Russia", target_year=2026, mode="all")
# #END_BLOCK_FORECAST_ORCHESTRATOR