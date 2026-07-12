// Scene 1: side-scrolling school hallway.
// Controls: A/← back, D/→ forward, SPACE jump, S/↓ crouch.

import { Assets, drawSprite } from "./assets";
import { DialogueBox } from "./dialogue";

const W = 960;
const H = 540;
const GROUND_Y = 470;
const WORLD_W = 3200;
const DOOR_X = 2950;
const HAILY_X = 1700;
const PLAYER_H = 170;

const MOVE_SPEED = 300;
const CROUCH_SPEED = 110;
const JUMP_VY = -640;
const GRAVITY = 1700;

interface TouchButton {
  x: number;
  y: number;
  r: number;
  label: string;
  action: "left" | "right" | "jump";
  held: boolean;
  pointerId: number | null;
}

export class HallwayScene {
  private px = 160;
  private py = GROUND_Y;
  private vy = 0;
  private facingRight = true;
  private crouching = false;
  private walkT = 0;
  private moving = false;
  private camX = 0;

  private hailyDone = false;
  private entering = false;
  private fade = 0;

  private touchSeen = false;
  private buttons: TouchButton[] = [
    { x: 70, y: H - 60, r: 42, label: "◀", action: "left", held: false, pointerId: null },
    { x: 175, y: H - 60, r: 42, label: "▶", action: "right", held: false, pointerId: null },
    { x: W - 80, y: H - 60, r: 46, label: "⤒", action: "jump", held: false, pointerId: null },
  ];

  constructor(
    private assets: Assets,
    private dialogue: DialogueBox,
    private keys: Set<string>,
    private onEnterOffice: () => void
  ) {}

  start(): void {
    this.dialogue.show([
      {
        speaker: "Fertinann",
        text: "eehh? Why's the hallway empty? It's never empty.",
        thought: true,
      },
    ]);
  }

  onKeyDown(code: string): void {
    if (this.dialogue.active) {
      if (code === "Space" || code === "Enter") this.dialogue.advance();
      return;
    }
    if (code === "Space" && this.py >= GROUND_Y && !this.entering) {
      this.vy = JUMP_VY;
    }
  }

  onPointerDown(x: number, y: number, pointerId: number, isTouch: boolean): void {
    if (isTouch) this.touchSeen = true;
    if (this.dialogue.active) {
      this.dialogue.advance();
      return;
    }
    if (isTouch) {
      for (const b of this.buttons) {
        if (Math.hypot(x - b.x, y - b.y) <= b.r + 12) {
          b.held = true;
          b.pointerId = pointerId;
          if (b.action === "jump" && this.py >= GROUND_Y && !this.entering) {
            this.vy = JUMP_VY;
          }
        }
      }
    }
  }

  onPointerUp(pointerId: number): void {
    for (const b of this.buttons) {
      if (b.pointerId === pointerId) {
        b.held = false;
        b.pointerId = null;
      }
    }
  }

  private held(action: "left" | "right"): boolean {
    return this.buttons.some((b) => b.action === action && b.held);
  }

  update(dt: number): void {
    this.dialogue.update(dt);

    if (this.entering) {
      this.fade = Math.min(1, this.fade + dt * 1.5);
      if (this.fade >= 1) this.onEnterOffice();
      return;
    }

    const inputLocked = this.dialogue.active;
    let dir = 0;
    if (!inputLocked) {
      const left = this.keys.has("KeyA") || this.keys.has("ArrowLeft") || this.held("left");
      const right = this.keys.has("KeyD") || this.keys.has("ArrowRight") || this.held("right");
      this.crouching =
        (this.keys.has("KeyS") || this.keys.has("ArrowDown")) && this.py >= GROUND_Y;
      if (left) dir -= 1;
      if (right) dir += 1;
    } else {
      this.crouching = false;
    }

    const speed = this.crouching ? CROUCH_SPEED : MOVE_SPEED;
    this.px += dir * speed * dt;
    this.px = Math.max(60, Math.min(WORLD_W - 40, this.px));
    this.moving = dir !== 0;
    if (dir !== 0) this.facingRight = dir > 0;
    if (this.moving) this.walkT += dt;

    // jump physics
    this.vy += GRAVITY * dt;
    this.py += this.vy * dt;
    if (this.py > GROUND_Y) {
      this.py = GROUND_Y;
      this.vy = 0;
    }

    // Haily catches you partway down the hall
    if (!this.hailyDone && this.px > HAILY_X - 320) {
      this.hailyDone = true;
      this.dialogue.show([
        { speaker: "???", text: "HEY over there your late!" },
        { speaker: "Fertinann", text: "oh crud" },
        {
          speaker: "Hall monitor Haily",
          text: "your late go to the principal's office now",
        },
      ]);
    }

    // reach the principal's door
    if (this.hailyDone && !this.dialogue.active && this.px > DOOR_X - 60) {
      this.entering = true;
    }

    this.camX = Math.max(0, Math.min(WORLD_W - W, this.px - W / 2));
  }

