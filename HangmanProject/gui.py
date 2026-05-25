import pygame
import pygame.freetype
import os
from game_logic import HangmanGame
from word_bank import get_random_word, get_config


# ──────────────────────────────────────────────────────────────────────────────
# THEME & COLOR PALETTES (Light & Dark Mode)
# ──────────────────────────────────────────────────────────────────────────────

# Dark Mode (Premium Dark Mode - RGB tuples)
DARK_BACKGROUND = (18, 18, 24)
DARK_PANEL = (30, 30, 42)
DARK_BUTTON_HOVER = (45, 45, 65)
DARK_TEXT_PRIMARY = (240, 240, 245)
DARK_ACCENT_SUCCESS = (0, 200, 115)
DARK_ERROR_GALLOWS = (239, 68, 68)

# Light Mode (Clean, readable light palette)
LIGHT_BACKGROUND = (245, 245, 250)
LIGHT_PANEL = (230, 230, 240)
LIGHT_BUTTON_HOVER = (210, 210, 230)
LIGHT_TEXT_PRIMARY = (30, 30, 40)
LIGHT_ACCENT_SUCCESS = (0, 150, 80)
LIGHT_ERROR_GALLOWS = (220, 40, 40)

# Theme dictionary for easy switching
THEMES = {
    "dark": {
        "bg": DARK_BACKGROUND,
        "panel": DARK_PANEL,
        "hover": DARK_BUTTON_HOVER,
        "text": DARK_TEXT_PRIMARY,
        "success": DARK_ACCENT_SUCCESS,
        "error": DARK_ERROR_GALLOWS,
    },
    "light": {
        "bg": LIGHT_BACKGROUND,
        "panel": LIGHT_PANEL,
        "hover": LIGHT_BUTTON_HOVER,
        "text": LIGHT_TEXT_PRIMARY,
        "success": LIGHT_ACCENT_SUCCESS,
        "error": LIGHT_ERROR_GALLOWS,
    }
}

# Default to dark mode
BACKGROUND = DARK_BACKGROUND
PANEL = DARK_PANEL
BUTTON_HOVER = DARK_BUTTON_HOVER
TEXT_PRIMARY = DARK_TEXT_PRIMARY
ACCENT_SUCCESS = DARK_ACCENT_SUCCESS
ERROR_GALLOWS = DARK_ERROR_GALLOWS

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

# QWERTY layout for keyboard
QWERTY = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]


# ──────────────────────────────────────────────────────────────────────────────
# AUDIO MANAGER (Lightweight, safe fallback)
# ──────────────────────────────────────────────────────────────────────────────
class AudioManager:
    """Manages background music with graceful fallback if audio files missing."""
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.current = None
        self.available = False
        try:
            pygame.mixer.init()
            self.available = True
            print('[AudioManager] pygame.mixer initialized successfully')
        except Exception as e:
            self.available = False
            print(f'[AudioManager] pygame.mixer init failed: {e}')

    def _file(self, name: str) -> str:
        """Get full path to audio file."""
        return os.path.join(self.assets_dir, "audio", name)

    def play(self, filename: str, loops: int = -1, volume: float = 0.7):
        """Play audio file with graceful fallback if file missing or mixer unavailable."""
        if not self.available:
            print(f"[AudioManager] play('{filename}') skipped: audio not available")
            return
        
        path = self._file(filename)
        try:
            if not os.path.exists(path):
                print(f"[AudioManager] file not found: {path}")
                return
            
            # Don't restart if same track already playing
            if self.current == path and pygame.mixer.music.get_busy():
                print('[AudioManager] same track already playing; skipping')
                return
            
            print(f'[AudioManager] loading and playing: {path}')
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            pygame.mixer.music.play(loops=loops)
            self.current = path
        except Exception as e:
            print(f'[AudioManager] error during play: {e}')

    def stop(self):
        """Stop audio playback gracefully."""
        if not self.available:
            return
        try:
            pygame.mixer.music.stop()
            self.current = None
            print('[AudioManager] music stopped')
        except Exception as e:
            print(f'[AudioManager] error during stop: {e}')


