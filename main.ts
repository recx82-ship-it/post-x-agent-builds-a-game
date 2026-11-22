// Copies POST.json from the repository root into the output directory.
// That is all this program does: the house reads the post itself from X.
import { copyFile, mkdir, readFile } from "node:fs/promises";
import { join } from "node:path";

const botDir = process.env.MAKEFUN_BOT_DIR ?? "/bot";
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

const source = join(botDir, "POST.json");
const raw = await readFile(source, "utf8");
const parsed = JSON.parse(raw);
if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
  throw new Error("POST.json must hold a JSON object");
}
if (typeof parsed.url !== "string" || parsed.url.length === 0) {
  throw new Error("POST.json must hold a non-empty url string");
}

await mkdir(outDir, { recursive: true });
await copyFile(source, join(outDir, "POST.json"));
console.log(`Copied POST.json to ${join(outDir, "POST.json")}`);
