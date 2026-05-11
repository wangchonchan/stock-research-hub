import express, { type Express } from "express";
import { createServer } from "http";
import path from "path";
import { spawn } from "child_process";

interface ResearchResult {
  ticker?: string;
  company_name?: string;
  price?: {
    current_price?: number;
  };
  diagnostics?: string[];
}

const PYTHON_BIN = process.env.PYTHON_BIN || process.env.PYTHON || "python3";

function extractLastJsonObject(output: string): string | null {
  const trimmedOutput = output.trimEnd();
  const end = trimmedOutput.lastIndexOf("}");
  if (end === -1) return null;

  // The Python engine can emit warnings before the payload, and the payload is
  // deeply nested. Walking backward from the final brace returns the innermost
  // valid object first, so scan forward and keep the largest valid object that
  // ends at the final brace.
  for (
    let start = trimmedOutput.indexOf("{");
    start !== -1;
    start = trimmedOutput.indexOf("{", start + 1)
  ) {
    const candidate = trimmedOutput.slice(start, end + 1);
    try {
      JSON.parse(candidate);
      return candidate;
    } catch {
      // Keep scanning until we find the root JSON object.
    }
  }

  return null;
}

function isResearchResultPayload(value: unknown): value is ResearchResult {
  if (!value || typeof value !== "object") return false;
  const payload = value as ResearchResult;
  return (
    typeof payload.ticker === "string" &&
    Boolean(payload.ticker) &&
    typeof payload.price?.current_price === "number"
  );
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
    const pythonProcess = spawn(PYTHON_BIN, [scriptPath, ticker], {
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });

    let didRespond = false;
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      pythonProcess.kill("SIGTERM");
    }, 60_000);

    let stdoutData = "";
    let stderrData = "";

    pythonProcess.on("error", err => {
      clearTimeout(timeout);
      if (didRespond) return;
      didRespond = true;
      console.error(
        `Failed to start research engine with ${PYTHON_BIN}: ${err}`
      );
      res.status(500).json({
        error: "Failed to start stock research engine",
        details: err instanceof Error ? err.message : String(err),
        diagnostics: [
          `Configured Python binary: ${PYTHON_BIN}`,
          "Set PYTHON_BIN=/path/to/python if the runtime does not expose python3.",
        ],
      });
    });

    pythonProcess.stdout.on("data", chunk => {
      stdoutData += chunk.toString();
    });

    pythonProcess.stderr.on("data", chunk => {
      stderrData += chunk.toString();
    });

    pythonProcess.on("close", (code, signal) => {
      clearTimeout(timeout);
      if (didRespond) return;

      if (timedOut || signal === "SIGTERM") {
        didRespond = true;
        console.error(`Python process timed out for ${ticker}: ${stderrData}`);
        return res.status(504).json({
          error: "Stock research timed out",
          details:
            "The upstream finance data request took too long to respond.",
          diagnostics: stderrData ? [stderrData] : [],
        });
      }

      if (code !== 0) {
        didRespond = true;
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

        const parsedPayload: unknown = JSON.parse(jsonPayload);
        if (!isResearchResultPayload(parsedPayload)) {
          throw new Error("Research engine returned an incomplete payload");
        }

        const result = parsedPayload;
        const diagnostics = result.diagnostics ?? [];
        const hasPrice =
          typeof result.price?.current_price === "number" &&
          result.price.current_price > 0;
        const hasProfile = Boolean(
          result.company_name &&
            result.company_name !== "N/A" &&
            result.company_name !== result.ticker
        );

        if (!hasPrice) {
          console.error(
            `Research engine did not return a usable live price for ${ticker}: ${diagnostics.join("; ")}`
          );
          didRespond = true;
          return res.status(502).json({
            error: "Live stock data unavailable",
            details:
              "The research engine ran, but none of the configured upstream finance providers returned a usable price.",
            diagnostics: [
              `Ticker: ${ticker}`,
              hasProfile
                ? `Profile resolved as: ${result.company_name}`
                : "Company profile was not resolved.",
              ...diagnostics,
            ],
          });
        }

        didRespond = true;
        res.json(result);
      } catch (err) {
        console.error(
          `Error parsing Python output: ${err}\nRaw output: ${stdoutData}`
        );
        didRespond = true;
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
