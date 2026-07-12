import pygame
import sys
import random
import os
import json
from pygame.locals import *

# Asset paths - Update these to match your file structure
ASSETS_DIR = "assets"  # Base directory for all assets
FOOD_DIR = os.path.join(ASSETS_DIR, "food")
CHAR_DIR = os.path.join(ASSETS_DIR, "characters")
BG_DIR = os.path.join(ASSETS_DIR, "backgrounds")
UI_DIR = os.path.join(ASSETS_DIR, "ui")

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1800
SCREEN_HEIGHT = 900
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Game states
MENU = 0
CHARACTER_SELECT = 1
CATCHING = 2
SERVING = 3
GAME_OVER = 4
SERVING_FEEDBACK = 5  # New state for showing serve results

# Player data
player_data = {
    "character": "",
    "coins": 0,
    "unlocked_foods": ["toast", "burger", "egg", "sushi", "pizza"],
    "kitchen_level": 1,
    "wrong_orders": 0
}

# --- Dimensions for Assets (adjust if your assets are different) ---
PLAYER_CHARACTER_WIDTH = 80
PLAYER_CHARACTER_HEIGHT = 120
PLATE_WIDTH = 160
PLATE_HEIGHT = 40
FOOD_ITEM_HEIGHT_ESTIMATE = 35
FOOD_SPAWN_Y_OFFSET = -60

# --- Stacking Visuals ---
PLATE_FIRST_ITEM_OFFSET_Y = 5
# How much of the *previous* item is effectively overlapped by the current item's placement.
# Larger value = more overlap / tighter stack.
# e.g., 0.6 means the current food's bottom is placed 60% of the way down the previous food's height, from its top.
STACKING_OVERLAP_FACTOR = 0.6  # MODIFIED: Increased from 0.4 to 0.6 for tighter stacking


class Button:
    def __init__(self, x, y, width, height, text, color=GRAY, hover_color=BLUE, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=10)

        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, pos: tuple[int, int]):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos: tuple[int, int], event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            print(f"Button '{self.text}' clicked.")
            return True
        return False


class Food:
    def __init__(self, food_type, x, y=FOOD_SPAWN_Y_OFFSET):
        self.food_type = food_type
        self.speed = random.randint(3, 6)
        self.image = None
        self.load_image()
        if self.image:
            self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        # print(f"Food '{self.food_type}' created at ({x}, {y}) with speed {self.speed}") # Less verbose

    def load_image(self) -> None:
        # try:
        image_path = os.path.join(FOOD_DIR, f"{self.food_type}.png")
        original_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(original_image, (256, 256))
        # except pygame.error:
        #     print(f"Could not load image for {self.food_type}. Using placeholder.")
        #     self.image = pygame.Surface((40, 40))
        #     self.image.set_colorkey(BLACK)  # Make black transparent for placeholder
        #     self.image.fill(GRAY)  # Fallback fill color
        #     # Placeholder drawings (optional if you have actual placeholders)
        #     if self.food_type == "toast":
        #         pygame.draw.rect(self.image, (210, 180, 140), (5, 5, 30, 30))
        #     elif self.food_type == "burger":
        #         pygame.draw.circle(self.image, (139, 69, 19), (20, 20), 15)
        #     elif self.food_type == "egg":
        #         pygame.draw.ellipse(self.image, (255, 255, 224), (5, 10, 30, 20))
        #     elif self.food_type == "sushi":
        #         pygame.draw.rect(self.image, (200, 200, 200), (5, 10, 30, 20))
        #         pygame.draw.circle(self.image, (255, 100, 100), (20, 20), 5)
        #     elif self.food_type == "pizza":
        #         pygame.draw.polygon(self.image, (255, 215, 0), [(0, 0), (40, 0), (20, 40)])

    def update(self):
        self.rect.y += self.speed

    def draw(self, screen):
        if self.image:  # Ensure image is loaded
            screen.blit(self.image, self.rect)


