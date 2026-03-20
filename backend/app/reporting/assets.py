# ############################################################################
# AI_HEADER: MODULE_CHART_ASSETS
# ROLE: SVG paths for planetary glyphs and zodiac signs.
# DEPENDENCIES: None.
# GRACE_ANCHORS: [ASSETS_PLANETS, ASSETS_SIGNS]
# ############################################################################

# #START_BLOCK_ASSETS_PLANETS
PLANET_GLYPHS = {
    "Sun": '<circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="1" fill="currentColor"/>',
    "Moon": '<path d="M14 2C9 2 5 6 5 12s4 10 9 10c-3 0-5-4-5-10s2-10 5-10z" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Mercury": '<circle cx="12" cy="9" r="4" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 13v10M8 17h8M8 5a4 4 0 0 1 8 0" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Venus": '<circle cx="12" cy="9" r="5" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 14v9M8 19h8" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Mars": '<circle cx="10" cy="14" r="5" stroke="currentColor" stroke-width="2" fill="none"/><path d="M14 10l7-7M16 3h5v5" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Jupiter": '<path d="M7 19V5h8M7 12h10c3 0 3 7 0 7H14" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Saturn": '<path d="M14 4v16M10 8h8M10 20c-3 0-3-5 0-5h4" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Uranus": '<path d="M12 2v17M8 19h8M8 5v8a4 4 0 0 0 8 0V5" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="21" r="1.5" fill="currentColor"/>',
    "Neptune": '<path d="M12 20V4M8 4v8c0 2 4 2 4 0s4 2 4 0V4M5 18h14" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Pluto": '<circle cx="12" cy="6" r="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M8 9a4 4 0 0 0 8 0M12 9v13M8 18h8" stroke="currentColor" stroke-width="2" fill="none"/>',
    "North Node": '<path d="M7 18a4 4 0 1 1 8 0 4 4 0 1 1 8 0" stroke="currentColor" stroke-width="2" fill="none"/><path d="M11 18a4 4 0 0 0 8 0" stroke="currentColor" stroke-width="2" fill="none"/>',
    "True Node": '<path d="M7 18a4 4 0 1 1 8 0 4 4 0 1 1 8 0" stroke="currentColor" stroke-width="2" fill="none"/><path d="M11 18a4 4 0 0 0 8 0" stroke="currentColor" stroke-width="2" fill="none"/>',
    "South Node": '<path d="M7 6a4 4 0 1 0 8 0 4 4 0 1 0 8 0" stroke="currentColor" stroke-width="2" fill="none"/><path d="M11 6a4 4 0 0 1 8 0" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Chiron": '<circle cx="12" cy="18" r="4" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 14V6M8 10l8-8" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Lilith": '<path d="M14 2C9 2 5 6 5 12s4 10 9 10c-3 0-5-4-5-10s2-10 5-10z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 18v5M9 21h6" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Mean Apogee": '<path d="M14 2C9 2 5 6 5 12s4 10 9 10c-3 0-5-4-5-10s2-10 5-10z" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 18v5M9 21h6" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Selena": '<circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2" fill="none"/><path d="M12 4v2M12 20v2M4 12h2M20 12h2" stroke="currentColor" stroke-width="2"/>',
    "Part of Fortune": '<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path d="M5 5l14 14M5 19L19 5" stroke="currentColor" stroke-width="2"/>',
    "Ceres": '<path d="M12 4a8 8 0 0 0 0 16M12 12h8" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Pallas": '<path d="M12 4l6 8-6 8-6-8z" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Juno": '<path d="M12 4v12M8 8h8M12 16a4 4 0 1 0 0 8 4 4 0 0 0 0-8" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Vesta": '<path d="M8 20V10l4-6 4 6v10M6 20h12" stroke="currentColor" stroke-width="2" fill="none"/>',
}
# #END_BLOCK_ASSETS_PLANETS

# #START_BLOCK_ASSETS_SIGNS
ZODIAC_GLYPHS = {
    "Aries": '<path d="M12 20V8c-4 0-7-2-7-5M12 8c4 0 7-2 7-5" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Taurus": '<circle cx="12" cy="14" r="5" stroke="currentColor" stroke-width="2" fill="none"/><path d="M7 9a5 5 0 0 1 10 0" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Gemini": '<path d="M7 4v16M17 4v16M5 4h14M5 20h14" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Cancer": '<path d="M6 12a6 6 0 0 1 6-6 6 6 0 0 1 6 6M6 12a3 3 0 1 0 0 6 3 3 0 0 0 0-6M18 12a3 3 0 1 1 0-6 3 3 0 0 1 0 6" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Leo": '<circle cx="7" cy="14" r="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M7 11c0-5 5-8 10-2s0 12-5 12" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Virgo": '<path d="M5 6c3 0 3 5 3 5s0-5 3-5 3 5 3 5v7c0 3-4 3-4 0" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Libra": '<path d="M5 18h14M8 14h8M12 14a4 4 0 0 0-4-4M12 14a4 4 0 0 1 4-4" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Scorpio": '<path d="M6 6c3 0 3 5 3 5s0-5 3-5 3 5 3 5v8M15 21l4-4M19 21l-4-4" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Sagittarius": '<path d="M5 12h14M17 7l5 5-5 5M12 5v14" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Capricorn": '<path d="M7 7c0 7 0 7 5 7s5-10 5-10 5 0 5 5-4 5-4 5" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Aquarius": '<path d="M5 8l3 3 3-3 3 3 3-3M5 16l3 3 3-3 3 3 3-3" stroke="currentColor" stroke-width="2" fill="none"/>',
    "Pisces": '<path d="M5 7c5 0 5 10 0 10M19 7c-5 0-5 10 0 10M5 12h14" stroke="currentColor" stroke-width="2" fill="none"/>',
}
# #END_BLOCK_ASSETS_SIGNS