# ──────────────────────────────────────────────────────────────────────────────
# VECTOR DRAWING FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def draw_button(surface, x, y, width, height, text, is_hover=False, font=None, colors=None):
    """
    Draw a button with text, support hover state.
    Uses customizable color scheme (defaults to dark mode).
    """
    if colors is None:
        colors = THEMES["dark"]
    
    color = colors["hover"] if is_hover else colors["panel"]
    pygame.draw.rect(surface, color, (x, y, width, height), border_radius=8)
    pygame.draw.rect(surface, colors["success"], (x, y, width, height), width=2, border_radius=8)
    
    if font:
        text_surf, _ = font.render(text, colors["text"])
        text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(text_surf, text_rect)


def draw_gallows(surface, mistakes, colors=None):
    """
    Draw a minimalist gallows frame using lines and circles.
    Progressively reveals hangman figure based on mistake count (0-6).
    
    Progression:
    0 mistakes: Empty gallows
    1 mistake: Head (circle)
    2 mistakes: Body (line)
    3 mistakes: Left arm (line)
    4 mistakes: Right arm (line)
    5 mistakes: Left leg (line)
    6 mistakes: Right leg (line)
    """
    if colors is None:
        colors = THEMES["dark"]
    
    # Gallows frame - compact, fits on screen
    # Base
    pygame.draw.line(surface, colors["text"], (70, 480), (220, 480), 4)
    # Vertical post
    pygame.draw.line(surface, colors["text"], (110, 480), (110, 140), 4)
    # Top horizontal
    pygame.draw.line(surface, colors["text"], (110, 140), (200, 140), 4)
    # Rope
    pygame.draw.line(surface, colors["text"], (200, 140), (200, 180), 2)

    # Hangman parts (progressive based on mistakes)
    if mistakes > 0:
        # Head (circle)
        pygame.draw.circle(surface, colors["error"], (200, 210), 20, 2)
    if mistakes > 1:
        # Body (vertical line)
        pygame.draw.line(surface, colors["error"], (200, 230), (200, 300), 3)
    if mistakes > 2:
        # Left arm
        pygame.draw.line(surface, colors["error"], (200, 250), (165, 280), 3)
    if mistakes > 3:
        # Right arm
        pygame.draw.line(surface, colors["error"], (200, 250), (235, 280), 3)
    if mistakes > 4:
        # Left leg
        pygame.draw.line(surface, colors["error"], (200, 300), (170, 360), 3)
    if mistakes > 5:
        # Right leg
        pygame.draw.line(surface, colors["error"], (200, 300), (230, 360), 3)


def draw_word_display(surface, word, guessed_letters, x, y, font, colors=None):
    """Draw the word blanks with guessed letters revealed (e.g., '_ _ _ _')."""
    if colors is None:
        colors = THEMES["dark"]
    
    display_text = " ".join(
        letter if letter in guessed_letters else "_"
        for letter in word
    )
    text_surf, _ = font.render(display_text, colors["success"])
    text_rect = text_surf.get_rect(center=(x, y))
    surface.blit(text_surf, text_rect)