class Plate:
    def __init__(self, x: int, y: int, character_name=None):
        self.speed = 10
        self.stacked_food = []
        self.character_name = character_name
        self.character_image = None
        self.image = None  # Initialize image attribute
        self.load_image()
        if self.image:  # Check if plate image loaded
            self.rect = self.image.get_rect()
            self.rect.x = x
            self.rect.y = y
        else:  # Fallback if plate image fails to load
            self.rect = pygame.Rect(x, y, PLATE_WIDTH, PLATE_HEIGHT)

        # print(f"Plate initialized for character: {character_name}") # Less verbose

    def load_image(self):
        # try:
        plate_path = os.path.join(UI_DIR, "plate.png")
        self.image = pygame.image.load(plate_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (PLATE_WIDTH, PLATE_HEIGHT))
        # except pygame.error:
        #     print("Could not load plate image. Using placeholder.")
        #     self.image = pygame.Surface((PLATE_WIDTH, PLATE_HEIGHT), pygame.SRCALPHA)  # Use SRCALPHA for transparency
        #     self.image.fill((200, 200, 200, 150))  # Semi-transparent gray
        #     pygame.draw.rect(self.image, WHITE, self.image.get_rect(), 3)

        if self.character_name:
            # try:
            char_path = os.path.join(CHAR_DIR, f"{self.character_name}.png")
            self.character_image = pygame.image.load(char_path).convert_alpha()
            self.character_image = pygame.transform.scale(self.character_image,
                                                          (PLAYER_CHARACTER_WIDTH, PLAYER_CHARACTER_HEIGHT))
            # except pygame.error:
            #     print(f"Could not load character image for {self.character_name}. Using placeholder character.")
            #     self.character_image = pygame.Surface((PLAYER_CHARACTER_WIDTH, PLAYER_CHARACTER_HEIGHT))
            #     self.character_image.fill(BLUE)  # Placeholder color

    def move(self, direction):
        if direction == "left" and self.rect.left > 0:
            self.rect.x -= self.speed
        elif direction == "right" and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

    def update_stacked_food_positions(self):
        if not self.stacked_food:
            return

        first_food = self.stacked_food[0]
        first_food.rect.centerx = self.rect.centerx
        first_food.rect.bottom = self.rect.top + PLATE_FIRST_ITEM_OFFSET_Y

        for i in range(1, len(self.stacked_food)):
            previous_food = self.stacked_food[i - 1]
            current_food = self.stacked_food[i]
            current_food.rect.centerx = self.rect.centerx

            # overlap_pixels defines how far the bottom of the current_food is placed
            # relative to the top of the previous_food.
            # A larger STACKING_OVERLAP_FACTOR means current_food.rect.bottom is further down,
            # thus more of the previous_food is covered (more overlap).
            overlap_pixels = (previous_food.image.get_height() * STACKING_OVERLAP_FACTOR)
            current_food.rect.bottom = previous_food.rect.top + overlap_pixels

    def draw(self, screen):
        char_rect_x = self.rect.centerx - PLAYER_CHARACTER_WIDTH // 2
        char_rect_y = self.rect.bottom - PLAYER_CHARACTER_HEIGHT + PLATE_HEIGHT * 0.6

        if self.character_image:
            screen.blit(self.character_image, (char_rect_x, char_rect_y))

        if self.image:  # Draw plate if loaded
            screen.blit(self.image, self.rect)

        for food_item in self.stacked_food:
            food_item.draw(screen)


