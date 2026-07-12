// Scene 2: the principal's office (point & click).
// OBJETEVE: FIND OUT HOW TO LEAVE.
// Puzzle: gum + ruler = sticky ruler → grab coins from Mr.Best's desk without
// waking him → buy Oddward's pin for 25 cents → pick the door lock.

import { Assets, drawSprite } from "./assets";
import { DialogueBox, roundRect, wrapText } from "./dialogue";

const W = 960;
const H = 540;

type ItemId = "gum" | "ruler" | "stickyRuler" | "coin" | "pin";

interface Item {
  id: ItemId;
  name: string;
  examine: string;
}

interface Hotspot {
  id: string;
  // normalized coords relative to the background art
  nx: number;
  ny: number;
  nw: number;
  nh: number;
  visible: () => boolean;
}

const ITEM_DEFS: Record<ItemId, Item> = {
  gum: { id: "gum", name: "gum", examine: "It's mint… disgusting" },
  ruler: { id: "ruler", name: "ruler", examine: "A wooden ruler. 12 inches of possibility." },
  stickyRuler: {
    id: "stickyRuler",
    name: "sticky ruler",
    examine: "A ruler with gum stuck on the end. Science.",
  },
  coin: { id: "coin", name: "25 cents", examine: "25 cents exactly. Pin money." },
  pin: { id: "pin", name: "pin", examine: "A shiny pin from Oddward. Pointy." },
};

export class OfficeScene {
  private inventory: (ItemId | null)[] = [null, null, null, null, null, null];

  private tookGum = false;
  private tookRuler = false;
  private tookCoins = false;
  private hasPin = false;
  private oddwardMet = false;
  private escaped = false;
  private winT = 0;

  private hoverId: string | null = null;
  private dragging: { slot: number; item: ItemId; x: number; y: number } | null = null;
  private dragMoved = false;
  private t = 0;

  // background drawn with "contain" fit on the left, inventory panel on the right
  private bg = { x: 0, y: 0, w: 749, h: 540 };
  private panelX = 749;

  private hotspots: Hotspot[] = [
    { id: "gum", nx: 0.14, ny: 0.78, nw: 0.09, nh: 0.1, visible: () => !this.tookGum },
    { id: "ruler", nx: 0.675, ny: 0.28, nw: 0.1, nh: 0.2, visible: () => !this.tookRuler },
    { id: "coins", nx: 0.82, ny: 0.43, nw: 0.09, nh: 0.07, visible: () => !this.tookCoins },
    { id: "oddward", nx: 0.3, ny: 0.4, nw: 0.15, nh: 0.32, visible: () => true },
    { id: "mrbest", nx: 0.87, ny: 0.55, nw: 0.13, nh: 0.28, visible: () => true },
    { id: "note", nx: 0.52, ny: 0.28, nw: 0.07, nh: 0.09, visible: () => true },
    { id: "door", nx: 0.8, ny: 0.02, nw: 0.19, nh: 0.36, visible: () => true },
  ];

  constructor(
    private assets: Assets,
    private dialogue: DialogueBox
  ) {
    const bgAspect = assets.office.width / assets.office.height;
    this.bg.w = Math.round(H * bgAspect);
    this.bg.h = H;
    this.panelX = this.bg.w;
  }

  start(): void {
    this.dialogue.show([
      {
        speaker: "",
        text: "In the principal's office. Principal Mr.Best is sleeping, not noticing you coming in.",
      },
      { speaker: "", text: "OBJETEVE: FIND OUT HOW TO LEAVE" },
    ]);
  }

  onKeyDown(code: string): void {
    if (this.dialogue.active && (code === "Space" || code === "Enter")) {
      this.dialogue.advance();
    }
  }

  // --- coordinate helpers ---

  private hotspotRect(h: Hotspot): { x: number; y: number; w: number; h: number } {
    return {
      x: this.bg.x + h.nx * this.bg.w,
      y: this.bg.y + h.ny * this.bg.h,
      w: h.nw * this.bg.w,
      h: h.nh * this.bg.h,
    };
  }

