import pygame
import pygame.freetype
import os
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None
from game_logic import HangmanGame
from word_bank import get_random_word, get_config

# Minimal color themes used by the UI (keeps compat with existing code)
THEMES = {
    "dark": {
        "bg": (24, 28, 33),
        "panel": (40, 44, 50),
        "hover": (60, 64, 70),
        "text": (245, 245, 245),
        "success": (102, 187, 106),
        "error": (229, 57, 53),
    },
    "light": {
        "bg": (245, 245, 245),
        "panel": (230, 230, 230),
        "hover": (200, 200, 200),
        "text": (30, 30, 30),
        "success": (76, 175, 80),
        "error": (211, 47, 47),
    },
}

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


def _load_image(path):
    """Load an image if it exists, otherwise return None."""
    if not os.path.exists(path):
        print(f'[Assets] missing image: {path}')
        return None

    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f'[Assets] failed to load {path}: {e}')

def _trim_transparent(image):
    """Remove transparent borders from an image surface when possible."""
    if image is None:
        return None

    try:
        rect = image.get_bounding_rect(min_alpha=1)
        if rect.width == 0 or rect.height == 0:
            return image
        return image.subsurface(rect).copy()
    except Exception:
        return image


def _extract_primary_sprite(image, alpha_threshold=60):
    """Extract the dominant opaque sprite region from a large transparent canvas."""
    if image is None:
        return None

    try:
        mask = pygame.mask.from_surface(image, alpha_threshold)
        rects = mask.get_bounding_rects()
        if not rects:
            return _trim_transparent(image)

        # Keep only the largest connected region to avoid strip artifacts.
        main_rect = max(rects, key=lambda rect: rect.width * rect.height)
        if main_rect.width <= 0 or main_rect.height <= 0:
            return _trim_transparent(image)
        return image.subsurface(main_rect).copy()
    except Exception:
        return _trim_transparent(image)


def _scale_image(image, size):
    """Safely scale an image surface to the requested size."""
    if image is None:
        return None
    return pygame.transform.smoothscale(image, size)


def _fit_image(image, size):
    """Scale an image to fit within size while preserving aspect ratio."""
    if image is None:
        return None

    target_w, target_h = size
    if target_w <= 0 or target_h <= 0:
        return None

    source_w = max(1, image.get_width())
    source_h = max(1, image.get_height())
    scale = min(target_w / source_w, target_h / source_h)
    fitted_w = max(1, int(source_w * scale))
    fitted_h = max(1, int(source_h * scale))
    return pygame.transform.smoothscale(image, (fitted_w, fitted_h))


def _cover_image(image, size):
    """Scale an image to fully cover size while preserving aspect ratio."""
    if image is None:
        return None

    target_w, target_h = size
    if target_w <= 0 or target_h <= 0:
        return None

    source_w = max(1, image.get_width())
    source_h = max(1, image.get_height())
    scale = max(target_w / source_w, target_h / source_h)
    cover_w = max(1, int(source_w * scale))
    cover_h = max(1, int(source_h * scale))
    scaled = pygame.transform.smoothscale(image, (cover_w, cover_h))
    crop_x = max(0, (cover_w - target_w) // 2)
    crop_y = max(0, (cover_h - target_h) // 2)
    return scaled.subsurface((crop_x, crop_y, target_w, target_h)).copy()


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


def _draw_text_shadow(surface, font, text, color, pos, shadow_color=(0, 0, 0), offset=(2, 2)):
    """Draw text with a small drop shadow for readability."""
    shadow_surf, _ = font.render(text, shadow_color)
    text_surf, _ = font.render(text, color)
    shadow_rect = shadow_surf.get_rect(topleft=(pos[0] + offset[0], pos[1] + offset[1]))
    text_rect = text_surf.get_rect(topleft=pos)
    surface.blit(shadow_surf, shadow_rect)
    surface.blit(text_surf, text_rect)


def _fit_sprite(image, size, padding=0.08):
    """Fit a sprite into a box while preserving aspect ratio and giving it breathing room."""
    if image is None:
        return None

    fitted = _fit_image(_trim_transparent(image), size)
    if fitted is None:
        return None

    target_w, target_h = size
    sprite_w = max(1, int(target_w * (1 - padding)))
    sprite_h = max(1, int(target_h * (1 - padding)))
    fitted = _fit_image(fitted, (sprite_w, sprite_h)) or fitted
    return fitted


def build_frames(sheet_path, count, target_w=366, target_h=352, spacing=0, margin_left=0, margin_top=0):
    """Build Tk-compatible animation frames from a horizontal sprite sheet."""
    if Image is None or ImageTk is None:
        print("[Sprites] Pillow (PIL) is unavailable; skipping Tk frame generation")
        return []

    if count <= 0:
        return []

    try:
        sheet = Image.open(sheet_path).convert("RGBA")
    except Exception as e:
        print(f"[Sprites] Failed to open sheet '{sheet_path}': {e}")
        return []

    sheet_w, sheet_h = sheet.size
    usable_w = sheet_w - margin_left - (count - 1) * spacing
    if usable_w <= 0 or usable_w % count != 0:
        print(f"[Sprites] Invalid frame slicing config for: {sheet_path}")
        return []

    frame_w = usable_w // count
    frames = []
    for i in range(count):
        left = margin_left + i * (frame_w + spacing)
        right = left + frame_w
        top = margin_top
        bottom = sheet_h

        frame = sheet.crop((left, top, right, bottom))

        # Trim transparent borders to stabilize centering across frames.
        bbox = frame.getbbox()
        if bbox:
            frame = frame.crop(bbox)

        scale = min(target_w / max(1, frame.width), target_h / max(1, frame.height))
        new_w = max(1, int(frame.width * scale))
        new_h = max(1, int(frame.height * scale))
        resized = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y), resized)
        frames.append(ImageTk.PhotoImage(canvas))

    return frames


