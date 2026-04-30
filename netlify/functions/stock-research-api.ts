import { Handler } from "@netlify/functions";
import { spawn } from "child_process";
import path from "path";

export const handler: Handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  try {
    const { ticker } = JSON.parse(event.body || "{}");
    if (!ticker) {
      return { statusCode: 400, body: JSON.stringify({ error: "Ticker is required" }) };
    }

    // In Netlify Functions, the base directory might be different.
    // We need to find where research_engine.py is.
        // In Netlify, the function is bundled. We need to find the script relative to the base.
    // Try multiple possible locations for the script
    const scriptPath = path.resolve(process.cwd(), "research_engine.py");
    console.log(`Attempting to run python script at: ${scriptPath}`);

    return new Promise((resolve) => {
      const pythonProcess = spawn("python3", [scriptPath, ticker]);

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
          resolve({
            statusCode: 500,
            body: JSON.stringify({ error: "Failed to fetch stock data", details: stderrData }),
          });
          return;
        }

        try {
          const jsonMatch = stdoutData.match(/\{[\s\S]*\}/);
          if (!jsonMatch) {
            throw new Error("No JSON found in output");
          }
          resolve({
            statusCode: 200,
            headers: { "Content-Type": "application/json" },
            body: jsonMatch[0],
          });
        } catch (err) {
          console.error(`Error parsing Python output: ${err}\nRaw output: ${stdoutData}`);
          resolve({
            statusCode: 500,
            body: JSON.stringify({ error: "Invalid data format from research engine" }),
          });
        }
      });
    });
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: "Internal Server Error" }),
    };
  }
};
