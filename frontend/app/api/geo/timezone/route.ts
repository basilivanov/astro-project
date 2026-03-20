// ############################################################################
// AI_HEADER: MODULE_GEO_TIMEZONE_PROXY
// ROLE: Proxy GeoNames timezone lookup to backend.
// DEPENDENCIES: backend /api/geo/timezone.
// GRACE_ANCHORS: [PROXY_HANDLER]
// ############################################################################

const serverApiBase =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://backend:8000";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const lat = url.searchParams.get("lat") || "";
  const lon = url.searchParams.get("lon") || "";
  const targetUrl = new URL(`${serverApiBase}/api/geo/timezone`);
  targetUrl.searchParams.set("lat", lat);
  targetUrl.searchParams.set("lon", lon);

  const response = await fetch(targetUrl.toString(), { cache: "no-store" });
  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
