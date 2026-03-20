#!/bin/bash
echo "=== UI EVIDENCE ==="
echo ""
echo "--- frontend/app/create/page.tsx (Pack Selector & Ask Form) ---"
grep -nE "HORARY_PACKS|isHorary|selectedPack|handlePay|canAskFree" frontend/app/create/page.tsx | head -n 50
echo ""
echo "--- frontend/app/reports/history/page.tsx (Filters) ---"
grep -nE "setFilter|filteredReports|chips" frontend/app/reports/history/page.tsx | head -n 30
echo ""
echo "--- frontend/components/TrafficLights.tsx (Legend) ---"
grep -nE "Legend|green:|yellow:|red:" frontend/components/TrafficLights.tsx
echo ""
echo "--- frontend/app/profile/edit/page.tsx (Sun Sign) ---"
grep -nE "sun_sign|ZODIAC_SIGNS" frontend/app/profile/edit/page.tsx
