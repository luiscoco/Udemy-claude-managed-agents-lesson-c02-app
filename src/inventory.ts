// The host-side effect shared by both slides. It runs on YOUR machine in both
// flows: only who drives the iteration changes.

export const RESERVE_STOCK_TOOL = {
  name: "reserveStock",
  description:
    "Reserve units of a product in the warehouse. Returns the reservation or an error " +
    "explaining why it could not be made (unknown SKU, not enough stock).",
  input_schema: {
    type: "object" as const,
    properties: {
      sku: { type: "string", description: "Product SKU, e.g. SKU-100" },
      // No `minimum`: strict tools reject it. reserveStock enforces >= 1 instead.
      quantity: { type: "integer", description: "Units to reserve (1 or more)" },
    },
    required: ["sku", "quantity"],
    additionalProperties: false,
  },
};

const INITIAL_STOCK: Record<string, { name: string; available: number }> = {
  "SKU-100": { name: "Astronaut mug", available: 12 },
  "SKU-200": { name: "Rocket hoodie", available: 3 },
  "SKU-300": { name: "Moon lamp", available: 0 },
};

let stock = structuredClone(INITIAL_STOCK);
let nextReservation = 1;

// Each demo run starts from the same warehouse, so the two flows are comparable.
export function resetStock(): void {
  stock = structuredClone(INITIAL_STOCK);
  nextReservation = 1;
}

export function stockSnapshot(): { sku: string; name: string; initial: number; available: number }[] {
  return Object.entries(stock).map(([sku, item]) => ({
    sku,
    name: item.name,
    initial: INITIAL_STOCK[sku].available,
    available: item.available,
  }));
}

// "Checked" handler: the model's input is untrusted, so validate before acting.
export function reserveStock(input: unknown): string {
  const { sku, quantity } = (input ?? {}) as { sku?: unknown; quantity?: unknown };
  if (typeof sku !== "string" || !Number.isInteger(quantity) || (quantity as number) < 1) {
    return JSON.stringify({ ok: false, error: "Invalid input: need { sku: string, quantity: integer >= 1 }" });
  }
  const item = stock[sku];
  if (!item) {
    return JSON.stringify({ ok: false, error: `Unknown SKU ${sku}`, knownSkus: Object.keys(stock) });
  }
  const qty = quantity as number;
  if (item.available < qty) {
    return JSON.stringify({ ok: false, error: `Only ${item.available} of ${sku} available` });
  }
  item.available -= qty;
  const reservationId = `RES-${String(nextReservation++).padStart(4, "0")}`;
  return JSON.stringify({ ok: true, reservationId, sku, name: item.name, quantity: qty, remaining: item.available });
}
