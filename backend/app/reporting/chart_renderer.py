# ############################################################################
# AI_HEADER: MODULE_CHART_RENDERER
# ROLE: Generate SVG chart from StelliumEngine data.
# DEPENDENCIES: stellium_engine, backend/app/reporting/assets.py
# GRACE_ANCHORS: [SVG_BUILDER, SVG_LAYERS, SVG_STYLES]
# ############################################################################

import math
from typing import Dict, List, Any

from .assets import PLANET_GLYPHS, ZODIAC_GLYPHS

# #START_BLOCK_SVG_STYLES
# Clean, minimal styles for PDF and Web
CSS_STYLES = """
    .chart-bg { fill: none; }
    .zodiac-ring { fill: none; stroke: #333; stroke-width: 1.5; }
    .house-line { stroke: #666; stroke-width: 1; stroke-dasharray: 4; }
    .aspect-line { stroke-width: 1.5; opacity: 0.7; }
    .aspect-conjunction { stroke: #3b82f6; stroke-dasharray: 3; } /* Blue Dotted */
    .aspect-opposition { stroke: #ef4444; } /* Red */
    .aspect-square { stroke: #ef4444; } /* Red */
    .aspect-trine { stroke: #22c55e; } /* Green */
    .aspect-sextile { stroke: #22c55e; } /* Green */
    .planet-glyph { fill: #000; }
    .sign-glyph { fill: #333; }
    .cusp-label { font-size: 10px; font-family: sans-serif; fill: #666; }
"""
# #END_BLOCK_SVG_STYLES

