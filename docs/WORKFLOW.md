# Workflow Example

## Request

```bash
curl -X POST http://localhost:8000/api/workflows/report \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Demo Client",
    "birth_date": "1990-01-15 12:00",
    "birth_location": "Sochi, Russia",
    "report_type": "natal_master"
  }'
```

## Async Request (UI friendly)

```bash
curl -X POST http://localhost:8000/api/workflows/report/async \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Demo Client",
    "birth_date": "1990-01-15 12:00",
    "birth_location": "Sochi, Russia",
    "report_type": "natal_master"
  }'
```

## Async Response (shape)

```json
{
  "report_id": "uuid",
  "client_id": "uuid",
  "status": "in_progress"
}
```

Check progress via `/api/admin/reports/{id}`.

## Response (shape)

```json
{
  "report_id": "uuid",
  "client_id": "uuid",
  "markdown": "# Report: natal_master\n\n## Core Profile\n\n...",
  "sections": [
    {
      "section_id": "core",
      "title": "Core Profile",
      "content": "..."
    }
  ],
  "chart": {
    "chart_type": "natal",
    "name": "Demo Client",
    "datetime_utc": "1990-01-15T12:00:00+00:00",
    "datetime_local": "1990-01-15T12:00:00+00:00",
    "location": {
      "name": "Sochi, Russia",
      "latitude": 43.6028,
      "longitude": 39.7342,
      "timezone": "Europe/Moscow"
    },
    "house_system": "Placidus",
    "houses": [
      {
        "house": 1,
        "longitude": 0.0,
        "sign": "Aries",
        "sign_degree": 0.0
      }
    ],
    "positions": [
      {
        "name": "Sun",
        "longitude": 0.0,
        "latitude": 0.0,
        "sign": "Aries",
        "sign_degree": 0.0,
        "is_retrograde": false
      }
    ],
    "fixed_stars": []
  }
}
```