# ──────────────────────────────────────────────────────────────────────────────
# BUTTON CLASS (For interactivity & hover detection)
# ──────────────────────────────────────────────────────────────────────────────
class Button:
    """Clickable button with hover detection."""
    def __init__(self, x, y, width, height, text, colors=None, image=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hover = False
        self.colors = colors if colors else THEMES["dark"]
        self.image = image

    def update(self, mouse_pos):
        """Update hover state based on mouse position."""
        self.is_hover = self.rect.collidepoint(mouse_pos)

    def draw(self, surface, font):
        """Draw button with current state."""
        if self.image is not None:
            button_image = _fit_image(self.image, (self.rect.width, self.rect.height))
            if button_image is not None:
                button_rect = button_image.get_rect(center=self.rect.center)
                surface.blit(button_image, button_rect)
                return

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

    def draw(self, surface, font, colors=None, state="available"):
        """Draw keyboard button with state-based styling."""
        if colors is None:
            colors = THEMES["dark"]

        key_rect = self.rect

        if state == "correct":
            base_color = (210, 236, 202)
            border_color = colors["success"]
        elif state == "wrong":
            base_color = (241, 216, 216)
            border_color = colors["error"]
        else:
            base_color = colors["panel"]
            border_color = colors["hover"]

        radius = max(8, key_rect.height // 4)
        pygame.draw.rect(surface, base_color, key_rect, border_radius=radius)
        pygame.draw.rect(surface, border_color, key_rect, width=2, border_radius=radius)

        # Keep keyboard glyphs high contrast against all key states.
        text_color = (255, 255, 255)
        text_surf, _ = font.render(self.letter, text_color)
        letter_rect = text_surf.get_rect(center=key_rect.center)
        surface.blit(text_surf, letter_rect)

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
        self.keyboard_font = pygame.freetype.SysFont("courier", 16, bold=True)

        # Game state
        self.game = None
        self.difficulty = "medium"
        self.current_screen = "main_menu"
        self.timer_remaining = 0
        self.timer_active = False
        self.feedback = ""
        self.sprite_frames = []
        self.current_sprite_sheet = None

        # Settings state
        self.theme = "dark"  # "dark" or "light"
        self.music_enabled = True  # True or False
        
        # Get current colors based on theme
        self.colors = THEMES[self.theme]

        # Legacy image assets used by the original UI
        self.asset_dir = os.path.join(os.path.dirname(__file__), "old assets")
        self.keyboard_asset_dir = os.path.join(os.path.dirname(__file__), "PNG")
        self.assets = self._load_assets()

        # Audio
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.audio = AudioManager(assets_dir)

        # Keyboard state
        self.keyboard_buttons = []
        self.hangman_sprite = None
        self._build_keyboard()
        self._refresh_sprite_frames(force=True)
        
        # Button collections (initialized to prevent AttributeError on first frame)
        self.main_menu_buttons = []
        self.difficulty_buttons = []
        self.settings_buttons = []
        self.back_button = None
        self.play_again_button = None
        self.menu_button_end = None
        self.menu_button_game = None
        self.hint_button = None

    def _difficulty_sprite_config(self, difficulty=None):
        """Return the enforced difficulty-to-character configuration."""
        diff = (difficulty or self.difficulty).lower()
        config = {
            "easy": ("rigby", "Rigby8.png", 8),
            "medium": ("mordecai", "Mordecai6.png", 6),
            "hard": ("benson", "Benson4.png", 4),
        }
        return config.get(diff, config["medium"])

    def _refresh_sprite_frames(self, force=False):
        """Build Tk animation frames only when difficulty sheet changes."""
        _, filename, frame_count = self._difficulty_sprite_config()
        sheet_path = os.path.join(self.asset_dir, filename)

        if not force and self.current_sprite_sheet == sheet_path and self.sprite_frames:
            return

        self.current_sprite_sheet = sheet_path
        self.sprite_frames = build_frames(
            sheet_path,
            frame_count,
            target_w=366,
            target_h=352,
        )

    def _load_assets(self):
        """Load the image set used by the older visual style."""
        image_files = {
            "clipboard": "clipboard.png",
            "background": "housebg.jpg",
            "banner": "Regular_Game.png",
            "menu": "menu_btn.png",
            "new_game": "New_Game.png",
            "change_difficulty": "Change_Difficulty.png",
            "music": "music.png",
            "settings": "settings.png",
            "exit": "Exit_Game.png",
            "back": "Back.png",
            "easy": "Easy.png",
            "medium": "Medium.png",
            "medium_alt": "Meduim.png",
            "hard": "Hard.png",
            "hint": "Hint.png",
            "heart_full": "heart_full.png",
            "heart_empty": "heart_empty.png",
            "benson": "Benson4.png",
            "mordecai": "Mordecai6.png",
            "rigby": "Rigby8.png",
        }

        assets = {}
        for key, filename in image_files.items():
            if key == "medium_alt":
                continue
            assets[key] = _trim_transparent(_load_image(os.path.join(self.asset_dir, filename)))

        if assets["medium"] is None:
            assets["medium"] = _trim_transparent(_load_image(os.path.join(self.asset_dir, image_files["medium_alt"])))

        assets["word_blank"] = _trim_transparent(_load_image(os.path.join(self.keyboard_asset_dir, "blank_lg_white.png")))
        if assets["word_blank"] is None:
            assets["word_blank"] = _trim_transparent(_load_image(os.path.join(self.keyboard_asset_dir, "blank_md_white.png")))

        self.word_blank_dark = _trim_transparent(_load_image(os.path.join(self.keyboard_asset_dir, "blank_lg_black.png")))

        return assets

    def _load_hangman_frames(self):
        """Load character sprites used to represent gameplay state."""
        sprite_map = {
            "easy": "Rigby8.png",
            "medium": "Mordecai6.png",
            "hard": "Benson4.png",
        }

        sprites_by_state = {}
        for state, filename in sprite_map.items():
            raw_sprite = _load_image(os.path.join(self.asset_dir, filename))
            sprites_by_state[state] = _extract_primary_sprite(raw_sprite)

        return sprites_by_state

    def _load_keyboard_assets(self):
        """Load per-key art from the PNG folder."""
        return {}

    def _keyboard_layout(self):
        """Return a consistent QWERTY grid layout for the on-screen keyboard."""
        keyboard_rect = pygame.Rect(0, 488, self.screen_width, max(0, self.screen_height - 488))
        row_gap = 12
        key_gap = 10
        key_size = 48
        total_height = len(QWERTY) * key_size + (len(QWERTY) - 1) * row_gap
        top_y = keyboard_rect.bottom - total_height - 18

        layout = {}
        for row_idx, row in enumerate(QWERTY):
            total_width = len(row) * key_size + (len(row) - 1) * key_gap
            start_x = keyboard_rect.centerx - total_width // 2
            y = top_y + row_idx * (key_size + row_gap)

            for col_idx, letter in enumerate(row):
                x = start_x + col_idx * (key_size + key_gap)
                layout[letter] = pygame.Rect(x, y, key_size, key_size)

        return layout

    def _build_keyboard(self):
        """Create keyboard button grid with QWERTY layout."""
        self.keyboard_buttons = []
        self.hangman_sprites = self._load_hangman_frames()
        layout = self._keyboard_layout()

        for row in QWERTY:
            for letter in row:
                rect = layout[letter]
                self.keyboard_buttons.append(KeyboardButton(letter, rect.x, rect.y, rect.width, rect.height))

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
                elif self.current_screen == "game" and event.key == pygame.K_h:
                    self._use_hint()
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
                self._refresh_sprite_frames()
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
                    if not self.music_enabled:
                        self.audio.stop()
                    elif self.current_screen == "settings":
                        self.audio.play("menu.mp3", loops=-1, volume=0.7)
        
        if self.back_button and self.back_button.is_clicked(mouse_pos):
            self.current_screen = "main_menu"

    def _handle_game_click(self, mouse_pos):
        """Handle clicks during game (keyboard buttons)."""
        if self.hint_button and self.hint_button.is_clicked(mouse_pos):
            self._use_hint()
            return

        if self.menu_button_game and self.menu_button_game.is_clicked(mouse_pos):
            self.current_screen = "main_menu"
            return

        for btn in self.keyboard_buttons:
            if btn.is_clicked(mouse_pos) and not btn.is_used:
                self._process_guess(btn.letter)

    def _use_hint(self):
        """Reveal a hint letter when the selected difficulty allows it."""
        if self.game is None or not self.game.hint_available:
            return
        if self.game.hint_used:
            self.feedback = "Hint already used."
            return

        letter = self.game.use_hint()
        if not letter:
            self.feedback = "No hint available."
            return

        button = next((btn for btn in self.keyboard_buttons if btn.letter == letter), None)
        if button is not None:
            button.is_used = True

        self.feedback = f"Hint revealed: '{letter}'"

        if self.game.get_status() != "ongoing":
            self.current_screen = "end"

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
        self._refresh_sprite_frames()
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
        button = next((btn for btn in self.keyboard_buttons if btn.letter == letter), None)
        if button is not None:
            if button.is_used:
                return
            button.is_used = True

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
        self._draw_background()

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

    def _draw_background(self):
        """Draw the house background first on every frame."""
        background = self.assets.get("background")
        if background is not None:
            bg_img = _scale_image(background, (self.screen_width, self.screen_height))
            if bg_img is not None:
                self.screen.blit(bg_img, (0, 0))
                return

        self.screen.fill(self.colors["bg"])

    def _draw_main_menu(self):
        """Draw main menu screen."""
        # Draw clipboard first (behind text/buttons), scaled up by ~25%.
        clipboard = self.assets.get("clipboard")
        if clipboard is not None:
            base_w = min(700, int(self.screen_width * 0.62))
            base_h = min(960, int(self.screen_height * 0.78))
            # increase by 25% but don't overflow screen bounds
            # make clipboard slightly smaller than previous 25% enlargement (use ~5% instead)
            clipboard_w = min(self.screen_width - 40, int(base_w * 1.05))
            clipboard_h = min(self.screen_height - 40, int(base_h * 1.05))
            clipboard_img = _fit_image(clipboard, (clipboard_w, clipboard_h))
            if clipboard_img is not None:
                clipboard_rect = clipboard_img.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 20))
                self.screen.blit(clipboard_img, clipboard_rect)

        # Draw banner (title card) on top of the clipboard so the Regular Game art sits front.
        banner = self.assets.get("banner")
        if banner is not None:
            banner_w = min(520, self.screen_width - 80)
            banner_h = max(110, banner_w * banner.get_height() // max(1, banner.get_width()))
            banner_img = _fit_image(banner, (banner_w, banner_h))
            if banner_img is not None:
                banner_rect = banner_img.get_rect(center=(self.screen_width // 2, 90))
                self.screen.blit(banner_img, banner_rect)

        # Draw title only when banner is not present (banner contains its own title art)
        if banner is None:
            title_text = "REGULAR HANGMAN"
            text_color = self.colors["text"]
            outline_color = (10, 10, 10)
            title_y = 90
            title_surf, _ = self.title_font.render(title_text, text_color)
            title_rect = title_surf.get_rect(center=(self.screen_width // 2, title_y))
            outline_surf, _ = self.title_font.render(title_text, outline_color)
            for ox, oy in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
                orect = outline_surf.get_rect(center=(title_rect.centerx + ox, title_rect.centery + oy))
                self.screen.blit(outline_surf, orect)
            self.screen.blit(title_surf, title_rect)

        # Menu buttons
        button_configs = [
            ("New Game", 218, self.assets.get("new_game")),
            ("Change Difficulty", 325, self.assets.get("change_difficulty")),
            ("Settings", 445, self.assets.get("settings")),
            ("Exit Game", 565, self.assets.get("exit")),
        ]

        # Shrink menu buttons by 25% and adjust vertical positions per user request
        shrink = 0.75
        base_offset = 40  # moved up 20px from previous 60
        self.main_menu_buttons = []
        for text, y, image in button_configs:
            # Base sizes (original design)
            if text == "New Game":
                base_w, base_h = 270, 78
            elif text == "Change Difficulty":
                base_w, base_h = 378, 109
            elif text == "Settings":
                base_w, base_h = 720, 208
            else:
                base_w, base_h = 360, 104

            w = max(1, int(base_w * shrink))
            h = max(1, int(base_h * shrink))
            # make menu buttons 10% smaller than current computed size
            w = max(1, int(w * 0.90))
            h = max(1, int(h * 0.90))
            btn_x = self.screen_width // 2 - w // 2
            # shift Settings slightly right
            if text == "Settings":
                btn_x += 5
            # shift Exit Game a little to the right as requested
            if text == "Exit Game":
                btn_x += 15

            # compute visual center for this button (used when cropping Settings' hitbox)
            center_x = btn_x + w // 2
            center_y = ( (y - h // 2) + base_offset )
            # apply same per-button vertical tweaks used earlier to get accurate center_y
            if text == "New Game":
                center_y = (y - h // 2) + base_offset + 15 + h // 2
            elif text == "Change Difficulty":
                center_y = (y - h // 2) + base_offset + 5 + h // 2
            elif text == "Settings":
                center_y = (y - h // 2) + base_offset - 35 + h // 2
            else:
                center_y = (y - h // 2) + base_offset - 30 + h // 2

            # Per-button vertical tweaks:
            if text == "New Game":
                # move New Game up by 25px relative to previous placement
                btn_y = (y - h // 2) + base_offset + 15
            elif text == "Change Difficulty":
                # move Change Difficulty up by 25px
                btn_y = (y - h // 2) + base_offset + 5
            elif text == "Settings":
                # move settings up additional 10px (and right by 5px elsewhere)
                btn_y = (y - h // 2) + base_offset - 35
            else:  # Exit Game unchanged
                btn_y = (y - h // 2) + base_offset - 30

            if text == "Settings":
                # Draw Settings visual at a slightly adjusted location (3px right, 10px up)
                visual_cx = center_x + 3
                visual_cy = center_y - 10

                if image is not None:
                    visual_img = _fit_image(image, (w, h))
                    if visual_img is not None:
                        visual_rect = visual_img.get_rect(center=(visual_cx, visual_cy))
                        self.screen.blit(visual_img, visual_rect)

                # Create a smaller hitbox (50% size) and discard the top half by positioning its
                # top at the visual center (so only the bottom half is clickable).
                hit_w = max(1, int(w * 0.5))
                hit_h = max(1, int(h * 0.5))
                hit_x = visual_cx - hit_w // 2
                hit_y = visual_cy

                # Build a Button for click detection but don't draw it as a visual element.
                btn = Button(hit_x, hit_y, hit_w, hit_h, text, self.colors, image=None)
                btn.update(pygame.mouse.get_pos())
                btn.is_hover = False
                self.main_menu_buttons.append(btn)
            else:
                btn = Button(btn_x, btn_y, w, h, text, self.colors, image=image)
                btn.update(pygame.mouse.get_pos())
                # disable hover visuals on main-menu buttons
                btn.is_hover = False
                btn.draw(self.screen, self.body_font)
                self.main_menu_buttons.append(btn)

        # Play menu music if not already playing and music is enabled
        if self.music_enabled and self.audio.available and not pygame.mixer.music.get_busy():
            self.audio.play("menu.mp3", loops=-1, volume=0.7)

    def _draw_difficulty(self):
        """Draw difficulty selection screen."""
        # Draw clipboard background like main menu (keeps visual continuity)
        clipboard = self.assets.get("clipboard")
        if clipboard is not None:
            base_w = min(700, int(self.screen_width * 0.62))
            base_h = min(960, int(self.screen_height * 0.78))
            clipboard_w = min(self.screen_width - 40, int(base_w * 1.05))
            clipboard_h = min(self.screen_height - 40, int(base_h * 1.05))
            clipboard_img = _fit_image(clipboard, (clipboard_w, clipboard_h))
            if clipboard_img is not None:
                clipboard_rect = clipboard_img.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 20))
                self.screen.blit(clipboard_img, clipboard_rect)

        # Header
        header_surf, _ = self.heading_font.render("SELECT DIFFICULTY", self.colors["text"])
        header_rect = header_surf.get_rect(center=(self.screen_width // 2, 80))
        self.screen.blit(header_surf, header_rect)

        # Difficulty buttons (layout to match clipboard area like main menu)
        difficulty_configs = [
            ("Easy", "8 attempts · Category shown · Hint allowed", self.assets.get("easy")),
            ("Medium", "6 attempts · No category · 1 hint allowed", self.assets.get("medium")),
            ("Hard", "4 attempts · No hints · 30-sec timer", self.assets.get("hard")),
        ]

        # Determine clipboard area to place buttons (use same sizing as main menu)
        clipboard = self.assets.get("clipboard")
        if clipboard is not None:
            base_w = min(700, int(self.screen_width * 0.62))
            base_h = min(960, int(self.screen_height * 0.78))
            clipboard_w = min(self.screen_width - 40, int(base_w * 1.05))
            clipboard_h = min(self.screen_height - 40, int(base_h * 1.05))
            clipboard_img = _fit_image(clipboard, (clipboard_w, clipboard_h))
            if clipboard_img is not None:
                clipboard_rect = clipboard_img.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 20))
                area_top = clipboard_rect.top + int(clipboard_rect.height * 0.18)
                area_bottom = clipboard_rect.bottom - int(clipboard_rect.height * 0.12)
                center_x = clipboard_rect.centerx
            else:
                area_top, area_bottom, center_x = 220, 620, self.screen_width // 2
        else:
            area_top, area_bottom, center_x = 220, 620, self.screen_width // 2

        slots = len(difficulty_configs)
        total_height = area_bottom - area_top
        slot_height = total_height / slots if slots > 0 else 120

        shrink = 0.75
        self.difficulty_buttons = []
        for idx, (text, desc, image) in enumerate(difficulty_configs):
            # base size for difficulty buttons
            base_w, base_h = 378, 109
            w = max(1, int(base_w * shrink))
            h = max(1, int(base_h * shrink))
            # additional 10% shrink to match main menu visuals
            w = max(1, int(w * 0.90))
            h = max(1, int(h * 0.90))
            # make difficulty buttons 25% smaller per request
            w = max(1, int(w * 0.75))
            h = max(1, int(h * 0.75))

            center_y = int(area_top + slot_height * (idx + 0.5))
            btn_x = center_x - w // 2
            # nudge the Medium button slightly to the right
            if text.lower() == "medium":
                btn_x += 3
            # nudge the Hard button slightly to the right
            if text.lower() == "hard":
                btn_x += 15
            btn_y = center_y - h // 2

            btn = Button(btn_x, btn_y, w, h, text, self.colors, image=image)
            btn.update(pygame.mouse.get_pos())
            btn.draw(self.screen, self.body_font)
            self.difficulty_buttons.append(btn)
            # descriptions intentionally omitted (visual-only difficulty buttons)

        # Back button (enlarged) — position left of clipboard and prefer art if available
        if 'clipboard_rect' in locals():
            back_w = max(160, int(clipboard_rect.width * 0.18))
            back_h = max(56, int(clipboard_rect.height * 0.10))
            back_x = max(12, clipboard_rect.left - back_w // 2)
            back_y = clipboard_rect.bottom - back_h - 18
        else:
            back_x, back_y, back_w, back_h = 20, self.screen_height - 110, 260, 110

        back_img = self.assets.get("back")
        self.back_button = Button(back_x, back_y, back_w, back_h, "← BACK", self.colors, image=back_img if back_img is not None else None)
        self.back_button.update(pygame.mouse.get_pos())
        self.back_button.draw(self.screen, self.large_font)

    def _draw_settings(self):
        """Draw settings screen with theme and music toggle options."""
        # Draw clipboard background like main menu (gives consistent backdrop)
        clipboard = self.assets.get("clipboard")
        if clipboard is not None:
            base_w = min(700, int(self.screen_width * 0.62))
            base_h = min(960, int(self.screen_height * 0.78))
            clipboard_w = min(self.screen_width - 40, int(base_w * 1.05))
            clipboard_h = min(self.screen_height - 40, int(base_h * 1.05))
            clipboard_img = _fit_image(clipboard, (clipboard_w, clipboard_h))
            if clipboard_img is not None:
                clipboard_rect = clipboard_img.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 20))
                self.screen.blit(clipboard_img, clipboard_rect)

        # Draw settings image as title/header if available (scale to clipboard width)
        settings_img = self.assets.get("settings")
        if settings_img is not None and 'clipboard_rect' in locals():
            # Make header 100% bigger relative to previous 0.75: use 1.5x clipboard width but clamp to clipboard
            header_w = min(int(clipboard_rect.width * 1.5), max(120, clipboard_rect.width - 40))
            header_h = max(64, header_w * settings_img.get_height() // max(1, settings_img.get_width()))
            header_surf = _fit_image(settings_img, (header_w, header_h))
            if header_surf is not None:
                # Nudge header up by 25px for requested vertical shift
                header_rect = header_surf.get_rect(center=(clipboard_rect.centerx, clipboard_rect.top + int(clipboard_rect.height * 0.10) - 25))
                self.screen.blit(header_surf, header_rect)
        elif settings_img is not None:
            # Fallback when clipboard not present — keep header modest
            header_w = min(520, self.screen_width - 80)
            header_h = max(64, header_w * settings_img.get_height() // max(1, settings_img.get_width()))
            header_surf = _fit_image(settings_img, (header_w, header_h))
            if header_surf is not None:
                header_rect = header_surf.get_rect(center=(self.screen_width // 2, 90 - 25))
                self.screen.blit(header_surf, header_rect)
        else:
            # Fallback to text header if settings image missing
            header_surf, _ = self.heading_font.render("SETTINGS", self.colors["text"])
            header_rect = header_surf.get_rect(center=(self.screen_width // 2, 80 - 25))
            self.screen.blit(header_surf, header_rect)

        # Music control placed inside clipboard for better layout; theme control removed
        self.settings_buttons = []
        if 'clipboard_rect' in locals():
            cx = clipboard_rect.centerx
            music_w = max(220, int(clipboard_rect.width * 0.56))
            music_h = max(72, int(clipboard_rect.height * 0.12))
            music_x = cx - music_w // 2
            music_y = clipboard_rect.top + int(clipboard_rect.height * 0.48)
            music_img = self.assets.get("music") or self.assets.get("menu")
            music_btn = Button(music_x, music_y, music_w, music_h, "", self.colors, image=music_img)
            music_btn.update(pygame.mouse.get_pos())
            music_btn.draw(self.screen, self.body_font)
            self.settings_buttons.append(("music", music_btn))
        else:
            music_img = self.assets.get("music") or self.assets.get("menu")
            music_btn = Button(self.screen_width // 2 - 180, 460, 360, 104, "", self.colors, image=music_img)
            music_btn.update(pygame.mouse.get_pos())
            music_btn.draw(self.screen, self.body_font)
            self.settings_buttons.append(("music", music_btn))

        # Back button (enlarged)
        self.back_button = Button(20, self.screen_height - 110, 260, 110, "← BACK", self.colors, image=self.assets.get("back"))
        self.back_button.update(pygame.mouse.get_pos())
        self.back_button.draw(self.screen, self.small_font)

    def _draw_game(self):
        """Draw game screen with all game UI elements."""
        cfg = get_config(self.difficulty)
        self._draw_game_hud(cfg)
        self._draw_scene()
        self._draw_word_panel()
        self._draw_keyboard_panel()

    def _draw_game_hud(self, cfg):
        """Draw the top HUD bar using the existing heart, menu, and hint art."""
        hud_rect = pygame.Rect(0, 0, self.screen_width, 82)
        center_y = hud_rect.centery
        left_x = hud_rect.left + 14

        mistakes = self.game.max_attempts - self.game.remaining_attempts
        heart_full = self.assets.get("heart_full")
        heart_empty = self.assets.get("heart_empty")
        if heart_full is not None and heart_empty is not None:
            heart_full_img = _scale_image(heart_full, (28, 28))
            heart_empty_img = _scale_image(heart_empty, (28, 28))
            for idx in range(self.game.max_attempts):
                heart = heart_empty_img if idx < mistakes else heart_full_img
                if heart is not None:
                    self.screen.blit(heart, (left_x + idx * 31, center_y - 14))

        diff_text = "DIFFICULTY:"
        diff_label_surf, _ = self.small_font.render(diff_text, self.colors["text"])
        diff_label_pos = (hud_rect.centerx - diff_label_surf.get_width() // 2, center_y - 28)
        _draw_text_shadow(self.screen, self.small_font, diff_text, self.colors["text"], diff_label_pos)

        diff_value = self.difficulty.upper()
        diff_value_surf, _ = self.heading_font.render(diff_value, self.colors["text"])
        diff_value_pos = (hud_rect.centerx - diff_value_surf.get_width() // 2, center_y - 4)
        _draw_text_shadow(self.screen, self.heading_font, diff_value, self.colors["text"], diff_value_pos)

        if cfg["timer_seconds"] and self.timer_active:
            timer_color = self.colors["error"] if self.timer_remaining <= 10 else (250, 200, 0)
            timer_text = f"⏱ {int(self.timer_remaining)}s"
            timer_surf, _ = self.small_font.render(timer_text, timer_color)
            timer_pos = (hud_rect.centerx - timer_surf.get_width() // 2, center_y + 18)
            _draw_text_shadow(self.screen, self.small_font, timer_text, timer_color, timer_pos)

        menu_btn = self.assets.get("menu")
        hint_btn = self.assets.get("hint")
        self.menu_button_game = Button(hud_rect.right - 250, hud_rect.top + 12, 112, 42, "Menu", self.colors, image=menu_btn)
        self.hint_button = Button(hud_rect.right - 126, hud_rect.top + 12, 112, 42, "Hint", self.colors, image=hint_btn)
        self.menu_button_game.update(pygame.mouse.get_pos())
        self.hint_button.update(pygame.mouse.get_pos())
        self.menu_button_game.draw(self.screen, self.small_font)
        self.hint_button.draw(self.screen, self.small_font)

    def _draw_scene(self):
        """Draw the character art directly on top of the unified background."""
        # Enforced mapping: easy->Rigby, medium->Mordecai, hard->Benson.
        sprite = self.hangman_sprites.get(self.difficulty, self.hangman_sprites.get("medium"))

        if sprite is not None:
            sprite_img = _fit_sprite(sprite, (310, 290), padding=0.02)
            if sprite_img is not None:
                # Ground the character on the left lawn near the lamppost.
                sprite_rect = sprite_img.get_rect(topleft=(160, 230))
                self.screen.blit(sprite_img, sprite_rect)

    def _draw_word_panel(self):
        """Draw the category label and word blanks directly on the background."""
        word_rect = pygame.Rect(0, 378, self.screen_width, 110)
        cfg = get_config(self.difficulty)
        label_color = (255, 255, 255)

        category_text = f"Category: {self.game.category}" if cfg["show_category"] else "Category hidden"
        category_surf, _ = self.small_font.render(category_text, label_color)
        category_pos = (word_rect.centerx - category_surf.get_width() // 2, word_rect.top + 8)
        _draw_text_shadow(self.screen, self.small_font, category_text, label_color, category_pos)

        word = self.game.word
        guessed_letters = self.game.guessed_letters
        blank = self.assets.get("word_blank") or self.word_blank_dark
        box_gap = 8
        box_w = 48
        box_h = 60
        total_width = len(word) * box_w + (len(word) - 1) * box_gap
        start_x = word_rect.centerx - total_width // 2
        top_y = word_rect.top + 28

        for idx, letter in enumerate(word):
            x = start_x + idx * (box_w + box_gap)
            box_rect = pygame.Rect(x, top_y, box_w, box_h)
            if blank is not None:
                box_img = _fit_image(blank, (box_w, box_h))
                if box_img is not None:
                    self.screen.blit(box_img, box_rect)
            else:
                pygame.draw.rect(self.screen, (255, 248, 232), box_rect, border_radius=10)
                pygame.draw.rect(self.screen, self.colors["success"], box_rect, width=2, border_radius=10)

            if letter in guessed_letters:
                letter_color = (35, 35, 40) if self.theme == "light" else self.colors["text"]
                letter_surf, _ = self.heading_font.render(letter, letter_color)
                # Place letters dynamically relative to the blank box so they stay above
                # the underline regardless of box sizing. Use ~25% down from top of the box.
                letter_y = box_rect.top + int(box_h * 0.25)
                letter_rect = letter_surf.get_rect(center=(box_rect.centerx, letter_y))
                shadow_surf, _ = self.heading_font.render(letter, (0, 0, 0))
                shadow_rect = shadow_surf.get_rect(center=(box_rect.centerx + 2, letter_y + 2))
                self.screen.blit(shadow_surf, shadow_rect)
                self.screen.blit(letter_surf, letter_rect)

        if self.feedback:
            feedback_color = self.colors["success"] if "✓" in self.feedback or "Hint" in self.feedback else self.colors["error"] if "✗" in self.feedback else self.colors["text"]
            feedback_surf, _ = self.small_font.render(self.feedback, feedback_color)
            feedback_pos = (word_rect.centerx - feedback_surf.get_width() // 2, word_rect.bottom - 24)
            _draw_text_shadow(self.screen, self.small_font, self.feedback, feedback_color, feedback_pos)

    def _draw_keyboard_panel(self):
        """Draw the dedicated keyboard directly on the main surface."""
        keyboard_rect = pygame.Rect(0, 488, self.screen_width, self.screen_height - 488)
        label_color = (255, 255, 255)
        label_surf, _ = self.small_font.render("Keyboard", label_color)
        label_pos = (keyboard_rect.centerx - label_surf.get_width() // 2, keyboard_rect.top + 2)
        _draw_text_shadow(self.screen, self.small_font, "Keyboard", label_color, label_pos)

        layout = self._keyboard_layout()

        for row_idx, row in enumerate(QWERTY):
            for col_idx, letter in enumerate(row):
                button = next((btn for btn in self.keyboard_buttons if btn.letter == letter), None)
                if button is None:
                    continue

                button.rect = layout[letter]
                state = "available"
                if letter in self.game.guessed_letters:
                    state = "correct" if letter in self.game.word else "wrong"
                    button.is_used = True
                elif button.is_used:
                    state = "wrong"

                button.draw(self.screen, self.keyboard_font, self.colors, state=state)

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
        self.play_again_button = Button(panel_x + 20, panel_y + 180, 220, 78, "▶ Play Again", self.colors, image=self.assets.get("new_game"))
        self.menu_button_end = Button(panel_x + 260, panel_y + 180, 220, 78, "↩ Menu", self.colors, image=self.assets.get("menu"))

        self.play_again_button.update(pygame.mouse.get_pos())
        self.menu_button_end.update(pygame.mouse.get_pos())

        self.play_again_button.draw(self.screen, self.body_font)
        self.menu_button_end.draw(self.screen, self.body_font)

        character = self.assets.get("mordecai") if status == "win" else self.assets.get("rigby") or self.assets.get("benson")
        if character is not None:
            character_img = _fit_image(character, (140, 140))
            character_rect = character_img.get_rect(midleft=(panel_x - 40, panel_y + panel_h // 2))
            self.screen.blit(character_img, character_rect)
