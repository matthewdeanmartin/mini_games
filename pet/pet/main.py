# pet/main.py
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ProgressBar, Static

# ----------------------------
# Helpers
# ----------------------------

def slugify(s: str) -> str:
    """Textual-safe identifier chunk: letters/numbers/_/- only."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9_-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "item"
    if s[0].isdigit():
        s = f"i_{s}"
    return s

def clamp_pct(v: int) -> int:
    return max(0, min(100, v))

# ----------------------------
# Game Data
# ----------------------------

PETS = ["snake", "dog", "cat", "spider", "bird", "fish"]
GENDERS = ["Male", "Female", "Non-binary"]

# (name, cost, hunger_gain)
FOODS = [
    ("Kibble", 5, 12),
    ("Treats", 5, 8),
    ("Fish Bits", 10, 22),
    ("Premium Meal", 10, 18),
]

@dataclass(frozen=True)
class Toy:
    slug: str
    name: str
    cost: int
    coin_reward: int
    happiness_reward: int

TOY_CATALOG: List[Toy] = []
for (name, cost, coins, happy) in [
    ("Ball", 15, 3, 2),
    ("Rope", 35, 6, 3),
    ("Laser Pointer", 70, 10, 4),
    ("Training Clicker", 120, 15, 5),
    ("Agility Set", 200, 22, 6),
]:
    TOY_CATALOG.append(Toy(slug=slugify(name), name=name, cost=cost, coin_reward=coins, happiness_reward=happy))

EGG_COST_START = 50

# ----------------------------
# State
# ----------------------------

@dataclass
class GameState:
    pet: Optional[str] = None
    gender: str = field(default_factory=lambda: random.choice(GENDERS))

    hunger: int = 80
    sleep: int = 85
    happiness: int = 60

    coins: int = 30
    toys_owned: List[Toy] = field(default_factory=list)

    pets_owned_total: int = 1  # current + previous
    eggs_owned: int = 0

    age_minutes: int = 0
    sleeping: bool = False

    paused: bool = False  # NEW

    def reset_for_new_pet(self, pet: str) -> None:
        self.pet = pet
        self.gender = random.choice(GENDERS)
        self.hunger = 80
        self.sleep = 85
        self.happiness = 60
        self.coins = 30
        self.toys_owned = []
        self.age_minutes = 0
        self.sleeping = False
        self.paused = False

# ----------------------------
# Screens
# ----------------------------

class PetSelectScreen(Screen):
    CSS = """
    PetSelectScreen { align: center middle; }
    #card { width: 72; border: round $accent; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #subtitle { content-align: center middle; color: $text-muted; padding-bottom: 1; }
    #pet_grid { grid-size: 3; grid-gutter: 1 1; padding-top: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Choose Your Pet", id="title")
            yield Label("Pick one to start. You can buy eggs later to earn more pets.", id="subtitle")
            with Grid(id="pet_grid"):
                for p in PETS:
                    yield Button(p.title(), id=f"pet_{p}", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("pet_"):
            pet = bid.removeprefix("pet_")
            self.app.start_new_run(pet)  # type: ignore[attr-defined]


class RoomScreen(Screen):
    CSS = """
    RoomScreen { layout: vertical; }
    #bars { padding: 0 1; border: round $surface; }
    #room { height: 1fr; padding: 1 1; border: round $surface; }
    #pet_box { width: 1fr; height: 1fr; content-align: center middle; border: round $accent; }
    #nav { height: auto; padding: 1 1; border: round $surface; }
    .muted { color: $text-muted; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="bars"):
            yield Label("", id="status_line")
            with Vertical():
                yield Label("Hunger", classes="muted")
                yield ProgressBar(total=100, show_eta=False, id="hunger_bar")
                yield Label("Sleep", classes="muted")
                yield ProgressBar(total=100, show_eta=False, id="sleep_bar")
                yield Label("Happiness", classes="muted")
                yield ProgressBar(total=100, show_eta=False, id="happy_bar")

        with Container(id="room"):
            yield Static("", id="pet_box")

        with Container(id="nav"):
            with Horizontal():
                yield Button("Kitchen", id="go_kitchen")
                yield Button("Play", id="go_play", variant="success")
                yield Button("Sleep", id="go_sleep")
                yield Button("Stats", id="go_stats")
                yield Button("Shop", id="go_shop")
                yield Button("Pause", id="go_pause", variant="warning")  # NEW
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_ui()

    def on_screen_resume(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        gs: GameState = self.app.gs  # type: ignore[attr-defined]
        if gs.pet is None:
            return

        paused_tag = "  |  PAUSED" if gs.paused else ""
        self.query_one("#status_line", Label).update(
            f"Pet: {gs.pet.title()}  |  Coins: {gs.coins}  |  Toys: {len(gs.toys_owned)}  |  Eggs: {gs.eggs_owned}{paused_tag}"
        )

        self.query_one("#hunger_bar", ProgressBar).progress = clamp_pct(gs.hunger)
        self.query_one("#sleep_bar", ProgressBar).progress = clamp_pct(gs.sleep)
        self.query_one("#happy_bar", ProgressBar).progress = clamp_pct(gs.happiness)

        self.query_one("#pet_box", Static).update(self.render_pet_on_rug(gs))

    def render_pet_on_rug(self, gs: GameState) -> str:
        pet = gs.pet.title()
        if gs.paused:
            mood = "⏸ paused"
        else:
            mood = "💤 sleeping" if gs.sleeping else "🙂 awake"

        rug = (
            "         .-=-=-=-=-=-=-=-.\n"
            "        /  ~ Cozy Rug ~   \\\n"
            "       /___________________\\\n"
        )
        pet_art = f"\n            ({pet})\n            [{mood}]\n"
        hint = "\n(Use the buttons below to move around.)"
        return rug + pet_art + hint

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "go_kitchen":
            self.app.push_screen(KitchenScreen())  # type: ignore[attr-defined]
        elif bid == "go_play":
            self.app.push_screen(PlayScreen())  # type: ignore[attr-defined]
        elif bid == "go_sleep":
            self.app.push_screen(SleepScreen())  # type: ignore[attr-defined]
        elif bid == "go_stats":
            self.app.push_screen(StatsScreen())  # type: ignore[attr-defined]
        elif bid == "go_shop":
            self.app.push_screen(ShopScreen())  # type: ignore[attr-defined]
        elif bid == "go_pause":
            self.app.pause_game()  # type: ignore[attr-defined]


class PauseScreen(Screen):
    CSS = """
    PauseScreen { align: center middle; }
    #card { width: 80; border: round yellow; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #note { color: $text-muted; padding-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Paused", id="title")
            yield Label("Pause penalty applied: Hunger -3, Sleep -3, Happiness -3.\nTimers are stopped while paused.", id="note")
            yield Label("", id="status")
            with Horizontal():
                yield Button("Resume", id="resume", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        gs: GameState = self.app.gs  # type: ignore[attr-defined]
        self.query_one("#status", Label).update(
            f"Now: Hunger {gs.hunger}% | Sleep {gs.sleep}% | Happiness {gs.happiness}%"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "resume":
            self.app.resume_game()  # type: ignore[attr-defined]


class KitchenScreen(Screen):
    CSS = """
    KitchenScreen { align: center middle; }
    #card { width: 88; border: round $accent; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #note { color: $text-muted; padding-bottom: 1; }
    #food_grid { grid-size: 2; grid-gutter: 1 1; padding-top: 1; padding-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Kitchen", id="title")
            yield Label("Buy food from the fridge to raise hunger.", id="note")
            yield Label("", id="kitchen_status")
            yield Static(self.fridge_text(), id="fridge_panel")

            with Grid(id="food_grid"):
                for i, (name, cost, gain) in enumerate(FOODS):
                    yield Button(f"Buy {name} ({cost}) +{gain}%", id=f"buy_food_{i}", variant="success")

            with Horizontal():
                yield Button("Back to Room", id="back")
        yield Footer()

    def fridge_text(self) -> str:
        lines = ["🥶 Fridge Items:"]
        for name, cost, gain in FOODS:
            lines.append(f"  • {name} — {cost} coins (+{gain}% hunger)")
        return "\n" + "\n".join(lines) + "\n"

    def on_mount(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        gs: GameState = self.app.gs  # type: ignore[attr-defined]
        self.query_one("#kitchen_status", Label).update(f"Coins: {gs.coins} | Hunger: {gs.hunger}%")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        gs: GameState = self.app.gs  # type: ignore[attr-defined]

        if bid == "back":
            self.app.pop_screen()
            return

        if bid.startswith("buy_food_"):
            idx = int(bid.removeprefix("buy_food_"))
            name, cost, gain = FOODS[idx]
            if gs.coins < cost:
                self.notify("Not enough coins!", severity="warning")
                return
            gs.coins -= cost
            gs.hunger = clamp_pct(gs.hunger + gain)
            self.notify(f"You bought {name}. Yum!")
            self.refresh_ui()
            self.app._check_leave_condition()  # type: ignore[attr-defined]


class PlayScreen(Screen):
    CSS = """
    PlayScreen { align: center middle; }
    #card { width: 88; border: round $accent; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #info { color: $text-muted; padding-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Play Time", id="title")
            yield Label(
                "Throw toys and train your pet to earn coins and boost happiness.\nNEW: Each play action costs 2% sleep.",
                id="info",
            )
            yield Label("", id="play_status")
            with Horizontal():
                yield Button("Throw Toy", id="throw", variant="success")
                yield Button("Train", id="train", variant="primary")
                yield Button("Back", id="back")
            yield Static("", id="log")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_ui("")

    def best_toy(self, gs: GameState) -> Optional[Toy]:
        return max(gs.toys_owned, key=lambda t: t.coin_reward) if gs.toys_owned else None

    def base_rewards(self, gs: GameState) -> tuple[int, int]:
        toy = self.best_toy(gs)
        if toy is None:
            return (2, 1)
        return (toy.coin_reward, toy.happiness_reward)

    def refresh_ui(self, msg: str) -> None:
        gs: GameState = self.app.gs  # type: ignore[attr-defined]
        toy = self.best_toy(gs)
        toy_name = toy.name if toy else "None"
        self.query_one("#play_status", Label).update(
            f"Coins: {gs.coins} | Happiness: {gs.happiness}% | Sleep: {gs.sleep}% | Best Toy: {toy_name}"
        )
        if msg:
            self.query_one("#log", Static).update(msg)

    def _apply_play_sleep_cost(self, gs: GameState) -> None:
        # NEW MECHANIC: each play action costs 2% sleep
        gs.sleep = clamp_pct(gs.sleep - 2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        gs: GameState = self.app.gs  # type: ignore[attr-defined]

        if bid == "back":
            self.app.pop_screen()
            return

        if bid not in ("throw", "train"):
            return

        coins_gain, happy_gain = self.base_rewards(gs)

        # Apply action + rewards
        if bid == "throw":
            gained_c = coins_gain + 1
            gained_h = max(1, happy_gain)
            gs.coins += gained_c
            gs.happiness = clamp_pct(gs.happiness + gained_h)
            self._apply_play_sleep_cost(gs)
            self.refresh_ui(f"You threw a toy! +{gained_c} coins, +{gained_h}% happiness, -2% sleep.")
        elif bid == "train":
            gained_c = max(1, coins_gain - 1)
            gained_h = happy_gain + 1
            gs.coins += gained_c
            gs.happiness = clamp_pct(gs.happiness + gained_h)
            self._apply_play_sleep_cost(gs)
            self.refresh_ui(f"You trained your pet! +{gained_c} coins, +{gained_h}% happiness, -2% sleep.")

        self.app._check_leave_condition()  # type: ignore[attr-defined]


class SleepScreen(Screen):
    CSS = """
    SleepScreen { align: center middle; }
    #card { width: 88; border: round $accent; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #info { color: $text-muted; padding-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Sleep", id="title")
            yield Label("While sleeping, sleep increases by 1 every 30 seconds.", id="info")
            yield Label("", id="sleep_status")
            with Horizontal():
                yield Button("Start Sleeping", id="start", variant="success")
                yield Button("Wake Up", id="wake", variant="warning")
                yield Button("Back", id="back")
            yield Static("", id="sleep_art")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        gs: GameState = self.app.gs  # type: ignore[attr-defined]
        self.query_one("#sleep_status", Label).update(
            f"Sleep: {gs.sleep}% | Sleeping: {'Yes' if gs.sleeping else 'No'}"
        )
        art = (
            "\n   zZzZz...\n  ( -_-)💤\n  [pet sleeping on the rug]\n"
            if gs.sleeping
            else "\n  (o_o) awake\n  [pet is not sleeping]\n"
        )
        self.query_one("#sleep_art", Static).update(art)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        gs: GameState = self.app.gs  # type: ignore[attr-defined]

        if bid == "back":
            self.app.pop_screen()
            return

        if bid == "start":
            gs.sleeping = True
            self.notify("Your pet fell asleep.")
        elif bid == "wake":
            gs.sleeping = False
            self.notify("Your pet woke up.")

        self.refresh_ui()
        self.app._check_leave_condition()  # type: ignore[attr-defined]


class StatsScreen(Screen):
    CSS = """
    StatsScreen { align: center middle; }
    #card { width: 88; border: round $accent; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #body { padding-top: 1; padding-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Stats", id="title")
            yield Static("", id="body")
            with Horizontal():
                yield Button("Back", id="back")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        gs: GameState = self.app.gs  # type: ignore[attr-defined]
        self.query_one("#body", Static).update(
            "\n".join(
                [
                    f"Pet: {gs.pet.title() if gs.pet else '(none)'}",
                    f"Gender: {gs.gender}",
                    f"Age: {gs.age_minutes} minute(s)",
                    f"Hunger: {gs.hunger}%",
                    f"Sleep: {gs.sleep}%",
                    f"Happiness: {gs.happiness}%",
                    f"Coins: {gs.coins}",
                    f"Toys owned: {len(gs.toys_owned)}",
                    f"Other pets owned (total): {max(0, gs.pets_owned_total - 1)}",
                    f"Eggs owned: {gs.eggs_owned}",
                    f"Paused: {'Yes' if gs.paused else 'No'}",
                ]
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return


class ShopScreen(Screen):
    CSS = """
    ShopScreen { align: center middle; }
    #card { width: 92; border: round $accent; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #note { color: $text-muted; padding-bottom: 1; }
    #shop_status { padding-bottom: 1; }
    #toy_grid { grid-size: 2; grid-gutter: 1 1; padding-top: 1; padding-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Shop", id="title")
            yield Label("Buy toys (better play rewards) or eggs (more pets).", id="note")
            yield Label("", id="shop_status")
            yield Static("", id="shop_list")

            with Grid(id="toy_grid"):
                for toy in TOY_CATALOG:
                    yield Button(f"Buy {toy.name} ({toy.cost})", id=f"buy_toy_{toy.slug}", variant="success")

            yield Button("Buy Egg", id="buy_egg", variant="primary")

            with Horizontal():
                yield Button("Back", id="back")
        yield Footer()

    def next_egg_cost(self, gs: GameState) -> int:
        return EGG_COST_START + (gs.pets_owned_total - 1) * 25

    def on_mount(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        gs: GameState = self.app.gs  # type: ignore[attr-defined]
        egg_cost = self.next_egg_cost(gs)

        self.query_one("#shop_status", Label).update(
            f"Coins: {gs.coins} | Toys: {len(gs.toys_owned)} | Eggs: {gs.eggs_owned}"
        )
        self.query_one("#buy_egg", Button).label = f"Buy Egg ({egg_cost})"

        owned = {t.slug for t in gs.toys_owned}
        lines = ["Toys:"]
        for toy in TOY_CATALOG:
            if toy.slug in owned:
                lines.append(f"  ✅ {toy.name} (owned) — +{toy.coin_reward} coins, +{toy.happiness_reward}% happy")
            else:
                lines.append(f"  🛒 {toy.name} — cost {toy.cost} — +{toy.coin_reward} coins, +{toy.happiness_reward}% happy")
        lines.append("")
        lines.append(f"Egg: 🥚 cost {egg_cost}")
        self.query_one("#shop_list", Static).update("\n".join(lines))

        for toy in TOY_CATALOG:
            btn = self.query_one(f"#buy_toy_{toy.slug}", Button)
            btn.disabled = toy.slug in owned

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        gs: GameState = self.app.gs  # type: ignore[attr-defined]

        if bid == "back":
            self.app.pop_screen()
            return

        if bid.startswith("buy_toy_"):
            toy_slug = bid.removeprefix("buy_toy_")
            toy = next((t for t in TOY_CATALOG if t.slug == toy_slug), None)
            if toy is None:
                return
            if any(t.slug == toy.slug for t in gs.toys_owned):
                self.notify("You already own that toy.", severity="warning")
                return
            if gs.coins < toy.cost:
                self.notify("Not enough coins.", severity="warning")
                return
            gs.coins -= toy.cost
            gs.toys_owned.append(toy)
            self.notify(f"Bought {toy.name}! Play rewards increased.")
            self.refresh_ui()
            return

        if bid == "buy_egg":
            cost = self.next_egg_cost(gs)
            if gs.coins < cost:
                self.notify("Not enough coins for an egg.", severity="warning")
                return
            gs.coins -= cost
            gs.eggs_owned += 1
            gs.pets_owned_total += 1
            self.notify("You bought an egg! (Tracked in Stats.)")
            self.refresh_ui()
            return


class GoodbyeScreen(Screen):
    CSS = """
    GoodbyeScreen { align: center middle; }
    #card { width: 88; border: round red; padding: 1 2; }
    #title { text-style: bold; content-align: center middle; padding-bottom: 1; }
    #msg { padding-bottom: 1; }
    """

    def __init__(self, reason: str) -> None:
        super().__init__()
        self.reason = reason

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="card"):
            yield Label("Goodbye…", id="title")
            yield Label(self.reason, id="msg")
            yield Label("Your pet left an egg behind. Everything will restart.", id="msg")
            yield Button("Restart", id="restart", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "restart":
            self.app.restart_after_goodbye()  # type: ignore[attr-defined]

# ----------------------------
# App
# ----------------------------

class PetGameApp(App):
    TITLE = "Pet TUI Prototype"
    BINDINGS = [("q", "quit", "Quit"), ("p", "pause", "Pause")]

    gs: GameState

    # pacing
    HUNGER_TICK_SECONDS = 60          # -1 hunger each tick
    SLEEP_DECAY_TICK_SECONDS = 120    # -1 sleep each tick (when not sleeping)
    SLEEP_REGEN_TICK_SECONDS = 30     # +1 sleep each tick (when sleeping)
    AGE_TICK_SECONDS = 60             # +1 minute age each tick

    def __init__(self) -> None:
        super().__init__()
        self.gs = GameState()

    def on_mount(self) -> None:
        self.push_screen(PetSelectScreen())
        self._start_timers()

    def _start_timers(self) -> None:
        self.set_interval(self.HUNGER_TICK_SECONDS, self._tick_hunger)
        self.set_interval(self.SLEEP_DECAY_TICK_SECONDS, self._tick_sleep_decay)
        self.set_interval(self.SLEEP_REGEN_TICK_SECONDS, self._tick_sleep_regen)
        self.set_interval(self.AGE_TICK_SECONDS, self._tick_age)

    # NEW: keyboard pause
    def action_pause(self) -> None:
        self.pause_game()

    # NEW: pause mechanics
    def pause_game(self) -> None:
        if self.gs.pet is None:
            return
        # If already paused, do nothing (prevents stacking + repeated penalties)
        if self.gs.paused:
            return

        # Pause penalty: each percentage goes down by 3%
        self.gs.hunger = clamp_pct(self.gs.hunger - 3)
        self.gs.sleep = clamp_pct(self.gs.sleep - 3)
        self.gs.happiness = clamp_pct(self.gs.happiness - 3)

        self.gs.paused = True
        self.push_screen(PauseScreen())
        self._check_leave_condition()
        self._refresh_room_if_present()

    def resume_game(self) -> None:
        if not self.gs.paused:
            return
        self.gs.paused = False
        # pop PauseScreen
        self.pop_screen()
        self._refresh_room_if_present()

    def start_new_run(self, pet: str) -> None:
        self.gs.reset_for_new_pet(pet)
        self.pop_screen()
        self.push_screen(RoomScreen())

    def restart_after_goodbye(self) -> None:
        self.gs.eggs_owned += 1
        while self.screen_stack:
            try:
                self.pop_screen()
            except Exception:
                break
        self.push_screen(PetSelectScreen())

    # timers: stop ticking while paused
    def _tick_hunger(self) -> None:
        if self.gs.pet is None or self.gs.paused:
            return
        self.gs.hunger = clamp_pct(self.gs.hunger - 1)
        self._check_leave_condition()
        self._refresh_room_if_present()

    def _tick_sleep_decay(self) -> None:
        if self.gs.pet is None or self.gs.paused:
            return
        if not self.gs.sleeping:
            self.gs.sleep = clamp_pct(self.gs.sleep - 1)
        self._check_leave_condition()
        self._refresh_room_if_present()

    def _tick_sleep_regen(self) -> None:
        if self.gs.pet is None or self.gs.paused:
            return
        if self.gs.sleeping:
            self.gs.sleep = clamp_pct(self.gs.sleep + 1)
        self._refresh_room_if_present()

    def _tick_age(self) -> None:
        if self.gs.pet is None or self.gs.paused:
            return
        self.gs.age_minutes += 1
        self._refresh_room_if_present()

    def _refresh_room_if_present(self) -> None:
        for screen in reversed(self.screen_stack):
            if isinstance(screen, RoomScreen):
                screen.refresh_ui()
                break

    def _check_leave_condition(self) -> None:
        if self.gs.pet is None:
            return

        if self.gs.hunger <= 10 or self.gs.sleep <= 10:
            parts = []
            if self.gs.hunger <= 10:
                parts.append("I'm too hungry…")
            if self.gs.sleep <= 10:
                parts.append("I'm too tired…")
            reason = " ".join(parts) + " Goodbye!"

            if not any(isinstance(s, GoodbyeScreen) for s in self.screen_stack):
                self.push_screen(GoodbyeScreen(reason))

            # End this run
            self.gs.pet = None
            self.gs.sleeping = False
            self.gs.paused = False

def main() -> None:
    PetGameApp().run()

if __name__ == "__main__":
    main()
