const fs = require("node:fs");
const path = require("node:path");

const root = __dirname;
const out = path.join(root, "dist");
const apiBase = process.env.API_BASE_URL || "http://localhost:8000";
const normalizedApiBase = apiBase.endsWith("/") ? apiBase.slice(0, -1) : apiBase;
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
for (const file of ["index.html", "style.css", "app.js", "vercel.json"]) {
  fs.copyFileSync(path.join(root, file), path.join(out, file));
}
fs.writeFileSync(
  path.join(out, "config.js"),
  "window.API_BASE_URL = " + JSON.stringify(normalizedApiBase) + ";\n",
  "utf8"
);
console.log("Built frontend for API:", normalizedApiBase);
