// Local web UI: serves public/index.html and streams each flow's events to the
// browser as Server-Sent Events (GET /api/run?flow=manual|managed&prompt=...).
import Anthropic from "@anthropic-ai/sdk";
import { readFile } from "node:fs/promises";
import { createServer, type ServerResponse } from "node:http";
import { runManaged } from "./flows/managed.js";
import { runManual } from "./flows/manual.js";
import { DEFAULT_PROMPT, MODEL, loadManagedIds, type Emit } from "./shared.js";

const PORT = Number(process.env.PORT ?? 3000);
const client = new Anthropic();
const root = new URL("../", import.meta.url);

async function sendFile(res: ServerResponse, path: string, type: string) {
  res.writeHead(200, { "Content-Type": type });
  res.end(await readFile(new URL(path, root)));
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", "http://localhost");
  try {
    if (url.pathname === "/") return await sendFile(res, "public/index.html", "text/html; charset=utf-8");
    const assets: Record<string, string> = {
      "/guide.html": "text/html; charset=utf-8",
      "/architecture.html": "text/html; charset=utf-8",
      "/style.css": "text/css; charset=utf-8",
      "/lab.css": "text/css; charset=utf-8",
      "/lab.js": "text/javascript; charset=utf-8",
      "/navigation.js": "text/javascript; charset=utf-8",
      "/architecture-manual.svg": "image/svg+xml; charset=utf-8",
      "/architecture-managed.svg": "image/svg+xml; charset=utf-8",
      "/architecture-manual.png": "image/png",
      "/architecture-managed.png": "image/png",
    };
    if (assets[url.pathname]) return await sendFile(res, "public" + url.pathname, assets[url.pathname]);
    if (url.pathname === "/astronaut.png") return await sendFile(res, "public/astronaut.png", "image/png");
    if (url.pathname === "/vendor/marked.js")
      return await sendFile(res, "node_modules/marked/lib/marked.umd.js", "text/javascript; charset=utf-8");

    if (url.pathname === "/api/config") {
      res.writeHead(200, { "Content-Type": "application/json" });
      return res.end(JSON.stringify({ model: MODEL, defaultPrompt: DEFAULT_PROMPT, managedReady: !!loadManagedIds().agentId }));
    }

    if (url.pathname === "/api/run") {
      const flow = url.searchParams.get("flow");
      const prompt = (url.searchParams.get("prompt") ?? "").trim().slice(0, 2000) || DEFAULT_PROMPT;
      res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive" });
      const emit: Emit = (event) => void res.write(`data: ${JSON.stringify(event)}\n\n`);
      try {
        if (flow === "manual") await runManual(client, prompt, emit);
        else if (flow === "managed") await runManaged(client, prompt, emit);
        else emit({ type: "error", message: `Unknown flow "${flow}"` });
      } catch (err) {
        const message =
          err instanceof Anthropic.AuthenticationError
            ? "Invalid API key. Put your real key in .env (not .env.example) and restart the server."
            : err instanceof Anthropic.APIError
              ? `API error ${err.status ?? ""}: ${err.message}`
              : String(err);
        console.error(`[${flow}]`, err);
        emit({ type: "error", message });
      }
      return res.end();
    }

    res.writeHead(404).end("Not found");
  } catch (err) {
    console.error(err);
    if (!res.headersSent) res.writeHead(500);
    res.end("Server error");
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Lesson C02 web UI running at http://127.0.0.1:${PORT}`);
  console.log(`Model: ${MODEL} · Managed agent ready: ${loadManagedIds().agentId ? "yes" : "no (run npm run managed:setup)"}`);
});