  draw(ctx: CanvasRenderingContext2D): void {
    ctx.clearRect(0, 0, W, H);

    // wall + floor, matching the art's palette
    ctx.fillStyle = "#9c9c9c";
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = "#f7f0c0";
    ctx.fillRect(0, GROUND_Y - 90, W, H - (GROUND_Y - 90));
    ctx.fillStyle = "#111";
    ctx.fillRect(0, GROUND_Y - 96, W, 8);

    ctx.save();
    ctx.translate(-this.camX, 0);

    this.drawDecor(ctx);
    this.drawHaily(ctx);
    this.drawDoor(ctx);

    // Ferdinann
    const inAir = this.py < GROUND_Y;
    const def = inAir
      ? this.assets.jump
      : this.moving && Math.floor(this.walkT * 6) % 2 === 0
        ? this.assets.walk1
        : this.assets.walk2;
    drawSprite(
      ctx,
      def,
      this.px,
      this.py,
      PLAYER_H,
      this.facingRight,
      this.crouching ? 0.62 : 1
    );

    ctx.restore();

    // HUD
    if (!this.dialogue.active && !this.entering) {
      ctx.fillStyle = "rgba(20,24,34,0.75)";
      ctx.fillRect(0, 0, W, 30);
      ctx.fillStyle = "#ecf0f1";
      ctx.font = "14px 'Courier New', monospace";
      ctx.fillText(
        this.hailyDone
          ? "Go to the principal's office →"
          : "A/D or ←/→ move · SPACE jump · S crouch",
        14,
        20
      );
    }

    if (this.touchSeen && !this.dialogue.active) this.drawTouchButtons(ctx);
    this.dialogue.draw(ctx, W, H);

    if (this.fade > 0) {
      ctx.fillStyle = `rgba(0,0,0,${this.fade})`;
      ctx.fillRect(0, 0, W, H);
    }
  }

