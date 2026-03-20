from zoneinfo import ZoneInfo
from datetime import datetime

dt = datetime(1980, 10, 30, 19, 50)
z = ZoneInfo("Europe/Moscow")
aware = dt.replace(tzinfo=z)
print(f"Time: {aware}")
print(f"Offset: {aware.utcoffset()}")