  private hotspotAt(x: number, y: number): Hotspot | null {
    for (const h of this.hotspots) {
      if (!h.visible()) continue;
      const r = this.hotspotRect(h);
      if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) return h;
    }
    return null;
  }

  private slotRect(i: number): { x: number; y: number; w: number; h: number } {
    const size = 82;
    const pad = 12;
    const cols = 2;
    const x0 = this.panelX + (W - this.panelX - cols * size - pad) / 2;
    const col = i % cols;
    const row = Math.floor(i / cols);
    return { x: x0 + col * (size + pad), y: 150 + row * (size + pad), w: size, h: size };
  }

  private slotAt(x: number, y: number): number | null {
    for (let i = 0; i < this.inventory.length; i++) {
      const r = this.slotRect(i);
      if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) return i;
    }
    return null;
  }

  private addItem(id: ItemId): void {
    const i = this.inventory.indexOf(null);
    if (i >= 0) this.inventory[i] = id;
  }

  private removeItem(id: ItemId): void {
    const i = this.inventory.indexOf(id);
    if (i >= 0) this.inventory[i] = null;
  }

  // --- input ---

  onPointerDown(x: number, y: number): void {
    if (this.escaped) {
      // "play again" button
      if (x > W / 2 - 90 && x < W / 2 + 90 && y > 420 && y < 470) location.reload();
      return;
    }
    if (this.dialogue.active) {
      this.dialogue.advance();
      return;
    }
    const slot = this.slotAt(x, y);
    if (slot !== null && this.inventory[slot]) {
      this.dragging = { slot, item: this.inventory[slot]!, x, y };
      this.dragMoved = false;
      return;
    }
    const h = this.hotspotAt(x, y);
    if (h) this.clickHotspot(h.id);
  }

  onPointerMove(x: number, y: number): void {
    if (this.dragging) {
      if (Math.hypot(x - this.dragging.x, y - this.dragging.y) > 6) this.dragMoved = true;
      this.dragging.x = x;
      this.dragging.y = y;
    } else {
      this.hoverId = this.hotspotAt(x, y)?.id ?? (this.slotAt(x, y) !== null ? "slot" : null);
    }
  }

  onPointerUp(x: number, y: number): void {
    if (!this.dragging) return;
    const drag = this.dragging;
    this.dragging = null;

    if (!this.dragMoved) {
      // plain click on an item: examine it
      this.say("Fertinann", ITEM_DEFS[drag.item].examine, true);
      return;
    }

    const slot = this.slotAt(x, y);
    if (slot !== null && slot !== drag.slot && this.inventory[slot]) {
      this.combine(drag.item, this.inventory[slot]!);
      return;
    }
    const h = this.hotspotAt(x, y);
    if (h) this.useItemOn(drag.item, h.id);
  }

  private say(speaker: string, text: string, thought = false): void {
    this.dialogue.show([{ speaker, text, thought }]);
  }

  private clickHotspot(id: string): void {
    switch (id) {
      case "gum":
        this.tookGum = true;
        this.addItem("gum");
        this.say(
          "Fertinann",
          "gum. it's most likely Tom's gum from last time he was here. It's mint… disgusting"
        );
        break;
      case "ruler":
        this.tookRuler = true;
        this.addItem("ruler");
        this.say("Fertinann", "A ruler in the trash can? Perfectly good ruler.");
        break;
      case "coins":
        this.say("Fertinann", "going to close will definitely awake him", true);
        break;
      case "oddward":
        if (!this.oddwardMet) {
          this.oddwardMet = true;
          this.dialogue.show([
            { speaker: "Fertinann", text: "wachya selling?" },
            { speaker: "Oddward", text: "Hey wanna buy a pin im selling them for 25 cents" },
            { speaker: "Fertinann", text: "i dont got money" },
            { speaker: "Oddward", text: "come back later i'll be here" },
          ]);
        } else if (this.inventory.includes("coin")) {
          this.buyPin();
        } else if (this.hasPin) {
          this.say("Oddward", "no refunds.");
        } else {
          this.say("Oddward", "come back later i'll be here");
        }
        break;
      case "mrbest":
        this.dialogue.show([
          { speaker: "", text: "Zzzzz… Mr.Best is fast asleep." },
          { speaker: "Fertinann", text: "better not wake him.", thought: true },
        ]);
        break;
      case "note":
        this.dialogue.show([
          {
            speaker: "",
            text: "A sticky note is taped to the wall: \"you can combine objects by clicking and dragging them — hall monitor Haily\"",
          },
        ]);
        break;
      case "door":
        if (this.hasPin) {
          this.say("Fertinann", "The pin! Maybe I can pick the lock. (drag the pin onto the door)", true);
        } else {
          this.say(
            "Fertinann",
            "Locked?! Who locks a principal's office from the OUTSIDE? Hall monitors take their job way too seriously.",
            true
          );
        }
        break;
    }
  }

  private combine(a: ItemId, b: ItemId): void {
    const pair = [a, b].sort().join("+");
    if (pair === "gum+ruler") {
      this.removeItem("gum");
      this.removeItem("ruler");
      this.addItem("stickyRuler");
      this.say("Fertinann", "gum… on a ruler. Now it's a GRABBER. I'm a genius.");
    } else {
      this.say("Fertinann", "hmm, those don't go together.", true);
    }
  }

  private useItemOn(item: ItemId, hotspot: string): void {
    if (hotspot === "coins") {
      if (item === "stickyRuler") {
        this.tookCoins = true;
        this.removeItem("stickyRuler");
        this.addItem("coin");
        this.dialogue.show([
          { speaker: "", text: "You reach waaaay over with the sticky ruler… tap… got it!" },
          { speaker: "Fertinann", text: "25 cents! And Mr.Best is still snoring." },
        ]);
      } else if (item === "ruler") {
        this.say("Fertinann", "The coins just slide off the ruler. It needs to be… stickier.", true);
      } else if (item === "gum") {
        this.say("Fertinann", "I'm not throwing gum at the principal.", true);
      } else {
        this.say("Fertinann", "that won't reach the coins.", true);
      }
      return;
    }
    if (hotspot === "oddward") {
      if (item === "coin") {
        this.buyPin();
      } else {
        this.say("Oddward", "i only take quarters.");
      }
      return;
    }
    if (hotspot === "door") {
      if (item === "pin") {
        this.removeItem("pin");
        this.dialogue.show(
          [
            { speaker: "", text: "You wiggle the pin in the lock… click!" },
            { speaker: "Fertinann", text: "FREEDOM!" },
            { speaker: "Fertinann", text: "…wait. now I'm even MORE late for class.", thought: true },
          ],
          () => {
            this.escaped = true;
          }
        );
      } else {
        this.say("Fertinann", "that's not going to open a locked door.", true);
      }
      return;
    }
    if (hotspot === "mrbest") {
      this.say("Fertinann", "no. no no no. He stays asleep.", true);
      return;
    }
    this.say("Fertinann", "that doesn't do anything.", true);
  }

  private buyPin(): void {
    if (!this.oddwardMet) {
      this.clickHotspot("oddward");
      return;
    }
    this.removeItem("coin");
    this.hasPin = true;
    this.addItem("pin");
    this.dialogue.show([
      { speaker: "Fertinann", text: "one pin please" },
      { speaker: "Oddward", text: "25 cents, one pin. pleasure doing business" },
    ]);
  }

  update(dt: number): void {
    this.t += dt;
    this.dialogue.update(dt);
    if (this.escaped) this.winT += dt;
  }

  // --- drawing ---

  draw(ctx: CanvasRenderingContext2D): void {
    ctx.fillStyle = "#141822";
    ctx.fillRect(0, 0, W, H);

    ctx.drawImage(this.assets.office, this.bg.x, this.bg.y, this.bg.w, this.bg.h);

    this.drawOverlays(ctx);
    this.drawPanel(ctx);

    // hover highlight
    if (this.hoverId && this.hoverId !== "slot" && !this.dialogue.active && !this.escaped) {
      const h = this.hotspots.find((s) => s.id === this.hoverId);
      if (h && h.visible()) {
        const r = this.hotspotRect(h);
        ctx.save();
        ctx.strokeStyle = `rgba(241,196,15,${0.55 + 0.35 * Math.sin(this.t * 5)})`;
        ctx.lineWidth = 3;
        roundRect(ctx, r.x - 3, r.y - 3, r.w + 6, r.h + 6, 8);
        ctx.stroke();
        ctx.restore();
      }
    }

    if (this.dragging) {
      this.drawItemIcon(ctx, this.dragging.item, this.dragging.x, this.dragging.y, 64, 0.85);
    }

    this.dialogue.draw(ctx, W, H);

    if (this.escaped) this.drawWin(ctx);
  }

  private drawOverlays(ctx: CanvasRenderingContext2D): void {
    const px = (nx: number) => this.bg.x + nx * this.bg.w;
    const py = (ny: number) => this.bg.y + ny * this.bg.h;
    ctx.save();
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#111";

    // mint gum under the front desk
    if (!this.tookGum) {
      ctx.fillStyle = "#59d6a8";
      ctx.beginPath();
      ctx.ellipse(px(0.185), py(0.85), 11, 8, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }

    // ruler sticking out of the trash can
    if (!this.tookRuler) {
      ctx.save();
      ctx.translate(px(0.71), py(0.36));
      ctx.rotate(-0.5);
      ctx.fillStyle = "#f4d03f";
      ctx.fillRect(-8, -52, 16, 62);
      ctx.strokeRect(-8, -52, 16, 62);
      ctx.strokeStyle = "#111";
      ctx.lineWidth = 2;
      for (let i = 1; i < 5; i++) {
        ctx.beginPath();
        ctx.moveTo(-8, -52 + i * 12);
        ctx.lineTo(-1, -52 + i * 12);
        ctx.stroke();
      }
      ctx.restore();
    }

    // coins on Mr.Best's desk
    if (!this.tookCoins) {
      ctx.fillStyle = "#f4d03f";
      for (const [dx, dy] of [
        [0, 0],
        [16, 4],
        [8, -7],
      ]) {
        ctx.beginPath();
        ctx.arc(px(0.855) + dx, py(0.475) + dy, 7, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }
    }

    // sticky note on the wall
    ctx.fillStyle = "#fdf6a3";
    const nx = px(0.535);
    const ny = py(0.295);
    ctx.fillRect(nx, ny, 34, 34);
    ctx.strokeRect(nx, ny, 34, 34);
    ctx.strokeStyle = "#9c8b1f";
    ctx.lineWidth = 2;
    for (let i = 1; i <= 3; i++) {
      ctx.beginPath();
      ctx.moveTo(nx + 5, ny + i * 8);
      ctx.lineTo(nx + 29, ny + i * 8);
      ctx.stroke();
    }
    ctx.restore();
  }

  private drawPanel(ctx: CanvasRenderingContext2D): void {
    ctx.save();
    ctx.fillStyle = "#1d2433";
    ctx.fillRect(this.panelX, 0, W - this.panelX, H);
    ctx.strokeStyle = "#f1c40f";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(this.panelX + 1, 0);
    ctx.lineTo(this.panelX + 1, H);
    ctx.stroke();

    ctx.fillStyle = "#f1c40f";
    ctx.font = "bold 15px 'Courier New', monospace";
    ctx.fillText("OBJETEVE:", this.panelX + 16, 32);
    ctx.fillStyle = "#ecf0f1";
    ctx.font = "13px 'Courier New', monospace";
    let y = 52;
    for (const l of wrapText(ctx, "FIND OUT HOW TO LEAVE", W - this.panelX - 30)) {
      ctx.fillText(l, this.panelX + 16, y);
      y += 17;
    }

    ctx.fillStyle = "#f1c40f";
    ctx.font = "bold 15px 'Courier New', monospace";
    ctx.fillText("🎒 BACKPACK", this.panelX + 16, 128);

    for (let i = 0; i < this.inventory.length; i++) {
      const r = this.slotRect(i);
      ctx.fillStyle = "#2b3346";
      ctx.strokeStyle = this.hoverId === "slot" ? "#f1c40f" : "#4a5470";
      ctx.lineWidth = 2;
      roundRect(ctx, r.x, r.y, r.w, r.h, 8);
      ctx.fill();
      ctx.stroke();
      const item = this.inventory[i];
      if (item && !(this.dragging && this.dragging.slot === i && this.dragMoved)) {
        this.drawItemIcon(ctx, item, r.x + r.w / 2, r.y + r.h / 2 - 6, 48, 1);
        ctx.fillStyle = "#ecf0f1";
        ctx.font = "11px 'Courier New', monospace";
        ctx.textAlign = "center";
        ctx.fillText(ITEM_DEFS[item].name, r.x + r.w / 2, r.y + r.h - 8);
        ctx.textAlign = "left";
      }
    }

    ctx.fillStyle = "#8a93a8";
    ctx.font = "11px 'Courier New', monospace";
    y = 460;
    for (const l of wrapText(
      ctx,
      "click things to look. drag items to combine or use them.",
      W - this.panelX - 26
    )) {
      ctx.fillText(l, this.panelX + 14, y);
      y += 15;
    }
    ctx.restore();
  }

  private drawItemIcon(
    ctx: CanvasRenderingContext2D,
    id: ItemId,
    cx: number,
    cy: number,
    size: number,
    alpha: number
  ): void {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(cx, cy);
    const s = size / 48;
    ctx.scale(s, s);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#111";
    switch (id) {
      case "gum":
        ctx.fillStyle = "#59d6a8";
        ctx.beginPath();
        ctx.ellipse(0, 0, 14, 10, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        break;
      case "ruler":
      case "stickyRuler":
        ctx.save();
        ctx.rotate(-0.6);
        ctx.fillStyle = "#f4d03f";
        ctx.fillRect(-6, -20, 12, 40);
        ctx.strokeRect(-6, -20, 12, 40);
        ctx.lineWidth = 1.5;
        for (let i = 1; i < 5; i++) {
          ctx.beginPath();
          ctx.moveTo(-6, -20 + i * 8);
          ctx.lineTo(0, -20 + i * 8);
          ctx.stroke();
        }
        if (id === "stickyRuler") {
          ctx.fillStyle = "#59d6a8";
          ctx.beginPath();
          ctx.ellipse(0, -20, 8, 6, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.lineWidth = 2;
          ctx.stroke();
        }
        ctx.restore();
        break;
      case "coin":
        ctx.fillStyle = "#f4d03f";
        ctx.beginPath();
        ctx.arc(0, 0, 13, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        ctx.fillStyle = "#111";
        ctx.font = "bold 12px 'Courier New', monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("25", 0, 1);
        ctx.textAlign = "left";
        ctx.textBaseline = "alphabetic";
        break;
      case "pin":
        ctx.fillStyle = "#c0c8d8";
        ctx.beginPath();
        ctx.moveTo(-2, -16);
        ctx.lineTo(2, -16);
        ctx.lineTo(1, 12);
        ctx.lineTo(-1, 12);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, 12);
        ctx.lineTo(0, 17);
        ctx.stroke();
        ctx.fillStyle = "#e74c3c";
        ctx.beginPath();
        ctx.arc(0, -18, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
        break;
    }
    ctx.restore();
  }

  private drawWin(ctx: CanvasRenderingContext2D): void {
    ctx.fillStyle = "rgba(10, 14, 24, 0.88)";
    ctx.fillRect(0, 0, W, H);

    const bounce = Math.abs(Math.sin(this.winT * 3)) * 30;
    drawSprite(ctx, this.assets.jump, W / 2, 330 - bounce, 190, false);

    ctx.textAlign = "center";
    ctx.fillStyle = "#f1c40f";
    ctx.font = "bold 34px 'Courier New', monospace";
    ctx.fillText("OBJETEVE COMPLETE!", W / 2, 80);
    ctx.fillStyle = "#ecf0f1";
    ctx.font = "18px 'Courier New', monospace";
    ctx.fillText("Fertinann escaped the principal's office!", W / 2, 380);

    ctx.fillStyle = "#2ecc71";
    ctx.strokeStyle = "#111";
    ctx.lineWidth = 3;
    roundRect(ctx, W / 2 - 90, 420, 180, 50, 10);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#111";
    ctx.font = "bold 18px 'Courier New', monospace";
    ctx.fillText("Play again", W / 2, 452);
    ctx.textAlign = "left";
  }
}