  private drawDecor(ctx: CanvasRenderingContext2D): void {
    ctx.lineWidth = 5;
    ctx.strokeStyle = "#111";

    // lockers
    for (let i = 0; i < 8; i++) {
      const x = 260 + i * 78;
      ctx.fillStyle = i % 2 === 0 ? "#3f5fbf" : "#4a6dd8";
      ctx.fillRect(x, GROUND_Y - 300, 70, 208);
      ctx.strokeRect(x, GROUND_Y - 300, 70, 208);
      ctx.fillStyle = "#111";
      ctx.fillRect(x + 12, GROUND_Y - 250, 24, 6);
      ctx.fillRect(x + 50, GROUND_Y - 210, 8, 18);
    }

    // "HAPPY" poster (like the one in the office art)
    this.poster(ctx, 1150, GROUND_Y - 330, 130, 130, "#f4d03f", ["HAPPY"], "#111");
    // five days poster
    this.poster(
      ctx,
      1950,
      GROUND_Y - 340,
      210,
      140,
      "#45d9e8",
      ["Five days", "of school", "Five ways", "to Rule!"],
      "#111"
    );
    this.poster(ctx, 2450, GROUND_Y - 330, 150, 120, "#f4a7c3", ["GO", "TEAM!"], "#111");

    // clock
    ctx.fillStyle = "#fff";
    ctx.beginPath();
    ctx.arc(950, GROUND_Y - 380, 34, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(950, GROUND_Y - 380);
    ctx.lineTo(950, GROUND_Y - 404);
    ctx.moveTo(950, GROUND_Y - 380);
    ctx.lineTo(968, GROUND_Y - 372);
    ctx.stroke();

    // wet floor sign to hop over
    this.wetFloorSign(ctx, 1250);
    // trash can to hop over
    ctx.fillStyle = "#3a3a3a";
    ctx.fillRect(2200, GROUND_Y - 66, 54, 66);
    ctx.strokeRect(2200, GROUND_Y - 66, 54, 66);

    // classroom doors in the background
    for (const dx of [700, 1500]) {
      ctx.fillStyle = "#8a5a2b";
      ctx.fillRect(dx, GROUND_Y - 310, 110, 218);
      ctx.strokeRect(dx, GROUND_Y - 310, 110, 218);
      ctx.fillStyle = "#cfd8dc";
      ctx.fillRect(dx + 34, GROUND_Y - 280, 42, 70);
      ctx.strokeRect(dx + 34, GROUND_Y - 280, 42, 70);
    }
  }

  private poster(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    w: number,
    h: number,
    bg: string,
    lines: string[],
    fg: string
  ): void {
    ctx.fillStyle = bg;
    ctx.fillRect(x, y, w, h);
    ctx.strokeRect(x, y, w, h);
    ctx.fillStyle = fg;
    ctx.font = "bold 18px 'Courier New', monospace";
    lines.forEach((l, i) => {
      ctx.fillText(l, x + 12, y + 28 + i * 24);
    });
  }

  private wetFloorSign(ctx: CanvasRenderingContext2D, x: number): void {
    ctx.fillStyle = "#f4d03f";
    ctx.beginPath();
    ctx.moveTo(x, GROUND_Y);
    ctx.lineTo(x + 26, GROUND_Y - 62);
    ctx.lineTo(x + 52, GROUND_Y);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#111";
    ctx.font = "bold 11px 'Courier New', monospace";
    ctx.fillText("WET", x + 14, GROUND_Y - 22);
  }

  private drawHaily(ctx: CanvasRenderingContext2D): void {
    const x = HAILY_X;
    const y = GROUND_Y;
    ctx.lineWidth = 5;
    ctx.strokeStyle = "#111";
    // legs
    ctx.fillStyle = "#333";
    ctx.fillRect(x - 16, y - 60, 12, 60);
    ctx.fillRect(x + 4, y - 60, 12, 60);
    // body
    ctx.fillStyle = "#e67e22";
    ctx.fillRect(x - 26, y - 130, 52, 74);
    ctx.strokeRect(x - 26, y - 130, 52, 74);
    // sash
    ctx.fillStyle = "#fff";
    ctx.save();
    ctx.translate(x, y - 94);
    ctx.rotate(-0.5);
    ctx.fillRect(-30, -8, 60, 16);
    ctx.strokeRect(-30, -8, 60, 16);
    ctx.restore();
    // head
    ctx.fillStyle = "#fcd9a0";
    ctx.beginPath();
    ctx.arc(x, y - 162, 30, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    // hair
    ctx.fillStyle = "#4a2c0a";
    ctx.beginPath();
    ctx.arc(x, y - 170, 30, Math.PI, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(x - 30, y - 170, 10, 44);
    ctx.fillRect(x + 20, y - 170, 10, 44);
    // eyes
    ctx.fillStyle = "#111";
    ctx.fillRect(x - 12, y - 166, 5, 12);
    ctx.fillRect(x + 7, y - 166, 5, 12);
    // label
    ctx.fillStyle = "#111";
    ctx.font = "bold 12px 'Courier New', monospace";
    ctx.fillText("HALL MONITOR", x - 48, y - 210);
  }

  private drawDoor(ctx: CanvasRenderingContext2D): void {
    const x = DOOR_X;
    ctx.lineWidth = 6;
    ctx.strokeStyle = "#111";
    ctx.fillStyle = "#8a5a2b";
    ctx.fillRect(x - 70, GROUND_Y - 340, 140, 248);
    ctx.strokeRect(x - 70, GROUND_Y - 340, 140, 248);
    ctx.fillStyle = "#cfd8dc";
    ctx.fillRect(x - 26, GROUND_Y - 306, 52, 84);
    ctx.strokeRect(x - 26, GROUND_Y - 306, 52, 84);
    ctx.fillStyle = "#f4d03f";
    ctx.fillRect(x + 34, GROUND_Y - 200, 14, 14);
    // sign
    ctx.fillStyle = "#f4d03f";
    ctx.fillRect(x - 80, GROUND_Y - 390, 160, 34);
    ctx.strokeRect(x - 80, GROUND_Y - 390, 160, 34);
    ctx.fillStyle = "#111";
    ctx.font = "bold 14px 'Courier New', monospace";
    ctx.fillText("PRINCIPAL Mr.Best", x - 72, GROUND_Y - 368);
  }

  private drawTouchButtons(ctx: CanvasRenderingContext2D): void {
    for (const b of this.buttons) {
      ctx.fillStyle = b.held ? "rgba(241,196,15,0.7)" : "rgba(236,240,241,0.35)";
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#111";
      ctx.font = "bold 30px 'Courier New', monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(b.label, b.x, b.y);
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
    }
  }
}
