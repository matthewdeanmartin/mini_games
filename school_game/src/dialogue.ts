// Simple click-to-advance dialogue box drawn at the bottom of the canvas.

export interface Line {
  speaker: string;
  text: string;
  thought?: boolean;
}

const SPEAKER_COLORS: Record<string, string> = {
  Fertinann: "#c0392b",
  "Hall monitor Haily": "#e67e22",
  Oddward: "#8e44ad",
  "???": "#e67e22",
  "": "#7f8c8d",
};

export function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number
): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let cur = "";
  for (const word of words) {
    const test = cur ? cur + " " + word : word;
    if (ctx.measureText(test).width > maxWidth && cur) {
      lines.push(cur);
      cur = word;
    } else {
      cur = test;
    }
  }
  if (cur) lines.push(cur);
  return lines;
}

export class DialogueBox {
  private queue: Line[] = [];
  private onDone: (() => void) | null = null;
  private blinkT = 0;

  get active(): boolean {
    return this.queue.length > 0;
  }

  show(lines: Line[], onDone?: () => void): void {
    this.queue = [...lines];
    this.onDone = onDone ?? null;
  }

  advance(): void {
    if (!this.active) return;
    this.queue.shift();
    if (!this.active && this.onDone) {
      const cb = this.onDone;
      this.onDone = null;
      cb();
    }
  }

  update(dt: number): void {
    this.blinkT += dt;
  }

  draw(ctx: CanvasRenderingContext2D, canvasW: number, canvasH: number): void {
    if (!this.active) return;
    const line = this.queue[0];
    const boxH = 110;
    const x = 20;
    const y = canvasH - boxH - 14;
    const w = canvasW - 40;

    ctx.save();
    ctx.fillStyle = "rgba(20, 24, 34, 0.92)";
    ctx.strokeStyle = "#f1c40f";
    ctx.lineWidth = 3;
    roundRect(ctx, x, y, w, boxH, 10);
    ctx.fill();
    ctx.stroke();

    let textY = y + 26;
    if (line.speaker) {
      ctx.fillStyle = SPEAKER_COLORS[line.speaker] ?? "#3498db";
      ctx.font = "bold 16px 'Courier New', monospace";
      const label = line.thought ? `${line.speaker} (thinking)` : line.speaker;
      ctx.fillText(label, x + 16, textY);
      textY += 24;
    }

    ctx.fillStyle = "#ecf0f1";
    ctx.font = line.thought
      ? "italic 16px 'Courier New', monospace"
      : "16px 'Courier New', monospace";
    for (const l of wrapText(ctx, line.text, w - 60)) {
      ctx.fillText(l, x + 16, textY);
      textY += 21;
    }

    if (Math.floor(this.blinkT * 2) % 2 === 0) {
      ctx.fillStyle = "#f1c40f";
      ctx.font = "16px 'Courier New', monospace";
      ctx.fillText("▶", x + w - 30, y + boxH - 14);
    }
    ctx.restore();
  }
}

export function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
): void {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
