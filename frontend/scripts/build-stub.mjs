import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = join(root, "dist", "mi-cole", "browser");

mkdirSync(outDir, { recursive: true });
copyFileSync(join(root, "index.html"), join(outDir, "index.html"));
console.log("Stub SPA → dist/mi-cole/browser/index.html");
