// Asset loading. The character drawings are huge (3480px) with lots of white
// space, so each sprite carries a crop rect around the actual figure.
// The artist drew Ferdinann facing LEFT; scenes flip him when walking right.

export interface SpriteDef {
  img: HTMLImageElement;
  sx: number;
  sy: number;
  sw: number;
  sh: number;
}

export interface Assets {
  walk1: SpriteDef;
  walk2: SpriteDef;
  jump: SpriteDef;
  office: HTMLImageElement;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`failed to load ${src}`));
    img.src = src;
  });
}

export async function loadAssets(): Promise<Assets> {
  const [walk1Img, walk2Img, jumpImg, office] = await Promise.all([
    loadImage("assets/walk1.png"),
    loadImage("assets/walk2.png"),
    loadImage("assets/jump.png"),
    loadImage("assets/office.png"),
  ]);
  return {
    walk1: { img: walk1Img, sx: 1180, sy: 850, sw: 980, sh: 2010 },
    walk2: { img: walk2Img, sx: 1180, sy: 850, sw: 980, sh: 2010 },
    // jump art has arms out (wider) and a shadow below the feet (excluded)
    jump: { img: jumpImg, sx: 1150, sy: 850, sw: 1090, sh: 1800 },
    office,
  };
}

// Draws a sprite anchored at bottom-center of (feetX, feetY).
// `unitScale` is pixels-on-screen per pixel-of-crop for the WALK sprites,
// so all poses render at a consistent body scale.
export function drawSprite(
  ctx: CanvasRenderingContext2D,
  def: SpriteDef,
  feetX: number,
  feetY: number,
  targetWalkHeight: number,
  facingRight: boolean,
  squash = 1
): void {
  const unitScale = targetWalkHeight / 2010;
  const w = def.sw * unitScale;
  const h = def.sh * unitScale * squash;
  ctx.save();
  ctx.translate(feetX, feetY);
  if (facingRight) ctx.scale(-1, 1);
  ctx.drawImage(def.img, def.sx, def.sy, def.sw, def.sh, -w / 2, -h, w, h);
  ctx.restore();
}
