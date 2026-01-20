# ############################################################################
# AI_HEADER: MODULE_PDF_REPORTER
# ROLE: Convert Markdown reports into HTML and PDF.
# DEPENDENCIES: markdown, weasyprint
# GRACE_ANCHORS: [PDF_RENDER]
# ############################################################################

import math
from markdown import markdown as md_to_html
from weasyprint import CSS, HTML

_BASE_CSS = """
@page { size: A4; margin: 18mm; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 12px; color: #1b1b1b; }
h1 { font-size: 20px; margin: 0 0 12px; }
h2 { font-size: 16px; margin: 18px 0 8px; }
h3 { font-size: 14px; margin: 16px 0 6px; }
p { margin: 0 0 10px; line-height: 1.5; }
ul { margin: 0 0 10px 18px; }
code, pre { font-family: "DejaVu Sans Mono", Consolas, monospace; }
pre { background: #f4f4f4; padding: 8px; border-radius: 6px; }
.report-cover { margin-bottom: 18px; }
.report-title { font-size: 22px; font-weight: 700; }
.report-subtitle { font-size: 14px; color: #555; margin-top: 4px; }
.report-meta { margin-top: 8px; font-size: 12px; color: #4b4b4b; display: grid; gap: 2px; }
.chart-wrap { margin: 16px 0 18px; display: flex; justify-content: center; }
.chart-wrap svg { width: 100%; max-width: 520px; height: auto; }
.chart-ring { stroke: #2f2f2f; stroke-width: 1.2; fill: none; }
.chart-ring--inner { stroke: #b9b1a5; stroke-width: 0.8; fill: none; }
.chart-house { stroke: #c9c1b6; stroke-width: 0.7; }
.chart-aspect--soft { stroke: #2e8b57; stroke-width: 0.9; opacity: 0.75; }
.chart-aspect--hard { stroke: #c0392b; stroke-width: 1.1; opacity: 0.75; }
.chart-aspect--neutral { stroke: #6b6b6b; stroke-width: 0.8; opacity: 0.6; }
.chart-planet { fill: #1b1b1b; font-size: 13px; font-weight: 600; }
.chart-dot { fill: #fff; stroke: #1b1b1b; stroke-width: 1; }
"""


def markdown_to_html(markdown_text: str) -> str:
    return md_to_html(
        markdown_text or "",
        extensions=["fenced_code", "tables"],
        output_format="html5",
    )


_PLANET_EMOJI = {
    "Sun": "☀️",
    "Moon": "🌙",
    "Mercury": "☿",
    "Venus": "♀️",
    "Mars": "♂️",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
    "Chiron": "⚷",
    "Lilith": "⚸",
    "Selena": "🌟",
}

_ASPECTS = [
    ("conjunction", 0, 6, "neutral"),
    ("opposition", 180, 6, "hard"),
    ("trine", 120, 6, "soft"),
    ("square", 90, 6, "hard"),
    ("sextile", 60, 6, "soft"),
]


def _angle_from_longitude(longitude: float) -> float:
    return (90 - longitude) % 360


def _polar_to_xy(angle_deg: float, radius: float, center: float) -> tuple[float, float]:
    rad = math.radians(angle_deg)
    x = center + radius * math.cos(rad)
    y = center - radius * math.sin(rad)
    return x, y


from stellium_engine import StelliumEngine


from .chart_renderer import NatalChartRenderer





class MockPos:


    def __init__(self, name, lon):


        self.name = name


        self.longitude = lon





class MockChart:


    def __init__(self, positions):


        self.positions = positions





def build_natal_chart_svg(chart_data: dict) -> str:


    """


    # PURPOSE: Generate SVG for the chart.


    # INPUT: chart_data dict.


    # OUTPUT: SVG string.


    """


    if not chart_data:


        return ""





    try:


        # Reconstruct minimal chart object for aspect calculation


        positions = []


        for p in chart_data.get("positions", []):


            positions.append(MockPos(p["name"], p["longitude"]))


        


        mock_chart = MockChart(positions)


        


        engine = StelliumEngine()


        aspects = engine.find_natal_aspects(mock_chart)


        


        renderer = NatalChartRenderer()


        return renderer.render(chart_data, aspects)


    except Exception as e:


        print(f"SVG Generation Error: {e}")


        return ""


def build_report_html(
    *,
    title: str,
    subtitle: str,
    meta_lines: list[str],
    chart_svg: str,
    body_html: str,
) -> str:
    meta_html = "".join(f"<div>{line}</div>" for line in meta_lines if line)
    chart_block = f'<div class="chart-wrap">{chart_svg}</div>' if chart_svg else ""
    return (
        "<html><head><meta charset=\"utf-8\"></head><body>"
        f'<div class="report-cover"><div class="report-title">{title}</div>'
        f'<div class="report-subtitle">{subtitle}</div>'
        f'<div class="report-meta">{meta_html}</div></div>'
        f"{chart_block}"
        f"{body_html}"
        "</body></html>"
    )


def html_to_pdf(html_text: str) -> bytes:
    html = HTML(string=html_text)
    css = CSS(string=_BASE_CSS)
    return html.write_pdf(stylesheets=[css])
