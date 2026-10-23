// Slide 07 - C02 · Code 1 · Manual tool round trip.
// Your host asks the model, runs the effect, and keeps the history itself.
import Anthropic from "@anthropic-ai/sdk";
import { RESERVE_STOCK_TOOL, reserveStock, resetStock, stockSnapshot } from "../inventory.js";
import { MODEL, type Emit } from "../shared.js";

const tools: Anthropic.Tool[] = [{ ...RESERVE_STOCK_TOOL, strict: true }];

export async function runManual(client: Anthropic, prompt: string, emit: Emit): Promise<void> {
  resetStock();
  const started = Date.now();
  const messages: Anthropic.MessageParam[] = [{ role: "user", content: prompt }];
  emit({ type: "start", flow: "manual", prompt, model: MODEL });

  // The slide shows one iteration; "repeat the model call to continue the loop".
  for (let turn = 1; turn <= 10; turn++) {
    // 1 · Ask the model
    const res = await client.messages.create({ model: MODEL, max_tokens: 16000, tools, messages });
    emit({ type: "step", text: `messages.create #${turn} -> stop_reason=${res.stop_reason}` });

    if (res.stop_reason === "tool_use") {
      const calls = res.content.filter((b): b is Anthropic.ToolUseBlock => b.type === "tool_use");
      if (calls.length === 0) throw new Error("Missing tool call");

      // 2 · Execute the effect for every call (the model may batch several)
      const results: Anthropic.ToolResultBlockParam[] = calls.map((call) => {
        const result = reserveStock(call.input);
        emit({ type: "tool", trigger: "stop_reason: tool_use", input: call.input, result });
        return { type: "tool_result", tool_use_id: call.id, content: result };
      });

      // 3 · Keep the history: assistant call + user result (all results in ONE message)
      messages.push({ role: "assistant", content: res.content });
      messages.push({ role: "user", content: results });
      emit({ type: "step", text: `messages.push(assistant call, user tool_result) -> ${messages.length} messages` });
      continue;
    }

    if (res.stop_reason === "refusal") {
      emit({ type: "error", message: `Claude declined the request (${res.stop_details?.category ?? "no category"}).` });
      return;
    }

    const text = res.content.flatMap((b) => (b.type === "text" ? [b.text] : [])).join("\n\n");
    emit({ type: "assistant", text });
    emit({
      type: "done",
      stats: [
        { label: "model calls", value: turn },
        { label: "messages kept by your host", value: messages.length },
        { label: "final stop_reason", value: res.stop_reason ?? "unknown" },
      ],
      stock: stockSnapshot(),
      ms: Date.now() - started,
    });
    return;
  }
  emit({ type: "error", message: "Stopped after 10 model calls without a final answer." });
}
