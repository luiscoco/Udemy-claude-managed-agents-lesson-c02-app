// Terminal output for the CLI scripts: same format as before the web UI existed.
import type { Emit } from "./shared.js";

export const printEvent: Emit = (e) => {
  switch (e.type) {
    case "start":
      if (e.sessionId) console.log(`session ${e.sessionId}`);
      console.log(`user> ${e.prompt}\n`);
      break;
    case "tool": {
      const { sku, quantity } = (e.input ?? {}) as { sku?: string; quantity?: number };
      const r = JSON.parse(e.result);
      console.log(`  [host] reserveStock(${sku}, ${quantity}) -> ${r.ok ? `${r.reservationId}, ${r.remaining} left` : r.error}`);
      break;
    }
    case "assistant":
      console.log(`claude> ${e.text}`);
      break;
    case "done":
      console.log(`\n(${e.stats.map((s) => `${s.label}: ${s.value}`).join(", ")})`);
      break;
    case "error":
      console.error(`error: ${e.message}`);
      process.exitCode = 1;
      break;
  }
};
