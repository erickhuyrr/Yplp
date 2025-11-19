import express from "express";
import { exec } from "child_process";
import { join } from "path";
import tmp from "tmp";
import fs from "fs";

const app = express();
app.use(express.json());

// Health check
app.get("/", (req, res) => res.json({ message: "yt-dlp API is running" }));

// Download endpoint
app.get("/download", async (req, res) => {
  const { url, format } = req.query;

  if (!url) return res.status(400).json({ error: "URL is required" });

  // Create temporary folder for this download
  const tempDir = tmp.dirSync({ unsafeCleanup: true });
  const outputPath = join(tempDir.name, "%(title)s.%(ext)s");

  let cmd = `yt-dlp -f bestaudio --no-progress --output "${outputPath}" "${url}"`;

  // If user wants mp3
  if (format === "mp3") {
    cmd = `yt-dlp -f bestaudio --extract-audio --audio-format mp3 --audio-quality 0 --no-progress --output "${outputPath}" "${url}"`;
  }

  exec(cmd, (error, stdout, stderr) => {
    if (error) {
      tempDir.removeCallback(); // cleanup temp
      return res.status(500).json({ error: stderr || error.message });
    }

    // Get downloaded file (first file in folder)
    const files = fs.readdirSync(tempDir.name);
    if (files.length === 0) {
      tempDir.removeCallback();
      return res.status(500).json({ error: "File not found after download" });
    }

    const filePath = join(tempDir.name, files[0]);
    const fileName = files[0];

    // Send file directly
    res.download(filePath, fileName, (err) => {
      tempDir.removeCallback(); // cleanup after sending
      if (err) console.error("Error sending file:", err);
    });
  });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
