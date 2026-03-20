# Synastry / Solar Create Cleanup

## Scope

Нarrow pass only for B2C `/create` and `/api/reports/create` around `synastry` and `solar_return`.

## Fixed

- `synastry` user create-flow now collects and sends:
  - `partner_birth_date`
  - `partner_birth_location`
  - `partner_name` as optional display field
- B2C backend now rejects `synastry` creation early if partner birth date/time or place is missing.
- `solar_return` user create-flow now exposes one honest field:
  - `solar_current_location`
- `solar_return` backend now uses:
  - explicit `solar_current_location` for the solar chart when provided;
  - active personal year logic instead of blind `now.year`.
- B2C create now forwards `birth_time_known` from the user profile into workflow payload.

## Intentional Non-Goals

- No changes to admin workflow form.
- No changes to catalog pricing/subscription semantics.
- No `solar_next_*` field in B2C flow, because current runtime does not actually use it for `solar_return`.
- No partner "unknown birth time" mode for `synastry` in this pass.

## Residual Risks

- `synastry` still depends on exact partner birth time for house-level precision; without exact time, a softer fallback mode still needs product/design work.
- `solar_return` now uses one explicit location and already participates in the flagged `/create` -> `/billing/complete` -> `/read` bridge, but default catalog/storefront semantics still stay subscription-first when bridge flags are off.
- Existing admin grant/product aliases like `solar_return_master` / `synastry_master` were not normalized here.
