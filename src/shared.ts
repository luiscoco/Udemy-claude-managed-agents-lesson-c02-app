// What both flows report while they run. The CLI prints these lines; the web
// server streams them to the browser as Server-Sent Events.
import { existsSync, readFileSync } from "node:fs";
import type { stockSnapshot } from "./inventory.js";

export type Flow = "manual" | "managed";

export type FlowEvent =
  | { type: "start"; flow: Flow; prompt: string; model: string; sessionId?: string }
  | { type: "step"; text: string } // a protocol step, e.g. "messages.create -> stop_reason=tool_use"
  | { type: "tool"; trigger: string; input: unknown; result: string }
  | { type: "assistant"; text: string }
  | {
      type: "done";
      stats: { label: string; value: string | number }[];
      stock: ReturnType<typeof stockSnapshot>;
      ms: number;
    }
  | { type: "error"; message: string };

export type Emit = (event: FlowEvent) => void;

export const DEFAULT_PROMPT =
  "Please reserve 2 astronaut mugs (SKU-100) and 1 rocket hoodie (SKU-200), then summarize.";

export const MODEL = process.env.CLAUDE_MODEL ?? "claude-opus-5-5";

const IDS_FILE = new URL("../.managed-ids.json", import.meta.url);

// IDs written by `npm run managed:setup`; env vars win if set.
export function loadManagedIds(): { agentId?: string; environmentId?: string } {
  const saved = existsSync(IDS_FILE) ? JSON.parse(readFileSync(IDS_FILE, "utf8")) : {};
  return {
    agentId: process.env.MANAGED_AGENT_ID ?? saved.agentId,
    environmentId: process.env.MANAGED_ENVIRONMENT_ID ?? saved.environmentId,
  };
}