class Customer:
    def __init__(self, x: int, y: int, order_foods_list):
        self.order = []
        self.patience = 100
        self.patience_drop_interval = FPS * 3  # Drop every 10 seconds (FPS frames)
        self.patience_drop_timer = 0
        self.patience_drop_amount = 10
        self.image = None  # Initialize image attribute
        self.load_image()
        if self.image:  # Check if customer image loaded
            self.rect = self.image.get_rect()
        else:  # Fallback if image fails
            self.rect = pygame.Rect(0, 0, PLAYER_CHARACTER_WIDTH, PLAYER_CHARACTER_HEIGHT)
        self.rect.x = x
        self.rect.y = y
        self.speech_bubble_rect = pygame.Rect(self.rect.centerx - 70, self.rect.top - 70, 140, 60)
        self.generate_order(order_foods_list)
        # print(f"Customer created at ({x},{y}) with order: {self.order}") # Less verbose

    def load_image(self):
        # try:
        customer_files = [f for f in os.listdir(CHAR_DIR) if f.startswith("customer") and f.endswith(".png")]
        if customer_files:
            customer_file = random.choice(customer_files)
            image_path = os.path.join(CHAR_DIR, customer_file)
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (PLAYER_CHARACTER_WIDTH, PLAYER_CHARACTER_HEIGHT))
        else:
            raise FileNotFoundError("No customer*.png files found.")
        # except (pygame.error, FileNotFoundError, OSError) as e:
        #     print(f"Could not load customer image: {e}. Using placeholder.")
        #     self.image = pygame.Surface((PLAYER_CHARACTER_WIDTH, PLAYER_CHARACTER_HEIGHT))
        #     self.image.fill((180, 120, 120))

    def generate_order(self, order_foods_list):
        if not order_foods_list:
            self.order = ["toast"]
        else:
            order_size = random.randint(1, min(3, len(order_foods_list)))
            self.order = random.sample(order_foods_list, order_size)

    def update(self):
        # Add this at the very beginning of the method
        # print(
        #     f"Customer ID {id(self)} updating. Timer: {self.patience_drop_timer}, Patience: {self.patience}, Interval: {self.patience_drop_interval}")

        if self.patience > 0:
            self.patience_drop_timer += 1
            if self.patience_drop_timer >= self.patience_drop_interval:
                # print(
                #     f"Customer ID {id(self)} MET PATIENCE DROP CONDITION! Timer: {self.patience_drop_timer}")  # Key print
                self.patience -= self.patience_drop_amount
                self.patience_drop_timer = 0
                if self.patience < 0:
                    self.patience = 0

    def draw(self, screen, font):
        if self.image:  # Draw customer if loaded
            screen.blit(self.image, self.rect)

        # Speech bubble and order
        pygame.draw.ellipse(screen, WHITE, self.speech_bubble_rect)
        pygame.draw.ellipse(screen, BLACK, self.speech_bubble_rect, 2)
        order_text = ", ".join(self.order)
        text_surface = font.render(order_text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.speech_bubble_rect.center)
        screen.blit(text_surface, text_rect)

        # Patience bar
        meter_width = self.rect.width
        meter_height = 8
        patience_bar_x = self.rect.left
        patience_bar_y = self.rect.top - meter_height - 5
        pygame.draw.rect(screen, GRAY, (patience_bar_x, patience_bar_y, meter_width, meter_height))
        current_patience_width = (self.patience / 100) * meter_width
        patience_color = GREEN if self.patience > 60 else YELLOW if self.patience > 30 else RED
        pygame.draw.rect(screen, patience_color, (patience_bar_x, patience_bar_y, current_patience_width, meter_height))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Stack & Serve - Restaurant Rush!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 30)
        self.small_font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 60)
        self.ui_font = pygame.font.SysFont(None, 28)

        self.state = MENU
        self.load_backgrounds()

        self.start_button = Button(SCREEN_WIDTH // 2 - 100, 200, 200, 50, "Start Game")
        self.quit_button = Button(SCREEN_WIDTH // 2 - 100, 270, 200, 50, "Quit")
        self.sam_button = Button(SCREEN_WIDTH // 2 - 175, 300, 150, 50, "Sam")
        self.jack_button = Button(SCREEN_WIDTH // 2 + 25, 300, 150, 50, "Jack")

        self.plate = None
        self.foods = []
        self.food_spawn_timer = 0
        self.food_spawn_interval = 60

        self.serve_action_button = Button(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT - 70, 150, 50, "Serve Order!")

        # For serving feedback
        self.serve_feedback_messages = []
        self.serve_feedback_ok_button = Button(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT * 0.6, 150, 50,
                                               "OK")  # Centered more
        self.next_state_after_feedback = None

        self.current_customer_for_round = None
        self.current_order_to_catch = []
        self.required_food_spawn_indices = []
        self.customer_patience_timer = 0  # Timer to decrease customer patience

        self.replay_button = Button(SCREEN_WIDTH // 2 - 100, 350, 200, 50, "Play Again")
        self.load_game()
        print("Game initialized. Current state: MENU")

    def load_backgrounds(self):
        print("Loading backgrounds...")
        # try:
        self.catching_bg = pygame.transform.scale(
            pygame.image.load(os.path.join(BG_DIR, "catching_bg.png")).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.serving_bg = pygame.transform.scale(
            pygame.image.load(os.path.join(BG_DIR, "serving_bg.png")).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.menu_bg = pygame.transform.scale(pygame.image.load(os.path.join(BG_DIR, "menu_bg.png")).convert(),
                                              (SCREEN_WIDTH, SCREEN_HEIGHT))
        # except pygame.error as e:
        #     print(f"Could not load background images: {e}. Using placeholders.")
        #     self.catching_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        #     self.catching_bg.fill((200, 230, 250))  # Removed semicolon
        #     self.serving_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        #     self.serving_bg.fill((230, 210, 200))  # Removed semicolon
        #     self.menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        #     self.menu_bg.fill((220, 220, 240))  # Removed semicolon
        print("Backgrounds loaded.")

    def load_game(self):
        save_path = "save_data.json"
        print(f"Attempting to load game data from {save_path}...")
        try:
            if os.path.exists(save_path):
                with open(save_path, 'r') as file:
                    global player_data  # Ensure global scope is intended for modification
                    loaded_data = json.load(file)
                    player_data["coins"] = loaded_data.get("coins", 0)
                    player_data["unlocked_foods"] = loaded_data.get("unlocked_foods",
                                                                    ["toast", "banana", "burger", "egg", "sushi", "pizza"])
                    player_data["kitchen_level"] = loaded_data.get("kitchen_level", 1)
                    player_data["wrong_orders"] = loaded_data.get("wrong_orders", 0)
                    print(f"Game data loaded: Coins={player_data['coins']}, WrongOrders={player_data['wrong_orders']}")
            else:
                print("No save file found. Using default player data.")
        except Exception as e:
            print(f"Error loading game data: {e}. Using default values.")
            self.reset_player_stats(full_reset=True)

    def save_game(self)->None:
        save_path = "save_data.json"
        print(f"Saving game data to {save_path}...")
        try:
            with open(save_path, 'w') as file:
                data_to_save = {
                    "coins": player_data["coins"],
                    "unlocked_foods": player_data["unlocked_foods"],
                    "kitchen_level": player_data["kitchen_level"],
                    "wrong_orders": player_data["wrong_orders"]
                }
                json.dump(data_to_save, file, indent=4)
                print(f"Game data saved: Coins={player_data['coins']}, WrongOrders={player_data['wrong_orders']}")
        except Exception as e:
            print(f"Error saving game data: {e}")

    def start_new_round(self):
        print("\n--- Starting New Round ---")
        if not player_data["unlocked_foods"]:
            print("Error: No unlocked foods to generate an order!")
            player_data["unlocked_foods"] = ["toast"]

        self.current_customer_for_round = Customer(SCREEN_WIDTH * 0.75, SCREEN_HEIGHT - PLAYER_CHARACTER_HEIGHT - 80,
                                                   player_data["unlocked_foods"])
        self.current_order_to_catch = self.current_customer_for_round.order[:]
        self.required_food_spawn_indices = list(range(len(self.current_order_to_catch)))
        random.shuffle(self.required_food_spawn_indices)
        self.customer_patience_timer = 0  # Reset patience timer for the new round

        print(f"New customer order: {self.current_order_to_catch}")

        plate_y_position = SCREEN_HEIGHT - PLATE_HEIGHT - (PLAYER_CHARACTER_HEIGHT * 0.30)
        self.plate = Plate(SCREEN_WIDTH // 2 - PLATE_WIDTH // 2, plate_y_position,
                           character_name=player_data["character"])
        self.foods = []
        self.food_spawn_timer = 0

        self.state = CATCHING
        print(f"Transitioned to CATCHING state for order: {self.current_order_to_catch}")

    def run(self) -> None:
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            events = pygame.event.get()  # Get all events once per frame

            for event in events:
                if event.type == QUIT:
                    self.save_game()
                    running = False

                if self.state == MENU:
                    self.start_button.check_hover(mouse_pos)
                    self.quit_button.check_hover(mouse_pos)
                    if self.start_button.is_clicked(mouse_pos, event):
                        self.state = CHARACTER_SELECT
                        print("State changed to CHARACTER_SELECT")
                    if self.quit_button.is_clicked(mouse_pos, event):
                        self.save_game()
                        running = False

                elif self.state == CHARACTER_SELECT:
                    self.sam_button.check_hover(mouse_pos)
                    self.jack_button.check_hover(mouse_pos)
                    character_selected = None
                    if self.sam_button.is_clicked(mouse_pos, event):
                        character_selected = "sam"
                    if self.jack_button.is_clicked(mouse_pos, event):
                        character_selected = "jack"

                    if character_selected:
                        player_data["character"] = character_selected
                        print(f"Character '{character_selected}' selected.")
                        self.reset_player_stats(full_reset=False)
                        self.start_new_round()

                elif self.state == CATCHING:
                    self.serve_action_button.check_hover(mouse_pos)
                    activate_serve = False
                    if self.serve_action_button.is_clicked(mouse_pos, event):
                        activate_serve = True
                    if event.type == KEYDOWN and event.key == K_SPACE:  # MODIFIED: Space bar activation
                        activate_serve = True

                    if activate_serve and self.plate and self.plate.stacked_food:
                        print("Serve action triggered. Transitioning to SERVING state.")
                        self.state = SERVING
                        if self.current_customer_for_round:
                            self.current_customer_for_round.patience = 100  # Reset patience for this attempt

                elif self.state == SERVING:
                    if event.type == KEYDOWN and event.key == K_SPACE:
                        print("SPACE pressed in SERVING state. Attempting to serve customer.")
                        self.process_served_order()

                elif self.state == SERVING_FEEDBACK:  # MODIFIED: Handle SERVING_FEEDBACK state
                    self.serve_feedback_ok_button.check_hover(mouse_pos)
                    if self.serve_feedback_ok_button.is_clicked(mouse_pos, event) or (event.type == KEYDOWN and event.key == K_SPACE):
                        print("Serve feedback OK button clicked.")
                        if self.next_state_after_feedback == CATCHING:
                            self.start_new_round()
                        elif self.next_state_after_feedback == GAME_OVER:
                            self.state = GAME_OVER
                            print("State changed to GAME_OVER.")
                        else:  # Fallback, should ideally not happen if next_state_after_feedback is set
                            self.state = MENU


                elif self.state == GAME_OVER:
                    self.replay_button.check_hover(mouse_pos)
                    if self.replay_button.is_clicked(mouse_pos, event):
                        print("Replay button clicked.")
                        self.reset_player_stats(full_reset=True)
                        self.state = MENU
                        print("State changed to MENU for replay.")

            # Game logic updates
            if self.state == CATCHING:
                self.update_catching()
            # Removed the separate patience update here, it's now in update_catching

            # Drawing
            self.draw_game_screen()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def update_catching(self):
        if not self.plate or not self.current_customer_for_round:
            return

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]: self.plate.move("left")
        if keys[K_RIGHT]: self.plate.move("right")

        self.plate.update_stacked_food_positions()

        self.food_spawn_timer += 1
        if self.food_spawn_timer >= self.food_spawn_interval:
            self.spawn_food_for_order()
            self.food_spawn_timer = 0

        for food in self.foods[:]:
            food.update()
            if self.plate.rect.colliderect(food.rect) and \
                    food.rect.bottom > self.plate.rect.top and \
                    food.rect.centery < self.plate.rect.bottom + food.image.get_height() * 0.5:  # Allow slightly more lenient catch vertically
                if len(self.plate.stacked_food) < 5:
                    self.foods.remove(food)
                    self.plate.stacked_food.append(food)
                    self.plate.update_stacked_food_positions()
                    # print(f"Caught: {food.food_type}. Stack: {[f.food_type for f in self.plate.stacked_food]}") # Less verbose
                else:
                    # print(f"Plate full, missed {food.food_type}") # Less verbose
                    self.foods.remove(food)
            elif food.rect.top > SCREEN_HEIGHT:
                self.foods.remove(food)
                # print(f"Food missed: {food.food_type}") # Less verbose

        # Update customer patience in the CATCHING state
        self.current_customer_for_round.update()
        if self.current_customer_for_round.patience <= 0:
            print("Customer lost patience during catching!")
            player_data["wrong_orders"] += 1

            self.serve_feedback_messages = [
                "Oh no! The customer lost patience while waiting!",
                f"That's a strike! Strikes: {player_data['wrong_orders']}/3"
            ]

            if player_data["wrong_orders"] >= 3:
                self.next_state_after_feedback = GAME_OVER
                self.serve_feedback_messages.append("Too many strikes... Game Over.")
            else:
                self.next_state_after_feedback = CATCHING
                self.serve_feedback_messages.append("Let's focus on the next customer!")

            self.plate.stacked_food = []  # Clear plate
            self.state = SERVING_FEEDBACK
            print(f"Transitioning to SERVING_FEEDBACK due to impatience. Next state: {self.next_state_after_feedback}")

    def draw_game_screen(self):
        current_bg = self.menu_bg
        if self.state == CATCHING:
            current_bg = self.catching_bg
        elif self.state in (SERVING, SERVING_FEEDBACK):
            current_bg = self.serving_bg
        elif self.state == GAME_OVER:
            current_bg = self.menu_bg
        self.screen.blit(current_bg, (0, 0))

        if self.state == MENU:
            title_text = self.large_font.render("Stack & Serve", True, BLACK)
            self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
            self.start_button.draw(self.screen, self.font)
            self.quit_button.draw(self.screen, self.font)
            self.draw_instructions(SCREEN_WIDTH // 2, 350, self.small_font)

        elif self.state == CHARACTER_SELECT:
            title_text = self.large_font.render("Choose Your Character", True, BLACK)
            self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
            self.sam_button.draw(self.screen, self.font)
            self.jack_button.draw(self.screen, self.font)

        elif self.state == CATCHING:
            if self.plate: self.plate.draw(self.screen)
            for food_item in self.foods: food_item.draw(self.screen)
            if self.current_customer_for_round:
                self.current_customer_for_round.draw(self.screen, self.font) # Draw customer on catching screen

            if self.current_order_to_catch:
                order_display_text = "Catch This Order: " + ", ".join(self.current_order_to_catch)
                text_surf = self.ui_font.render(order_display_text, True, BLACK, WHITE)
                text_rect = text_surf.get_rect(centerx=SCREEN_WIDTH // 2, y=10)
                self.screen.blit(text_surf, text_rect)

            self.serve_action_button.draw(self.screen, self.font)

            stack_text = self.font.render(f"Stacked: {len(self.plate.stacked_food) if self.plate else 0}/5", True,
                                          BLACK)
            self.screen.blit(stack_text, (20, 20))
            coins_text = self.font.render(f"Coins: {player_data['coins']}", True, BLACK)
            self.screen.blit(coins_text, (20, 50))
            wrong_text = self.font.render(f"Strikes: {player_data['wrong_orders']}/3", True, RED)
            self.screen.blit(wrong_text, (20, 80))
            # MODIFIED: Display patience score
            if self.current_customer_for_round:
                patience_val = max(0, int(self.current_customer_for_round.patience))  # Ensure non-negative
                patience_text = self.font.render(f"Patience: {patience_val}", True, BLACK)
                self.screen.blit(patience_text, (20, 110))


        elif self.state == SERVING:
            if self.current_customer_for_round:
                self.current_customer_for_round.rect.centerx = SCREEN_WIDTH // 2
                self.current_customer_for_round.speech_bubble_rect.centerx = SCREEN_WIDTH // 2
                # Adjust customer Y position to be more central on serving screen
                self.current_customer_for_round.rect.centery = SCREEN_HEIGHT // 2 - PLAYER_CHARACTER_HEIGHT
                self.current_customer_for_round.speech_bubble_rect.bottom = self.current_customer_for_round.rect.top - 10

                self.current_customer_for_round.draw(self.screen, self.font)

            if self.plate and self.plate.stacked_food:
                inventory_title = self.font.render("Your Stack to Serve:", True, BLACK)
                inventory_title_rect = inventory_title.get_rect(centerx=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT - 200)
                self.screen.blit(inventory_title, inventory_title_rect)

                food_names = [f.food_type for f in self.plate.stacked_food]
                inventory_text_str = ", ".join(food_names) or "Empty"

                # Draw stacked food images for visual confirmation
                temp_plate_x = SCREEN_WIDTH // 2 - PLATE_WIDTH // 2
                temp_plate_y = SCREEN_HEIGHT - 180  # Position for display

                # Create a temporary display plate centered
                display_plate_rect = pygame.Rect(SCREEN_WIDTH // 2 - PLATE_WIDTH // 2, temp_plate_y + 20, PLATE_WIDTH,
                                                 PLATE_HEIGHT)
                pygame.draw.rect(self.screen,
                                 (200, 200, 200),
                                 display_plate_rect, 0, 5)  # Simple plate visual


                current_y_offset = display_plate_rect.top + PLATE_FIRST_ITEM_OFFSET_Y
                for i, food_obj in enumerate(self.plate.stacked_food):
                    img_copy = food_obj.image.copy()

                    img_rect = img_copy.get_rect(centerx=display_plate_rect.centerx)
                    if i == 0:
                        img_rect.bottom = current_y_offset
                    else:
                        prev_img_height = self.plate.stacked_food[i - 1].image.get_height()
                        overlap = prev_img_height * .25 # STACKING_OVERLAP_FACTOR
                        img_rect.bottom = current_y_offset - prev_img_height + overlap  # current_y_offset becomes top of prev

                    self.screen.blit(img_copy, img_rect)
                    current_y_offset = img_rect.top  # for next item to stack above

            serve_prompt = self.font.render("Press SPACE to Serve!", True, BLACK, YELLOW)
            prompt_rect = serve_prompt.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 30)
            self.screen.blit(serve_prompt, prompt_rect)

            coins_text = self.font.render(f"Coins: {player_data['coins']}", True, BLACK)
            self.screen.blit(coins_text, (20, 20))  # Moved stats to top-left for consistency
            wrong_text = self.font.render(f"Strikes: {player_data['wrong_orders']}/3", True, RED)
            self.screen.blit(wrong_text, (20, 50))

        elif self.state == SERVING_FEEDBACK:  # MODIFIED: Draw SERVING_FEEDBACK screen
            feedback_title_text = "Order Result"
            title_surf = self.large_font.render(feedback_title_text, True, BLACK)
            title_rect = title_surf.get_rect(centerx=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT * 0.2)
            self.screen.blit(title_surf, title_rect)

            y_offset = SCREEN_HEIGHT * 0.35
            line_height = self.font.get_linesize() * 1.5
            for i, msg in enumerate(self.serve_feedback_messages):
                msg_surf = self.font.render(msg, True, BLACK)
                msg_rect = msg_surf.get_rect(centerx=SCREEN_WIDTH // 2, y=y_offset + i * line_height)
                self.screen.blit(msg_surf, msg_rect)

            self.serve_feedback_ok_button.rect.centerx = SCREEN_WIDTH // 2
            self.serve_feedback_ok_button.rect.centery = y_offset + len(self.serve_feedback_messages) * line_height + 60
            self.serve_feedback_ok_button.draw(self.screen, self.font)

            # Display current coins and strikes
            coins_text = self.font.render(f"Total Coins: {player_data['coins']}", True, BLACK)
            coins_rect = coins_text.get_rect(centerx=SCREEN_WIDTH // 2, y=title_rect.bottom + 20)
            self.screen.blit(coins_text, coins_rect)

            wrong_text = self.font.render(f"Strikes: {player_data['wrong_orders']}/3", True,
                                          RED if player_data['wrong_orders'] > 0 else BLACK)
            wrong_rect = wrong_text.get_rect(centerx=SCREEN_WIDTH // 2, y=coins_rect.bottom + 10)
            self.screen.blit(wrong_text, wrong_rect)


        elif self.state == GAME_OVER:
            title_text = self.large_font.render("Game Over!", True, RED)
            score_text = self.font.render(f"Final Coins: {player_data['coins']}", True, BLACK)
            self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 200))
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 280))
            self.replay_button.draw(self.screen, self.font)


        # Invisible?
        # fps_value = self.clock.get_fps()
        # fps_text_surface = self.small_font.render(f"FPS: {fps_value:.2f}", True, BLACK)
        # self.screen.blit(fps_text_surface, (SCREEN_WIDTH - 120, 100))  # Adjust position as needed

    def draw_instructions(self, x_center, y_start, font_to_use):
        instructions = [
            "How to Play:",
            "1. Catch falling food (LEFT/RIGHT arrows) to match the displayed order.",
            "2. Stack up to 5 items. Click 'Serve Order!' or Press SPACE when ready.",
            "3. On the serving screen, press SPACE to give food to the customer.",
            "4. Match their order perfectly to earn coins!",
            "5. Three wrong orders (strikes) or impatient customers lead to Game Over.",
        ]
        for i, line in enumerate(instructions):
            text_surface = font_to_use.render(line, True, BLACK)
            text_rect = text_surface.get_rect(centerx=x_center, y=y_start + i * (font_to_use.get_linesize() * 1.1))
            self.screen.blit(text_surface, text_rect)

    def spawn_food_for_order(self):
        if not self.current_order_to_catch:
            # print("Warning: No current order to spawn food for.") # Less verbose
            return

        food_type_to_spawn = None
        if self.required_food_spawn_indices:
            food_index_to_spawn = self.required_food_spawn_indices.pop(0)
            food_type_to_spawn = self.current_order_to_catch[food_index_to_spawn]
            # print(f"Spawning required: {food_type_to_spawn}") # Less verbose
        else:
            if random.random() < 0.7:
                food_type_to_spawn = random.choice(self.current_order_to_catch)
                # print(f"Re-spawning order item: {food_type_to_spawn}") # Less verbose
            else:
                food_type_to_spawn = random.choice(player_data["unlocked_foods"])
                # print(f"Spawning distractor: {food_type_to_spawn}") # Less verbose

        if food_type_to_spawn:
            x_pos = random.randint(50, SCREEN_WIDTH - 90)
            self.foods.append(Food(food_type_to_spawn, x_pos))

    def process_served_order(self):
        if not self.current_customer_for_round or not self.plate:
            print("Error: No customer or plate to process order.")
            # This case should ideally not be reached if button/key is disabled without plate/food
            if player_data["wrong_orders"] < 3:
                self.next_state_after_feedback = CATCHING
                self.serve_feedback_messages = ["Error processing order. Moving to next round."]
            else:
                self.next_state_after_feedback = GAME_OVER
                self.serve_feedback_messages = ["Error processing order. Game Over."]
            self.state = SERVING_FEEDBACK
            return

        player_stack_types = [food.food_type for food in self.plate.stacked_food]
        customer_order_types = self.current_customer_for_round.order

        print(f"Processing Served Order. Player: {player_stack_types}, Customer: {customer_order_types}")
        self.serve_feedback_messages = []  # Clear previous

        if player_stack_types == customer_order_types:
            coins_earned = len(customer_order_types) * 10
            player_data["coins"] += coins_earned
            self.serve_feedback_messages.append(f"Perfect Match! +{coins_earned} coins!")
            self.serve_feedback_messages.append("Great job, Chef!")
            self.next_state_after_feedback = CATCHING
        else:
            player_data["wrong_orders"] += 1
            self.serve_feedback_messages.append("Oops! That's not the right order.")
            self.serve_feedback_messages.append(f"Strike {player_data['wrong_orders']} of 3.")
            if player_data["wrong_orders"] >= 3:
                self.serve_feedback_messages.append("Three strikes... Game Over!")
                self.next_state_after_feedback = GAME_OVER
            else:
                self.serve_feedback_messages.append("Try again with the next customer!")
                self.next_state_after_feedback = CATCHING

        self.plate.stacked_food = []  # Clear plate
        self.state = SERVING_FEEDBACK
        print(f"Transitioning to SERVING_FEEDBACK. Next state will be: {self.next_state_after_feedback}")

    def reset_player_stats(self, full_reset=True):
        print(f"Resetting player stats. Full reset: {full_reset}")
        player_data["coins"] = 0
        player_data["wrong_orders"] = 0
        if full_reset:
            player_data["unlocked_foods"] = ["toast", "burger", "egg", "sushi", "pizza"]
            player_data["kitchen_level"] = 1
            # player_data["character"] = "" # Keep character if not full reset from game over
        print(f"Stats after reset: Coins={player_data['coins']}, WrongOrders={player_data['wrong_orders']}")


def create_asset_directories() -> None:
    directories = [ASSETS_DIR, FOOD_DIR, CHAR_DIR, BG_DIR, UI_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")


if __name__ == "__main__":
    create_asset_directories()
    print("\n--- Asset Directory Structure & Required Files ---")
    print(f"IMPORTANT: Place your game assets in subdirectories of '{os.path.abspath(ASSETS_DIR)}'")
    print(f"  - Food PNGs (e.g., toast.png, burger.png) -> '{os.path.abspath(FOOD_DIR)}'")
    print(f"  - Character PNGs (sam.png, jack.png, customer_*.png) -> '{os.path.abspath(CHAR_DIR)}'")
    print(f"  - Background PNGs (menu_bg.png, catching_bg.png, serving_bg.png) -> '{os.path.abspath(BG_DIR)}'")
    print(f"  - UI PNGs (plate.png) -> '{os.path.abspath(UI_DIR)}'")
    print("--- Starting game... ---\n")

    game = Game()
    game.run()