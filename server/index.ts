import express, { type Express } from "express";
import { createServer } from "http";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface ResearchResult {
  ticker?: string;
  company_name?: string;
  price?: {
    current_price?: number;
  };
  diagnostics?: string[];
}

function extractLastJsonObject(output: string): string | null {
  const end = output.lastIndexOf("}");
  if (end === -1) return null;

  for (
    let start = output.lastIndexOf("{", end);
    start !== -1;
    start = output.lastIndexOf("{", start - 1)
  ) {
    const candidate = output.slice(start, end + 1);
    try {
      JSON.parse(candidate);
      return candidate;
    } catch {
      // Keep walking backwards until we find the root JSON object.
    }
  }

  return null;
}

async function setupFrontend(app: Express, staticPath: string) {
  if (process.env.NODE_ENV === "production") {
    app.use(express.static(staticPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(staticPath, "index.html"));
    });
    return;
  }

  const { createServer: createViteServer } = await import("vite");
  const vite = await createViteServer({
    server: { middlewareMode: true },
    appType: "spa",
  });
  app.use(vite.middlewares);
}

async function startServer() {
  const app = express();
  const server = createServer(app);

  // In Docker, the structure is /app/dist/public
  const staticPath = path.resolve(process.cwd(), "dist", "public");
  console.log(`Serving static files from: ${staticPath}`);

  app.use(express.json());

  // Health check endpoint for Hugging Face
  app.get("/health", (_req, res) => {
    res.status(200).send("OK");
  });

  app.post("/api/stock-research", (req, res) => {
    const rawTicker =
      typeof req.body?.ticker === "string" ? req.body.ticker.trim() : "";
    if (!rawTicker) {
      return res.status(400).json({ error: "Ticker is required" });
    }

    const ticker = rawTicker.toUpperCase();
    if (!/^[A-Z0-9][A-Z0-9.-]{0,14}$/.test(ticker)) {
      return res
        .status(400)
        .json({ error: "Ticker contains unsupported characters" });
    }

    // Execute Python script and capture stdout
    const scriptPath = path.resolve(process.cwd(), "research_engine.py");
    console.log(
      `Running python script at: ${scriptPath} for ticker: ${ticker}`
    );
    const pythonProcess = spawn("python3", [scriptPath, ticker], {
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });

    const timeout = setTimeout(() => {
      pythonProcess.kill("SIGTERM");
    }, 45_000);

    let stdoutData = "";
    let stderrData = "";

    pythonProcess.stdout.on("data", chunk => {
      stdoutData += chunk.toString();
    });

    pythonProcess.stderr.on("data", chunk => {
      stderrData += chunk.toString();
    });

    pythonProcess.on("close", (code, signal) => {
      clearTimeout(timeout);

      if (signal === "SIGTERM") {
        console.error(`Python process timed out for ${ticker}: ${stderrData}`);
        return res.status(504).json({
          error: "Stock research timed out",
          details:
            "The upstream finance data request took too long to respond.",
          diagnostics: stderrData ? [stderrData] : [],
        });
      }

      if (code !== 0) {
        console.error(`Python process exited with code ${code}: ${stderrData}`);
        return res.status(500).json({
          error: "Failed to fetch stock data",
          details: stderrData || "Research engine exited without details.",
          code: code,
        });
      }

      try {
        // yfinance and other libraries can write warnings before the JSON payload.
        // Parse the final complete JSON object rather than greedily matching from the first brace.
        const jsonPayload = extractLastJsonObject(stdoutData);
        if (!jsonPayload) {
          throw new Error("No JSON found in output");
        }

        const result = JSON.parse(jsonPayload) as ResearchResult;
        const diagnostics = result.diagnostics ?? [];
        const hasPrice =
          typeof result.price?.current_price === "number" &&
          result.price.current_price > 0;
        const hasProfile = Boolean(
          result.company_name &&
            result.company_name !== "N/A" &&
            result.company_name !== result.ticker
        );
        if (!hasPrice && !hasProfile) {
          console.warn(
            `Research engine returned partial/empty data for ${ticker}: ${diagnostics.join("; ")}`
          );
        }

        // Do not fail the search just because an upstream data provider returned
        // partial data. The UI can still render the report shell and diagnostics,
        // which keeps the core search flow responsive.
        res.json(result);
      } catch (err) {
        console.error(
          `Error parsing Python output: ${err}\nRaw output: ${stdoutData}`
        );
        res.status(500).json({
          error: "Invalid data format from research engine",
          details: err instanceof Error ? err.message : String(err),
        });
      }
    });
  });

  await setupFrontend(app, staticPath);

  const port = process.env.PORT || 3000;
  server.listen(Number(port), "0.0.0.0", () => {
    console.log(`Server running on 0.0.0.0:${port}`);
  });
}

startServer().catch(console.error);
