import sys
from datetime import datetime
from stellium_engine import StelliumEngine
from stellium.engines.houses import WholeSignHouses

def run_horary(question="Вопрос", location="Sochi, Russia", querent_house=1, quesited_house=7):
    """
    querent_house: Дом кверента (обычно 1)
    quesited_house: Дом квезита (7 - партнер/клиент, 10 - работа, 9 - поездка/учеба, 2 - деньги)
    """
    engine = StelliumEngine()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M")
    
    print(f"\n🔮 ХОРАРНЫЙ ВОПРОС: {question}")
    print(f"📍 {location} | 🕒 {date_str}")
    print("=" * 60)
    
    # Строим карту
    # Используем Regiomontanus или Placidus для хораров обычно, но Stellium лучше работает с WholeSign/Placidus.
    # Оставим Placidus (по умолчанию в create_transit_chart), так как дома важны.
    chart = engine.create_transit_chart(date_str, location)
    
    # Получаем куспиды домов
    hc = chart.get_houses()
    cusps = hc.cusps
    
    def get_sign(lon):
        signs = ["Овен", "Телец", "Близ", "Рак", "Лев", "Дева", 
                 "Весы", "Скорп", "Стрел", "Козер", "Водол", "Рыбы"]
        return signs[int(lon // 30)]

    def get_ruler_septener(sign_name):
        # Классическое управление (Септенер) для хораров
        rulers = {
            "Овен": "Mars", "Телец": "Venus", "Близ": "Mercury", "Рак": "Moon",
            "Лев": "Sun", "Дева": "Mercury", "Весы": "Venus", "Скорп": "Mars",
            "Стрел": "Jupiter", "Козер": "Saturn", "Водол": "Saturn", "Рыбы": "Jupiter"
        }
        return rulers.get(sign_name, "Unknown")

    # Определение сигнификаторов
    asc_lon = cusps[0]
    quesited_lon = cusps[quesited_house - 1]
    
    asc_sign = get_sign(asc_lon)
    quesited_sign = get_sign(quesited_lon)
    
    ruler_1 = get_ruler_septener(asc_sign)
    ruler_Q = get_ruler_septener(quesited_sign)
    
    print(f"🏠 1 Дом (Кверент): {asc_sign:<10} -> Управитель: {ruler_1}")
    print(f"🎯 {quesited_house} Дом (Вопрос):  {quesited_sign:<10} -> Управитель: {ruler_Q}")
    
    # Координаты
    positions = {getattr(p, 'name', ''): p.longitude for p in chart.positions}
    
    p1_lon = positions.get(ruler_1, 0)
    pQ_lon = positions.get(ruler_Q, 0)
    moon_lon = positions.get("Moon", 0)
    
    print(f"\n📊 ПОЛОЖЕНИЕ:")
    print(f"👤 {ruler_1}: {get_sign(p1_lon)} ({p1_lon % 30:.2f}°)")
    print(f"❓ {ruler_Q}: {get_sign(pQ_lon)} ({pQ_lon % 30:.2f}°)")
    print(f"🌙 Луна: {get_sign(moon_lon)} ({moon_lon % 30:.2f}°)")
    
    # Аспекты
    print(f"\n🔍 АСПЕКТЫ (Орбис 8°):")
    
    def check_aspect(n1, l1, n2, l2):
        diff = abs(l1 - l2)
        if diff > 180: diff = 360 - diff
        
        asp_name = None
        if diff < 10: asp_name = "Соединение (0°)"
        elif abs(diff - 60) < 8: asp_name = "Секстиль (60°)"
        elif abs(diff - 90) < 8: asp_name = "Квадрат (90°)"
        elif abs(diff - 120) < 8: asp_name = "Тригон (120°)"
        elif abs(diff - 180) < 8: asp_name = "Оппозиция (180°)"
        
        if asp_name:
            print(f"   👉 {n1} - {n2}: {asp_name} (Точность: {abs(diff - (0 if 'Соед' in asp_name else 60 if 'Секс' in asp_name else 90 if 'Квад' in asp_name else 120 if 'Триг' in asp_name else 180)):.1f}°)")
            return True
        return False

    found = check_aspect(ruler_1, p1_lon, ruler_Q, pQ_lon)
    if not found:
        print(f"   Нет мажорного аспекта между {ruler_1} и {ruler_Q}")
        
    print("\n🌙 Аспекты Луны (Ход дела):")
    check_aspect("Moon", moon_lon, ruler_Q, pQ_lon)
    check_aspect("Moon", moon_lon, ruler_1, p1_lon)

if __name__ == "__main__":
    # Пример использования из командной строки
    # python universal_horary.py "Вопрос" 7
    q = "Тестовый вопрос"
    h = 7
    if len(sys.argv) > 1:
        q = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            h = int(sys.argv[2])
        except:
            pass
            
    run_horary(q, quesited_house=h)
