// CLI entry for slide 08. The flow itself lives in flows/managed.ts.
import Anthropic from "@anthropic-ai/sdk";
import { printEvent } from "./cli-print.js";
import { runManaged } from "./flows/managed.js";
import { DEFAULT_PROMPT } from "./shared.js";

await runManaged(new Anthropic(), process.argv.slice(2).join(" ") || DEFAULT_PROMPT, printEvent);
