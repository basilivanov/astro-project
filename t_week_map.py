import json
from datetime import datetime

from backend.app.services.week_map import build_week_map
from backend.app.models import User

class DummyUser:
    def __init__(self):
        self.full_name = "Test User"
        self.birth_date = "1990-01-01"
        self.birth_time = "08:15"
        self.birth_place = "Moscow"
        self.birth_time_known = True
        self.birth_lat = 55.7558
        self.birth_lon = 37.6176

user = DummyUser()
print(json.dumps(build_week_map(datetime.now(), user), ensure_ascii=False))
