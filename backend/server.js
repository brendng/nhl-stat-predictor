const express = require("express");
const { spawn } = require("child_process");
const cors = require("cors");
const path = require("path");
const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.send("NHL predictor backend running :)");
});

app.get("/predict/:playerId", (req, res) => {
  const playerId = req.params.playerId;

  // locate python script in project root
  const projectRoot = path.resolve(__dirname, "..");
  const scriptPath = path.join(projectRoot, "predict.py");
  const pythonCmd = process.env.PYTHON || "python";

  const py = spawn(pythonCmd, [scriptPath, playerId], { cwd: projectRoot });

  let stdout = "";
  let stderr = "";

  py.stdout.on("data", (data) => {
    stdout += data.toString();
  });

  py.stderr.on("data", (data) => {
    stderr += data.toString();
    console.error("python stderr:", data.toString());
  });

  py.on("close", (code) => {
    if (code !== 0) {
      console.error("python exited with code", code, "stderr:", stderr);
      return res.status(500).json({ error: "prediction process failed", code, stderr });
    }

    stdout = stdout.trim();

    // try to get JSON from stdout, if the script prints logs, try to get final JSON object
    try {
      const parsed = JSON.parse(stdout);
      return res.json(parsed);
    } catch (e) {
      // fallback: extract last JSON type object in output
      const match = stdout.match(/\{[\s\S]*\}$/);
      if (match) {
        try {
          return res.json(JSON.parse(match[0]));
        } catch (err) {
          /* error fall through */
        }
      }
      console.error("failed to parse python output:", stdout);
      return res.status(500).json({ error: "invalid python output", stdout, stderr });
    }
  });
});

app.listen(PORT, () => {
  console.log(`Backend on http://localhost:${PORT}`);
});