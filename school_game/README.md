# Late Again! (school_game)

A side-scroller + point-and-click adventure. Design & art by Eloise
(see `spec/spec.md` and `assets/`), code in TypeScript.

## How it's put together

- `src/` — TypeScript source
  - `hallway.ts` — scene 1: side-scrolling hallway (move, jump, crouch, Haily)
  - `office.ts` — scene 2: principal's office (inventory, drag-to-combine puzzle)
  - `dialogue.ts` — the talk boxes
  - `assets.ts` — loads the drawings and crops the character out of the big PNGs
- `web/index.html` — page shell
- `build.mjs` — bundles everything into `../docs/school_game/` for GitHub Pages

## Working on it

```bash
cd school_game
npm install        # once
npm run build      # typecheck + bundle into ../docs/school_game/
npm run watch      # rebuild on every save while playtesting
```

Then open `docs/school_game/index.html` via any local web server, e.g.:

```bash
npx http-server docs
```

## Walkthrough (spoilers!)

gum (under the desk) + ruler (in the trash) = sticky ruler →
grab the coins on Mr.Best's desk without waking him →
buy Oddward's pin for 25 cents → use the pin on the locked door.
