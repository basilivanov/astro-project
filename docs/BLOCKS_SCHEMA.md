# Report Blocks Schema (JSON)

**Version:** 1.0
**Status:** Draft

The `content` field of `ReportChunk` can store either legacy Markdown (string) or a JSON array of Blocks.
The Frontend `BlockRenderer` distinguishes between them by attempting `JSON.parse()`.

## Base Block Structure
```json
{
  "type": "string",  // header, paragraph, list, table, key_value, callout, rating, divider
  "id": "optional_uuid",
  "source": "optional_string", // e.g. "engine", "llm"
  ... specific fields
}
```

## Block Types

### 1. Header
```json
{
  "type": "header",
  "level": 2, // 1-4
  "text": "Status of the Month"
}
```

### 2. Paragraph
```json
{
  "type": "paragraph",
  "text": "This is a **bold** text." // Supports basic inline markdown (bold, italic)
}
```

### 3. List
```json
{
  "type": "list",
  "ordered": false, // true for 1. 2. 3., false for bullets
  "items": [
    "Item 1",
    "Item 2"
  ]
}
```

### 4. Table
```json
{
  "type": "table",
  "columns": [
    {"header": "Planet", "width": "50%"},
    {"header": "Sign", "align": "center"}
  ],
  "rows": [
    ["Sun", "Aries"],
    ["Moon", "Taurus"]
  ]
}
```

### 5. Key Value (Grid)
Used for data presentation (passport data, quick stats).
```json
{
  "type": "key_value",
  "items": [
    {"key": "Date", "value": "12.04.2023"},
    {"key": "Time", "value": "14:00"}
  ]
}
```

### 6. Callout (Insight/Warning)
```json
{
  "type": "callout",
  "variant": "info", // info, warning, error, success, quote
  "title": "Insight",
  "content": "Mercury retrograde is active."
}
```

### 7. Rating (Score)
```json
{
  "type": "rating",
  "value": 7.5,
  "max": 10,
  "label": "Compatibility Score",
  "icon": "star" // star, heart, battery
}
```

### 8. Divider
```json
{
  "type": "divider"
}
```
