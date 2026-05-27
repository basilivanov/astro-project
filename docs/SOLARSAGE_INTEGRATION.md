# SolarSage Integration

## Recommended Mode

Run SolarSage as a local REST sidecar, not as MCP and not as an in-process library.

Reasoning:

- our main backend is Python, SolarSage is Go + CGO;
- REST keeps Swiss Ephemeris isolated in a separate container;
- this gives a stable healthcheckable boundary with retries, timeouts and logs;
- MCP is useful for agent tooling, but not as the main runtime integration path.

## Local Placement

- app repo: `/opt/astro-project`
- SolarSage repo: `/opt/solarsage`
- pinned upstream commit: `2cd05d2c0114e657de4f488412fc7675f68a970c`

## Start

```bash
cd /opt/astro-project
docker compose -f docker-compose.yml -f docker-compose.solarsage.yml up -d solarsage-api
```

Before first start, sync Swiss Ephemeris sources/data into `/opt/solarsage`:

```bash
cd /opt/astro-project
./scripts/setup_solarsage.sh
```

## Health

```bash
curl -H "X-API-Key: $SOLARSAGE_API_KEY" http://127.0.0.1:18091/api/v1/health
```

## Suggested Backend Contract

Use SolarSage only for capabilities that are absent or weaker in the current Stellium flow.

Primary candidates:

- Vedic / sidereal:
  - `/api/v1/vedic/dasha`
  - `/api/v1/vedic/ashtakavarga`
  - `/api/v1/vedic/yogas`
  - `/api/v1/chart/sidereal`
  - `/api/v1/chart/divisional`
- traditional:
  - `/api/v1/profection`
  - `/api/v1/firdaria`
  - `/api/v1/lots`
  - `/api/v1/bounds`
  - `/api/v1/planetary-hours`
  - `/api/v1/heliacal`
  - `/api/v1/bonification`
- predictive extensions:
  - `/api/v1/primary-directions`
  - `/api/v1/symbolic-directions`

Keep current Stellium canonical path for:

- base natal chart generation;
- current business day/week flows;
- existing report semantics already wired to project contracts.

## Integration Rules

- add one adapter in backend, not scattered direct calls;
- treat SolarSage as optional enrichment, not a hard dependency for core flows;
- on timeout/error return degraded enrichment, not total report failure;
- log every request/response envelope with correlation ids.

## Why Not MCP

MCP mode here is useful for ad hoc AI-agent usage, but weak as application runtime transport:

- stdio transport is less observable than HTTP;
- harder to supervise from backend services;
- worse fit for retries, health probes and service composition.

## Licensing Note

SolarSage itself is MIT, but it explicitly depends on Swiss Ephemeris data/code, and upstream documents Swiss Ephemeris as AGPL-3.0 or commercial.

Before any production exposure, legal/licensing terms for Swiss Ephemeris must be confirmed for this deployment model.

## Runtime Hardening

Two local hardening rules are applied for this installation:

- Swiss Ephemeris static library is rebuilt with `TLSOFF`, so state is not split per worker thread;
- both `SWISSEPH_EPHE_PATH` and `SE_EPHE_PATH` are set, so Swiss Ephemeris fallback path stays correct even if upstream code falls back to default path resolution.

Also, not only `*.se1` files are synced. Support files such as fixed-star and orbital-text catalogs are copied too.