# #START_BLOCK_SVG_BUILDER
class NatalChartRenderer:
    def __init__(self, size: int = 600):
        self.size = size
        self.center = size / 2
        self.radius = (size / 2) - 40 # Padding
        self.inner_radius = self.radius * 0.7 # Where planets sit
        
    def _pol_to_cart(self, radius, angle_deg):
        # Convert degrees to radians and adjust for SVG coordinate system (0 is East, clockwise? No, standard is counter-clockwise from East)
        # Astronomical: 0 = Aries (East point usually? Or Ascendant?)
        # Let's align 0 degrees (Aries 0) to standard position.
        # But charts usually put Ascendant at 9 o'clock (180 deg in math standard).
        # We need to rotate the chart so ASC is at left (180 deg).
        # We will receive chart rotation offset later.
        
        angle_rad = math.radians(angle_deg)
        # Math: 0 is Right (East), 90 is Bottom (South) in SVG Y-down?
        # SVG Y is down. 
        # 0 deg = (cx + r, cy)
        # 90 deg = (cx, cy + r)
        # We want standard astrological wheel: Counter-clockwise.
        # So we negate angle for SVG if we want CCW.
        x = self.center + radius * math.cos(angle_rad)
        y = self.center - radius * math.sin(angle_rad) # Y goes up visually (minus)
        return x, y

    def render(self, chart_data: Dict[str, Any], aspects: List[Dict]) -> str:
        """
        # PURPOSE: Render SVG string from chart data.
        # INPUT: chart_data (houses, positions), aspects.
        """
        # 1. Determine Rotation (ASC should be at 180 deg / 9 o'clock)
        # Find ASC longitude
        asc_pos = next((p for p in chart_data['houses'] if p['house'] == 1), None)
        asc_lon = asc_pos['longitude'] if asc_pos else 0
        
        # Rotation: We want ASC (asc_lon) to be at 180 degrees (Left)
        # Current pos P: P degrees.
        # Target visual angle V.
        # V = P - asc_lon + 180 ?
        # Example: ASC=0 (Aries). Visual=180. V = 0 - 0 + 180 = 180. Correct.
        # Example: Planet at 10 (Aries 10). V = 10 - 0 + 180 = 190. Correct (just below horizon).
        rotation_offset = 180 - asc_lon

        svg_content = []
        
        # 2. Zodiac Ring
        svg_content.append(self._render_zodiac_ring(rotation_offset))
        
        # 3. Houses
        svg_content.append(self._render_houses(chart_data['houses'], rotation_offset))
        
        # 4. Aspects
        svg_content.append(self._render_aspects(aspects, chart_data['positions'], rotation_offset))
        
        # 5. Planets
        svg_content.append(self._render_planets(chart_data['positions'], rotation_offset))

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.size} {self.size}" width="100%" height="100%">
            <style>{CSS_STYLES}</style>
            <circle cx="{self.center}" cy="{self.center}" r="{self.radius}" class="chart-bg" />
            {''.join(svg_content)}
        </svg>"""

    def _render_zodiac_ring(self, offset):
        # 12 sectors of 30 degrees
        # Signs: Aries (0-30), Taurus (30-60)...
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        elements = []
        # Outer ring
        elements.append(f'<circle cx="{self.center}" cy="{self.center}" r="{self.radius}" class="zodiac-ring"/>')
        elements.append(f'<circle cx="{self.center}" cy="{self.center}" r="{self.radius * 0.85}" class="zodiac-ring"/>')
        
        for i, sign in enumerate(signs):
            start_angle = i * 30 + offset
            # Center of sign
            mid_angle = start_angle + 15
            
            # Line separating signs
            x1, y1 = self._pol_to_cart(self.radius * 0.85, start_angle)
            x2, y2 = self._pol_to_cart(self.radius, start_angle)
            elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="1"/>')
            
            # Glyph
            gx, gy = self._pol_to_cart(self.radius * 0.92, mid_angle)
            glyph = ZODIAC_GLYPHS.get(sign, "")
            # Scale glyph down and position
            elements.append(f'<g transform="translate({gx-10}, {gy-10}) scale(0.8)" class="sign-glyph">{glyph}</g>')
            
        return "".join(elements)

    def _render_houses(self, houses, offset):
        elements = []
        for h in houses:
            angle = h['longitude'] + offset
            # Line from inner radius to center? Or just tick?
            # Standard: Line from zodiac ring inner edge to center?
            # Or simplified: Lines inside the circle.
            x1, y1 = self._pol_to_cart(0, angle) # Center
            x2, y2 = self._pol_to_cart(self.radius * 0.85, angle)
            elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="house-line"/>')
            
            # Label number
            # Position: slightly clockwise from cusp
            mid_angle = angle + 15 # Approx
            lx, ly = self._pol_to_cart(self.inner_radius * 0.6, mid_angle)
            elements.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" class="cusp-label">{h["house"]}</text>')
            
        return "".join(elements)

    def _render_planets(self, positions, offset):
        elements = []
        # Need collision detection/adjustment for planets close together
        # Simple MVP: Just place them.
        for p in positions:
            name = p['name']
            if name not in PLANET_GLYPHS: continue
            
            angle = p['longitude'] + offset
            x, y = self._pol_to_cart(self.inner_radius, angle)
            
            glyph = PLANET_GLYPHS[name]
            # Planet glyphs are usually 24x24 in asset, scale to 20x20
            elements.append(f'<g transform="translate({x-10}, {y-10}) scale(0.8)" class="planet-glyph" title="{name}">{glyph}</g>')
            
            # Tick on the zodiac ring to show precise degree
            tx1, ty1 = self._pol_to_cart(self.radius * 0.85, angle)
            tx2, ty2 = self._pol_to_cart(self.radius * 0.82, angle)
            elements.append(f'<line x1="{tx1}" y1="{ty1}" x2="{tx2}" y2="{ty2}" stroke="#000" stroke-width="1"/>')
            
        return "".join(elements)

    def _render_aspects(self, aspects, positions, offset):
        # Map planet name to coordinate
        pos_map = {}
        for p in positions:
            pos_map[p['name']] = p['longitude']
            
        elements = []
        for asp in aspects:
            p1 = asp['p1']
            p2 = asp['p2']
            atype = asp['type']
            
            if p1 not in pos_map or p2 not in pos_map: continue
            
            lon1 = pos_map[p1] + offset
            lon2 = pos_map[p2] + offset
            
            x1, y1 = self._pol_to_cart(self.inner_radius, lon1)
            x2, y2 = self._pol_to_cart(self.inner_radius, lon2)
            
            cls = f"aspect-line aspect-{atype}"
            elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>')
            
        return "".join(elements)
# #END_BLOCK_SVG_BUILDER

def build_natal_chart_svg(chart_data: Dict[str, Any]) -> str:
    """
    # PURPOSE: Helper to build SVG from chart_data dict.
    # INPUT: chart_data.
    # OUTPUT: SVG string.
    """
    if not chart_data:
        return ""
    
    renderer = NatalChartRenderer()
    aspects = chart_data.get("aspects", [])
    # Filter aspects to major only? Or all?
    # Engine 'aspects' usually contains major ones.
    
    return renderer.render(chart_data, aspects)
