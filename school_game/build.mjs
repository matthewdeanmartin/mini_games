// Builds the game into ../docs/school_game so it publishes with GitHub Pages.
import * as esbuild from "esbuild";
import { cpSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = join(here, "..", "docs", "school_game");
const assetsOut = join(outDir, "assets");

mkdirSync(assetsOut, { recursive: true });

// Copy assets with URL-friendly names (originals keep the artist's names).
const assetMap = {
  "Ferdenann waking 1.png": "walk1.png",
  "Ferdenann walking 2.png": "walk2.png",
  "Ferdenann jumping.png": "jump.png",
  "detenition.png": "office.png",
};
for (const [src, dest] of Object.entries(assetMap)) {
  cpSync(join(here, "assets", src), join(assetsOut, dest));
}
cpSync(join(here, "web", "index.html"), join(outDir, "index.html"));

const options = {
  entryPoints: [join(here, "src", "main.ts")],
  bundle: true,
  minify: true,
  sourcemap: false,
  target: "es2020",
  outfile: join(outDir, "game.js"),
  logLevel: "info",
};

if (process.argv.includes("--watch")) {
  const ctx = await esbuild.context(options);
  await ctx.watch();
  console.log("watching...");
} else {
  await esbuild.build(options);
}
