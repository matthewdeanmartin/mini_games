// Late Again! — a school sidescroller + escape-the-office adventure.
// Designed by Eloise, coded with a little robot help.

import { loadAssets, Assets, drawSprite } from "./assets";
import { DialogueBox } from "./dialogue";
import { HallwayScene } from "./hallway";
import { OfficeScene } from "./office";

const W = 960;
const H = 540;

const canvas = document.getElementById("game") as HTMLCanvasElement;
const ctx = canvas.getContext("2d")!;
ctx.imageSmoothingEnabled = true;
ctx.imageSmoothingQuality = "high";

function resize(): void {
  const scale = Math.min(
    (window.innerWidth - 20) / W,
    (window.innerHeight - 60) / H
  );
  canvas.style.width = `${Math.floor(W * scale)}px`;
  canvas.style.height = `${Math.floor(H * scale)}px`;
}
window.addEventListener("resize", resize);
resize();

function canvasCoords(e: PointerEvent): { x: number; y: number } {
  const rect = canvas.getBoundingClientRect();
  return {
    x: ((e.clientX - rect.left) * W) / rect.width,
    y: ((e.clientY - rect.top) * H) / rect.height,
  };
}

type SceneName = "title" | "hallway" | "office";

async function main(): Promise<void> {
  drawLoading();
  const assets = await loadAssets();

  const keys = new Set<string>();
  let scene: SceneName = "title";
  let titleT = 0;

  const dialogue = new DialogueBox();
  const office = new OfficeScene(assets, dialogue);
  const hallway = new HallwayScene(assets, dialogue, keys, () => {
    scene = "office";
    office.start();
  });

  window.addEventListener("keydown", (e) => {
    if (["Space", "ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"].includes(e.code)) {
      e.preventDefault();
    }
    if (e.repeat) return;
    keys.add(e.code);
    if (scene === "title") {
      startGame();
    } else if (scene === "hallway") {
      hallway.onKeyDown(e.code);
    } else {
      office.onKeyDown(e.code);
    }
  });
  window.addEventListener("keyup", (e) => keys.delete(e.code));
  window.addEventListener("blur", () => keys.clear());

  canvas.addEventListener("pointerdown", (e) => {
    canvas.setPointerCapture(e.pointerId);
    const { x, y } = canvasCoords(e);
    if (scene === "title") {
      startGame();
    } else if (scene === "hallway") {
      hallway.onPointerDown(x, y, e.pointerId, e.pointerType !== "mouse");
    } else {
      office.onPointerDown(x, y);
    }
  });
  canvas.addEventListener("pointermove", (e) => {
    const { x, y } = canvasCoords(e);
    if (scene === "office") office.onPointerMove(x, y);
  });
  canvas.addEventListener("pointerup", (e) => {
    const { x, y } = canvasCoords(e);
    if (scene === "hallway") hallway.onPointerUp(e.pointerId);
    else if (scene === "office") office.onPointerUp(x, y);
  });

  function startGame(): void {
    scene = "hallway";
    hallway.start();
  }

  let last = performance.now();
  function frame(now: number): void {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;

    if (scene === "title") {
      titleT += dt;
      drawTitle(assets, titleT);
    } else if (scene === "hallway") {
      hallway.update(dt);
      hallway.draw(ctx);
    } else {
      office.update(dt);
      office.draw(ctx);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function drawLoading(): void {
  ctx.fillStyle = "#141822";
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = "#ecf0f1";
  ctx.font = "20px 'Courier New', monospace";
  ctx.textAlign = "center";
  ctx.fillText("loading…", W / 2, H / 2);
  ctx.textAlign = "left";
}

function drawTitle(assets: Assets, t: number): void {
  // hallway-ish backdrop
  ctx.fillStyle = "#9c9c9c";
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = "#f7f0c0";
  ctx.fillRect(0, 380, W, H - 380);
  ctx.fillStyle = "#111";
  ctx.fillRect(0, 374, W, 8);

  const bounce = Math.abs(Math.sin(t * 2.5)) * 18;
  drawSprite(ctx, assets.jump, W / 2 + 240, 400 - bounce, 200, false);
  drawSprite(
    ctx,
    Math.floor(t * 4) % 2 === 0 ? assets.walk1 : assets.walk2,
    W / 2 - 260,
    408,
    200,
    true
  );

  ctx.textAlign = "center";
  ctx.fillStyle = "#111";
  ctx.font = "bold 64px 'Courier New', monospace";
  ctx.fillText("LATE AGAIN!", W / 2 + 3, 143);
  ctx.fillStyle = "#e74c3c";
  ctx.fillText("LATE AGAIN!", W / 2, 140);

  ctx.fillStyle = "#111";
  ctx.font = "20px 'Courier New', monospace";
  ctx.fillText("a school adventure by Eloise", W / 2, 190);

  if (Math.floor(t * 2) % 2 === 0) {
    ctx.fillStyle = "#111";
    ctx.font = "bold 22px 'Courier New', monospace";
    ctx.fillText("click or press any key to start", W / 2, 300);
  }
  ctx.textAlign = "left";
}

main();
