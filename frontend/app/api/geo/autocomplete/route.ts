// ############################################################################
// AI_HEADER: MODULE_GEO_PROXY
// ROLE: Proxy GeoNames autocomplete to backend.
// DEPENDENCIES: backend /api/geo/autocomplete.
// GRACE_ANCHORS: [PROXY_HANDLER]
// ############################################################################

const serverApiBase =
  process.env.INTERNAL_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://backend:8000";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const query = url.searchParams.get("q") || "";
  const limit = url.searchParams.get("limit") || "";
  const targetUrl = new URL(`${serverApiBase}/api/geo/autocomplete`);
  targetUrl.searchParams.set("q", query);
  if (limit) {
    targetUrl.searchParams.set("limit", limit);
  }

  const response = await fetch(targetUrl.toString(), { cache: "no-store" });
  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