# ──────────────────────────────────────────────────────────────────────────────
# BUTTON CLASS (For interactivity & hover detection)
# ──────────────────────────────────────────────────────────────────────────────
class Button:
    """Clickable button with hover detection."""
    def __init__(self, x, y, width, height, text, colors=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hover = False
        self.colors = colors if colors else THEMES["dark"]

    def update(self, mouse_pos):
        """Update hover state based on mouse position."""
        self.is_hover = self.rect.collidepoint(mouse_pos)

    def draw(self, surface, font):
        """Draw button with current state."""
        draw_button(surface, self.rect.x, self.rect.y, self.rect.width,
                    self.rect.height, self.text, self.is_hover, font, self.colors)

    def is_clicked(self, mouse_pos):
        """Check if button was clicked."""
        return self.rect.collidepoint(mouse_pos)


# ──────────────────────────────────────────────────────────────────────────────
# KEYBOARD BUTTON CLASS
# ──────────────────────────────────────────────────────────────────────────────
class KeyboardButton:
    """Letter button for the QWERTY keyboard grid."""
    def __init__(self, letter, x, y, width, height):
        self.letter = letter
        self.rect = pygame.Rect(x, y, width, height)
        self.is_used = False

    def draw(self, surface, font, colors=None):
        """Draw keyboard button with used/unused styling."""
        if colors is None:
            colors = THEMES["dark"]
        
        color = (80, 80, 100) if self.is_used else colors["panel"]
        border_color = (100, 100, 120) if self.is_used else colors["success"]
        
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, border_color, self.rect, width=1, border_radius=4)
        
        text_color = colors["text"] if not self.is_used else (120, 120, 130)
        text_surf, _ = font.render(self.letter, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        """Check if button was clicked."""
        return self.rect.collidepoint(mouse_pos)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION CLASS
# ──────────────────────────────────────────────────────────────────────────────
class HangmanApp:
    """Main Pygame-based Hangman game application."""
    
    def __init__(self):
        display_info = pygame.display.Info()
        self.screen_width = min(SCREEN_WIDTH, display_info.current_w)
        self.screen_height = min(SCREEN_HEIGHT, max(700, display_info.current_h - 80))
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Regular Hangman")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60

        # Fonts
        self.title_font = pygame.freetype.SysFont("courier", 48, bold=True)
        self.heading_font = pygame.freetype.SysFont("courier", 32, bold=True)
        self.body_font = pygame.freetype.SysFont("courier", 18)
        self.small_font = pygame.freetype.SysFont("courier", 14)
        self.large_font = pygame.freetype.SysFont("courier", 24, bold=True)

        # Game state
        self.game = None
        self.difficulty = "medium"
        self.current_screen = "main_menu"
        self.timer_remaining = 0
        self.timer_active = False
        self.feedback = ""

        # Settings state
        self.theme = "dark"  # "dark" or "light"
        self.music_enabled = True  # True or False
        
        # Get current colors based on theme
        self.colors = THEMES[self.theme]

        # Audio
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.audio = AudioManager(assets_dir)

        # Keyboard state
        self.keyboard_buttons = []
        self._build_keyboard()
        
        # Button collections (initialized to prevent AttributeError on first frame)
        self.main_menu_buttons = []
        self.difficulty_buttons = []
        self.settings_buttons = []
        self.back_button = None
        self.play_again_button = None
        self.menu_button_end = None

    def _build_keyboard(self):
        """Create keyboard button grid with QWERTY layout."""
        self.keyboard_buttons = []
        start_y = self.screen_height - 190
        row_height = 50
        key_width = 45
        key_height = 40

        for row_idx, row in enumerate(QWERTY):
            # Calculate row offset for staggered layout
            row_offset = (30 * row_idx)
            row_y = start_y + row_idx * row_height
            
            # Center the row
            total_width = len(row) * key_width
            start_x = (self.screen_width - total_width) // 2 + row_offset
            
            for col_idx, letter in enumerate(row):
                x = start_x + col_idx * key_width
                btn = KeyboardButton(letter, x, row_y, key_width, key_height)
                self.keyboard_buttons.append(btn)

    def run(self):
        """Main game loop."""
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(self.fps)

        pygame.quit()

    def _handle_events(self):
        """Handle user input and window events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.current_screen != "main_menu":
                        self.current_screen = "main_menu"
                elif self.current_screen == "game" and event.unicode.isalpha():
                    self._process_guess(event.unicode.upper())
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.current_screen == "main_menu":
                    self._handle_main_menu_click(mouse_pos)
                elif self.current_screen == "difficulty":
                    self._handle_difficulty_click(mouse_pos)
                elif self.current_screen == "settings":
                    self._handle_settings_click(mouse_pos)
                elif self.current_screen == "game":
                    self._handle_game_click(mouse_pos)
                elif self.current_screen == "end":
                    self._handle_end_click(mouse_pos)

    def _handle_main_menu_click(self, mouse_pos):
        """Handle clicks on main menu."""
        for btn in self.main_menu_buttons:
            if btn.is_clicked(mouse_pos):
                if btn.text == "New Game":
                    self._start_game(self.difficulty)
                elif btn.text == "Change Difficulty":
                    self.current_screen = "difficulty"
                elif btn.text == "Settings":
                    self.current_screen = "settings"
                elif btn.text == "Exit Game":
                    self.running = False

    def _handle_difficulty_click(self, mouse_pos):
        """Handle clicks on difficulty screen."""
        for btn in self.difficulty_buttons:
            if btn.is_clicked(mouse_pos):
                self.difficulty = btn.text.lower()
                self.current_screen = "main_menu"
        
        if self.back_button and self.back_button.is_clicked(mouse_pos):
            self.current_screen = "main_menu"

    def _handle_settings_click(self, mouse_pos):
        """Handle clicks on settings screen."""
        for setting_type, btn in self.settings_buttons:
            if btn.is_clicked(mouse_pos):
                if setting_type == "theme":
                    # Toggle between dark and light
                    self.theme = "light" if self.theme == "dark" else "dark"
                    self.colors = THEMES[self.theme]
                elif setting_type == "music":
                    # Toggle music on/off
                    self.music_enabled = not self.music_enabled
        
        if self.back_button and self.back_button.is_clicked(mouse_pos):
            self.current_screen = "main_menu"

    def _handle_game_click(self, mouse_pos):
        """Handle clicks during game (keyboard buttons)."""
        for btn in self.keyboard_buttons:
            if btn.is_clicked(mouse_pos) and not btn.is_used:
                self._process_guess(btn.letter)

    def _handle_end_click(self, mouse_pos):
        """Handle clicks on end game screen."""
        if self.play_again_button and self.play_again_button.is_clicked(mouse_pos):
            self._start_game(self.difficulty)
        elif self.menu_button_end and self.menu_button_end.is_clicked(mouse_pos):
            self.current_screen = "main_menu"

    def _start_game(self, difficulty):
        """Initialize a new game."""
        if self.music_enabled:
            self.audio.stop()
        self.difficulty = difficulty
        word, category = get_random_word(difficulty)
        self.game = HangmanGame(word, difficulty, category)
        self.current_screen = "game"
        
        cfg = get_config(difficulty)
        timer_seconds = cfg.get("timer_seconds")
        self.timer_remaining = timer_seconds if timer_seconds else 0
        self.timer_active = self.timer_remaining > 0
        self.feedback = ""
        
        # Reset keyboard
        for btn in self.keyboard_buttons:
            btn.is_used = False
        
        # Play game music if enabled
        if self.music_enabled:
            self.audio.play("game.mp3", loops=0, volume=0.7)

    def _process_guess(self, letter):
        """Process a letter guess."""
        if self.game.get_status() != "ongoing":
            return

        # Find and mark the keyboard button
        for btn in self.keyboard_buttons:
            if btn.letter == letter:
                if btn.is_used:
                    return
                btn.is_used = True
                break

        result = self.game.guess(letter)
        self.feedback = ""

        if result == "already":
            self.feedback = f"'{letter}' was already guessed."
        elif result == "wrong":
            self.feedback = f"✗ '{letter}' is not in the word!"
        else:
            self.feedback = f"✓ '{letter}' is correct!"

        # Check for end state
        if self.game.get_status() != "ongoing":
            self.current_screen = "end"
        else:
            # Reset timer if applicable
            if get_config(self.difficulty).get("timer_seconds"):
                self.timer_remaining = get_config(self.difficulty)["timer_seconds"]
                self.timer_active = True

    def _update(self):
        """Update game logic and state."""
        mouse_pos = pygame.mouse.get_pos()

        if self.current_screen == "main_menu":
            for btn in self.main_menu_buttons:
                btn.update(mouse_pos)
        elif self.current_screen == "difficulty":
            for btn in self.difficulty_buttons:
                btn.update(mouse_pos)
            if self.back_button:
                self.back_button.update(mouse_pos)
        elif self.current_screen == "settings":
            for setting_type, btn in self.settings_buttons:
                btn.update(mouse_pos)
            if self.back_button:
                self.back_button.update(mouse_pos)
        elif self.current_screen == "end":
            if self.play_again_button:
                self.play_again_button.update(mouse_pos)
            if self.menu_button_end:
                self.menu_button_end.update(mouse_pos)

        # Update timer
        if self.current_screen == "game" and self.timer_active and self.timer_remaining > 0:
            self.timer_remaining -= 1 / self.fps
            if self.timer_remaining <= 0:
                self.game.remaining_attempts -= 1
                self.feedback = "⏱ Time's up! You lost an attempt."
                self.timer_remaining = get_config(self.difficulty)["timer_seconds"]
                if self.game.get_status() != "ongoing":
                    self.current_screen = "end"

    def _draw(self):
        """Render current screen."""
        self.screen.fill(self.colors["bg"])

        if self.current_screen == "main_menu":
            self._draw_main_menu()
        elif self.current_screen == "difficulty":
            self._draw_difficulty()
        elif self.current_screen == "settings":
            self._draw_settings()
        elif self.current_screen == "game":
            self._draw_game()
        elif self.current_screen == "end":
            self._draw_end()

        pygame.display.flip()

    def _draw_main_menu(self):
        """Draw main menu screen."""
        # Title
        title_surf, _ = self.title_font.render("REGULAR HANGMAN", self.colors["text"])
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 80))
        self.screen.blit(title_surf, title_rect)

        # Menu buttons
        button_configs = [
            ("New Game", 250),
            ("Change Difficulty", 350),
            ("Settings", 450),
            ("Exit Game", 550),
        ]

        self.main_menu_buttons = []
        for text, y in button_configs:
            btn = Button(self.screen_width // 2 - 100, y, 200, 50, text, self.colors)
            btn.update(pygame.mouse.get_pos())
            btn.draw(self.screen, self.body_font)
            self.main_menu_buttons.append(btn)

        # Play menu music if not already playing and music is enabled
        if self.music_enabled and self.audio.available and not pygame.mixer.music.get_busy():
            self.audio.play("menu.mp3", loops=-1, volume=0.7)

    def _draw_difficulty(self):
        """Draw difficulty selection screen."""
        # Header
        header_surf, _ = self.heading_font.render("SELECT DIFFICULTY", self.colors["text"])
        header_rect = header_surf.get_rect(center=(self.screen_width // 2, 80))
        self.screen.blit(header_surf, header_rect)

        # Difficulty buttons
        difficulty_configs = [
            ("Easy", "8 attempts · Category shown · Hint allowed", 220),
            ("Medium", "6 attempts · No category · 1 hint allowed", 340),
            ("Hard", "4 attempts · No hints · 30-sec timer", 460),
        ]

        self.difficulty_buttons = []
        for text, desc, y in difficulty_configs:
            btn = Button(self.screen_width // 2 - 120, y, 240, 50, text, self.colors)
            btn.update(pygame.mouse.get_pos())
            btn.draw(self.screen, self.body_font)
            self.difficulty_buttons.append(btn)

            # Description text
            desc_surf, _ = self.small_font.render(desc, self.colors["text"])
            desc_rect = desc_surf.get_rect(center=(self.screen_width // 2, y + 70))
            self.screen.blit(desc_surf, desc_rect)

        # Back button
        self.back_button = Button(30, self.screen_height - 70, 120, 40, "← BACK", self.colors)
        self.back_button.update(pygame.mouse.get_pos())
        self.back_button.draw(self.screen, self.small_font)

    def _draw_settings(self):
        """Draw settings screen with theme and music toggle options."""
        # Header
        header_surf, _ = self.heading_font.render("SETTINGS", self.colors["text"])
        header_rect = header_surf.get_rect(center=(self.screen_width // 2, 80))
        self.screen.blit(header_surf, header_rect)

        # Theme section
        theme_label_surf, _ = self.body_font.render("THEME:", self.colors["text"])
        theme_label_rect = theme_label_surf.get_rect(center=(self.screen_width // 2, 180))
        self.screen.blit(theme_label_surf, theme_label_rect)

        # Theme toggle button
        self.settings_buttons = []
        theme_display = f"🌙 {self.theme.upper()} THEME" if self.theme == "dark" else f"☀️ {self.theme.upper()} THEME"
        theme_btn = Button(self.screen_width // 2 - 120, 270, 240, 50, theme_display, self.colors)
        theme_btn.update(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, self.colors["success"], theme_btn.rect, width=3, border_radius=8)
        theme_btn.draw(self.screen, self.body_font)
        self.settings_buttons.append(("theme", theme_btn))

        # Music section
        music_label_surf, _ = self.body_font.render("MUSIC:", self.colors["text"])
        music_label_rect = music_label_surf.get_rect(center=(self.screen_width // 2, 380))
        self.screen.blit(music_label_surf, music_label_rect)

        # Music toggle button
        music_display = "🔊 MUSIC ON" if self.music_enabled else "🔇 MUSIC OFF"
        music_btn = Button(self.screen_width // 2 - 120, 480, 240, 50, music_display, self.colors)
        music_btn.update(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, self.colors["success"], music_btn.rect, width=3, border_radius=8)
        music_btn.draw(self.screen, self.body_font)
        self.settings_buttons.append(("music", music_btn))

        # Back button
        self.back_button = Button(30, self.screen_height - 70, 120, 40, "← BACK", self.colors)
        self.back_button.update(pygame.mouse.get_pos())
        self.back_button.draw(self.screen, self.small_font)

    def _draw_game(self):
        """Draw game screen with all game UI elements."""
        # Difficulty badge (top right)
        diff_surf, _ = self.small_font.render(f"[ {self.difficulty.upper()} ]", self.colors["success"])
        diff_rect = diff_surf.get_rect(topright=(self.screen_width - 20, 20))
        self.screen.blit(diff_surf, diff_rect)

        # Menu button (top right)
        menu_text = "← Menu (ESC)"
        menu_surf, _ = self.small_font.render(menu_text, (180, 180, 190) if self.theme == "dark" else (100, 100, 110))
        menu_rect = menu_surf.get_rect(topright=(self.screen_width - 20, 50))
        self.screen.blit(menu_surf, menu_rect)

        # Category if applicable
        cfg = get_config(self.difficulty)
        if cfg["show_category"]:
            cat_surf, _ = self.small_font.render(f"Category: {self.game.category}", (180, 180, 190) if self.theme == "dark" else (100, 100, 110))
            cat_rect = cat_surf.get_rect(topright=(self.screen_width - 20, 20))
            self.screen.blit(cat_surf, cat_rect)

        # Timer if applicable
        if cfg["timer_seconds"] and self.timer_active:
            timer_color = self.colors["error"] if self.timer_remaining <= 10 else (250, 200, 0)
            timer_surf, _ = self.body_font.render(f"⏱ {int(self.timer_remaining)}s", timer_color)
            timer_rect = timer_surf.get_rect(topright=(self.screen_width - 20, 60))
            self.screen.blit(timer_surf, timer_rect)

        # Mistakes display (top left)
        mistakes = self.game.max_attempts - self.game.remaining_attempts
        mistakes_color = self.colors["error"] if mistakes >= self.game.max_attempts - 1 else self.colors["text"]
        mistakes_surf, _ = self.body_font.render(
            f"Mistakes: {mistakes}/{self.game.max_attempts}",
            mistakes_color
        )
        self.screen.blit(mistakes_surf, (20, 20))

        # Draw gallows with theme colors (left side)
        draw_gallows(self.screen, mistakes, self.colors)

        # Word display (right side, top)
        draw_word_display(self.screen, self.game.word, self.game.guessed_letters,
                         self.screen_width - 200, 120, self.large_font, self.colors)

        # Guessed letters (right side)
        guessed_text = ", ".join(self.game.guessed_letters) if self.game.guessed_letters else "—"
        guessed_text_short = ", ".join(list(self.game.guessed_letters)[:15]) + ("..." if len(self.game.guessed_letters) > 15 else "") if self.game.guessed_letters else "—"
        guessed_surf, _ = self.small_font.render(f"Guessed: {guessed_text_short}", (180, 180, 190) if self.theme == "dark" else (100, 100, 110))
        guessed_rect = guessed_surf.get_rect(topright=(self.screen_width - 20, 180))
        self.screen.blit(guessed_surf, guessed_rect)

        # Feedback message (right side, center)
        if self.feedback:
            feedback_color = self.colors["success"] if "✓" in self.feedback else self.colors["error"] if "✗" in self.feedback else self.colors["text"]
            feedback_surf, _ = self.body_font.render(self.feedback, feedback_color)
            feedback_rect = feedback_surf.get_rect(center=(self.screen_width - 200, 250))
            self.screen.blit(feedback_surf, feedback_rect)

        # Hint button if available
        if cfg["hint_available"]:
            hint_surf, _ = self.small_font.render("Press 'H' for Hint (coming soon)", (250, 200, 0))
            hint_rect = hint_surf.get_rect(center=(self.screen_width // 2, 300))
            self.screen.blit(hint_surf, hint_rect)

        # Keyboard
        for btn in self.keyboard_buttons:
            btn.draw(self.screen, self.small_font, self.colors)

    def _draw_end(self):
        """Draw game end screen with results and buttons."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        status = self.game.get_status()
        score = self.game.get_score()

        # Panel
        panel_w, panel_h = 500, 280
        panel_x = (self.screen_width - panel_w) // 2
        panel_y = (self.screen_height - panel_h) // 2

        pygame.draw.rect(self.screen, self.colors["panel"], (panel_x, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(self.screen, self.colors["success"], (panel_x, panel_y, panel_w, panel_h), width=3, border_radius=12)

        # Title
        title_text = "YOU WIN! 🎉" if status == "win" else "GAME OVER"
        title_color = self.colors["success"] if status == "win" else self.colors["error"]
        title_surf, _ = self.heading_font.render(title_text, title_color)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, panel_y + 40))
        self.screen.blit(title_surf, title_rect)

        # Word and score
        details_surf, _ = self.body_font.render(f"Word: {self.game.word}  |  Score: {score} pts", self.colors["text"])
        details_rect = details_surf.get_rect(center=(self.screen_width // 2, panel_y + 100))
        self.screen.blit(details_surf, details_rect)

        # Buttons
        self.play_again_button = Button(panel_x + 30, panel_y + 180, 200, 50, "▶ Play Again", self.colors)
        self.menu_button_end = Button(panel_x + 270, panel_y + 180, 200, 50, "↩ Menu", self.colors)

        self.play_again_button.update(pygame.mouse.get_pos())
        self.menu_button_end.update(pygame.mouse.get_pos())

        self.play_again_button.draw(self.screen, self.body_font)
        self.menu_button_end.draw(self.screen, self.body_font)
