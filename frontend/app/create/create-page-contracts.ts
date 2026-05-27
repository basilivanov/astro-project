import {
  CATALOG_GRACE_BLOCKS,
  CATALOG_GRACE_MODULES,
  withCatalogTrace,
} from "../../components/catalog/create-shared";
import type { CatalogEventPayload } from "../../components/catalog/catalog-analytics";

// START_MODULE_CONTRACT: M-CREATE-CHECKOUT-CONTRACTS
// purpose: Centralize strict-GRACE create-page trace helpers and stable semantic labels for split submodules.
// END_MODULE_CONTRACT: M-CREATE-CHECKOUT-CONTRACTS

// START_MODULE_MAP: M-CREATE-CHECKOUT-CONTRACTS
// entrypoints:
//   - CREATE_FLOW_ID
//   - appendQueryParam
//   - makeCreateTrace
// END_MODULE_MAP: M-CREATE-CHECKOUT-CONTRACTS

export const CREATE_FLOW_ID = "FLOW-FORECAST-CATALOG" as const;

export { CATALOG_GRACE_BLOCKS, CATALOG_GRACE_MODULES };

export function appendQueryParam(path: string, key: string, value: string): string {
  const glue = path.includes("?") ? "&" : "?";
  return `${path}${glue}${key}=${encodeURIComponent(value)}`;
}

export function toCreateSemanticBlock(blockId: string): string {
  return `CREATE_PAGE:${blockId}`;
}

export function makeCreateTrace(
  contract: string,
  block: string,
  correlationId: string,
  meta: CatalogEventPayload = {},
) {
  return withCatalogTrace(
    {
      surface: "create",
      flow_id: CREATE_FLOW_ID,
      ...meta,
    },
    {
      module: CATALOG_GRACE_MODULES.createCheckout,
      contract,
      block,
      semantic_block: toCreateSemanticBlock(block),
      correlation_id: correlationId,
    },
  );
}
