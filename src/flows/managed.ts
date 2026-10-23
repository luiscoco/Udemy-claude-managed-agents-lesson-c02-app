// Slide 08 - C02 · Code 2 · Managed custom tool.
// The session drives iteration; your host only answers the tool request.
import Anthropic from "@anthropic-ai/sdk";
import { reserveStock, resetStock, stockSnapshot } from "../inventory.js";
import { MODEL, loadManagedIds, type Emit } from "../shared.js";

export async function runManaged(client: Anthropic, prompt: string, emit: Emit): Promise<void> {
  const { agentId, environmentId } = loadManagedIds();
  if (!agentId || !environmentId) {
    emit({ type: "error", message: "No managed agent yet. Run `npm run managed:setup` once, then try again." });
    return;
  }

  resetStock();
  const started = Date.now();
  const session = await client.beta.sessions.create({
    agent: agentId,
    environment_id: environmentId,
    title: "Lesson C02 stock reservation",
  });
  const sessionId = session.id;
  emit({ type: "start", flow: "managed", prompt, model: MODEL, sessionId });

  // Stream-first: open the stream before sending the kickoff message.
  const stream = await client.beta.sessions.events.stream(sessionId);
  emit({ type: "step", text: "sessions.events.stream opened" });
  await client.beta.sessions.events.send(sessionId, {
    events: [{ type: "user.message", content: [{ type: "text", text: prompt }] }],
  });
  emit({ type: "step", text: "sent user.message" });

  let stopReason = "unknown";
  loop: for await (const event of stream) {
    switch (event.type) {
      case "agent.message": {
        const text = event.content.flatMap((b) => (b.type === "text" ? [b.text] : [])).join("\n\n");
        if (text) emit({ type: "assistant", text });
        break;
      }

      // Observe the event -> run the same handler -> send back a result.
      case "agent.custom_tool_use": {
        const result = reserveStock(event.input);
        emit({ type: "tool", trigger: "agent.custom_tool_use", input: event.input, result });
        await client.beta.sessions.events.send(sessionId, {
          events: [
            {
              type: "user.custom_tool_result",
              custom_tool_use_id: event.id,
              content: [{ type: "text", text: result }],
            },
          ],
        });
        emit({ type: "step", text: "sent user.custom_tool_result" });
        break;
      }

      case "session.status_idle":
        stopReason = event.stop_reason.type;
        emit({ type: "step", text: `session.status_idle (${stopReason})` });
        // requires_action = the session is waiting on our tool result; keep streaming.
        if (stopReason !== "requires_action") break loop;
        break;

      case "session.status_terminated":
        stopReason = "terminated";
        break loop;

      case "session.error":
        emit({ type: "step", text: `session.error: ${JSON.stringify(event)}` });
        break;
    }
  }

  // The platform retained the full event history - no local messages[] array.
  const history = await client.beta.sessions.events.list(sessionId);
  emit({
    type: "done",
    stats: [
      { label: "events kept by the platform", value: history.data.length },
      { label: "messages kept by your host", value: 0 },
      { label: "session", value: sessionId },
    ],
    stock: stockSnapshot(),
    ms: Date.now() - started,
  });
}
