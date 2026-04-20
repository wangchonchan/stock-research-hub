import express from "express";
import { createServer } from "http";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const server = createServer(app);

  // Serve static files from dist/public in production
  const staticPath =
    process.env.NODE_ENV === "production"
      ? path.resolve(__dirname, "public")
      : path.resolve(__dirname, "..", "dist", "public");

  app.use(express.static(staticPath));
  app.use(express.json());

  // API Route to fetch stock data using Python script
  app.post("/api/stock-research", async (req, res) => {
    const { ticker } = req.body;
    if (!ticker) {
      return res.status(400).json({ error: "Ticker is required" });
    }

    const { spawn } = await import("child_process");
    const pythonProcess = spawn("python3", ["research_engine.py", ticker]);

    let data = "";
    let error = "";

    pythonProcess.stdout.on("data", (chunk) => {
      data += chunk.toString();
    });

    pythonProcess.stderr.on("data", (chunk) => {
      error += chunk.toString();
    });

    pythonProcess.on("close", async (code) => {
      if (code !== 0) {
        console.error(`Python process exited with code ${code}: ${error}`);
        return res.status(500).json({ error: "Failed to fetch stock data" });
      }

      // Read the generated JSON file
      const fs = await import("fs/promises");
      const filePath = path.join(process.cwd(), `research_data_${ticker.toUpperCase()}.json`);
      
      fs.readFile(filePath, "utf-8")
        .then((content) => {
          res.json(JSON.parse(content));
        })
        .catch((err) => {
          console.error(`Error reading JSON file: ${err}`);
          res.status(500).json({ error: "Data file not found" });
        });
    });
  });

  // Handle client-side routing - serve index.html for all routes
  app.get("*", (_req, res) => {
    res.sendFile(path.join(staticPath, "index.html"));
  });

  const port = process.env.PORT || 3000;

  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });
}

startServer().catch(console.error);
