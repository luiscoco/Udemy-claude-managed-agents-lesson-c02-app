// CLI entry for slide 07. The flow itself lives in flows/manual.ts.
import Anthropic from "@anthropic-ai/sdk";
import { printEvent } from "./cli-print.js";
import { runManual } from "./flows/manual.js";
import { DEFAULT_PROMPT } from "./shared.js";

await runManual(new Anthropic(), process.argv.slice(2).join(" ") || DEFAULT_PROMPT, printEvent);
