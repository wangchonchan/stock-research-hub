import express from "express";
import { createServer } from "http";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const server = createServer(app);

  const staticPath =
    process.env.NODE_ENV === "production"
      ? path.resolve(__dirname, "public")
      : path.resolve(__dirname, "..", "dist", "public");

  app.use(express.static(staticPath));
  app.use(express.json());

  app.post("/api/stock-research", (req, res) => {
    const { ticker } = req.body;
    if (!ticker) {
      return res.status(400).json({ error: "Ticker is required" });
    }

    // Execute Python script and capture stdout
    const pythonProcess = spawn("python3", ["research_engine.py", ticker]);

    let stdoutData = "";
    let stderrData = "";

    pythonProcess.stdout.on("data", (chunk) => {
      stdoutData += chunk.toString();
    });

    pythonProcess.stderr.on("data", (chunk) => {
      stderrData += chunk.toString();
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        console.error(`Python process exited with code ${code}: ${stderrData}`);
        return res.status(500).json({ error: "Failed to fetch stock data" });
      }

      try {
        // Find the JSON part in stdout (in case there are other print statements)
        const jsonMatch = stdoutData.match(/\{[\s\S]*\}/);
        if (!jsonMatch) {
          throw new Error("No JSON found in output");
        }
        const result = JSON.parse(jsonMatch[0]);
        res.json(result);
      } catch (err) {
        console.error(`Error parsing Python output: ${err}\nRaw output: ${stdoutData}`);
        res.status(500).json({ error: "Invalid data format from research engine" });
      }
    });
  });

  app.get("*", (_req, res) => {
    res.sendFile(path.join(staticPath, "index.html"));
  });

  const port = process.env.PORT || 3000;
  server.listen(port, () => {
    console.log(`Server running on port ${port}`);
  });
}

startServer().catch(console.error);
