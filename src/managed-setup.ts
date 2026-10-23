// One-time setup for slide 08: an Environment and an Agent that registers
// reserveStock as a custom tool. Agents are persistent and versioned, so run
// this once and reuse the IDs - never create agents in the request path.
import Anthropic from "@anthropic-ai/sdk";
import { writeFileSync } from "node:fs";
import { RESERVE_STOCK_TOOL } from "./inventory.js";

const client = new Anthropic();

const environment = await client.beta.environments.create({
  name: "lesson-c02-env",
  config: { type: "cloud", networking: { type: "limited" } },
});

const agent = await client.beta.agents.create({
  name: "Lesson C02 Stock Agent",
  model: process.env.CLAUDE_MODEL ?? "claude-opus-5-5",
  system:
    "You are a warehouse assistant. Use the reserveStock tool to reserve products. " +
    "Report each reservation ID, and explain any reservation that failed.",
  // Only the custom tool: the effect lives on our host, not in the sandbox.
  tools: [{ type: "custom", ...RESERVE_STOCK_TOOL }],
});

const ids = { agentId: agent.id, agentVersion: agent.version, environmentId: environment.id };
writeFileSync(".managed-ids.json", JSON.stringify(ids, null, 2));
console.log("Saved .managed-ids.json:", ids);
