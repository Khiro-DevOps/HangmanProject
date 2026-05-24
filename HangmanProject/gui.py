import tkinter as tk
from tkinter import font as tkfont
from game_logic import HangmanGame
from word_bank import get_random_word, get_config
import os
from PIL import Image, ImageTk
import random

# Optional audio support using pygame; falls back silently if unavailable
try:
    import pygame
    _PYGAME_OK = True
except Exception:
    pygame = None
    _PYGAME_OK = False

# ── QWERTY layout ─────────────────────────────────────────────────────────────
QWERTY = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]

# ── Per-character display sizes ────────────────────────────────────────────────
TARGET_SIZES = {
    "easy":   (366, 352),
    "medium": (489, 352),
    "hard":   (472, 352),
}

# ── Unified canvas dimensions (all screens) ───────────────────────────────────
CW, CH = 900, 650

# ── Colors ────────────────────────────────────────────────────────────────────
THEME = {
    "easy":   {"bg": "#1a2e1a", "accent": "#4ade80", "btn": "#16a34a", "text": "#dcfce7"},
    "medium": {"bg": "#1e1e2e", "accent": "#facc15", "btn": "#ca8a04", "text": "#fefce8"},
    "hard":   {"bg": "#2e1a1a", "accent": "#f87171", "btn": "#dc2626", "text": "#fee2e2"},
}
BASE_BG   = "#0f0f0f"
BASE_TEXT = "#e5e5e5"


# ═════════════════════════════════════════════════════════════════════════════
# SPRITE & ASSET LOADER
# ═════════════════════════════════════════════════════════════════════════════
class SpriteLoader:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.bg_photo   = None
        self.frames     = {"easy": [], "medium": [], "hard": []}
        self.buttons    = {}

        self._sheets = {
            "easy":   ("Rigby8.png",    8),
            "medium": ("Mordecai6.png", 6),
            "hard":   ("Benson4.png",   4),
        }
        self._button_files = [
            "Regular_Game.png",
            "New_Game.png",
            "Change_Difficulty.png",
            "Exit_Game.png",
            "Easy.png",
            "Medium.png",
            "Hard.png",
            # Optional assets you may provide
            "Menu.png",
            "Menu_Btn.png",
            "menu_btn.png",
            "Back.png",
        ]

        self._load_bg()
        self._load_sheets()
        self._load_buttons()
        self._load_keyboard()
        self._load_hearts()

    # ── Background — single size for all screens ──────────────────────────────
    def _load_bg(self):
        path = os.path.join(self.assets_dir, "housebg.jpg")
        try:
            # Keep the raw PIL image so we can resize it on the fly later
            self.bg_image_raw = Image.open(path).convert("RGBA")
            self.bg_photo = ImageTk.PhotoImage(self.bg_image_raw.resize((CW, CH), Image.LANCZOS))
        except Exception:
            self.bg_image_raw = None
            self.bg_photo = None

    # ── Sprite sheets ─────────────────────────────────────────────────────────
    def _load_sheets(self):
        for diff, (fname, count) in self._sheets.items():
            path = os.path.join(self.assets_dir, fname)
            tw, th = TARGET_SIZES[diff]
            try:
                sheet  = Image.open(path).convert("RGBA")
                sw, sh = sheet.size
                fw     = sw // count
                frames = []
                for i in range(count):
                    box   = (i * fw, 0, (i + 1) * fw, sh)
                    frame = sheet.crop(box).resize((tw, th), Image.LANCZOS)
                    frames.append(ImageTk.PhotoImage(frame))
                self.frames[diff] = frames
            except Exception:
                placeholder = Image.new("RGBA", (tw, th), (50, 50, 50, 180))
                self.frames[diff] = [ImageTk.PhotoImage(placeholder) for _ in range(count)]

    # ── Remove near-black or near-white backgrounds ───────────────────────────
    def _remove_bg(self, img: Image.Image, threshold: int = 30) -> Image.Image:
        img  = img.convert("RGBA")
        data = img.getdata()
        new_data = []
        for r, g, b, a in data:
            # 1. Check if the pixel is already transparent
            if a == 0:
                new_data.append((0, 0, 0, 0))
                continue
                
            # 2. Check for near-black or near-white backgrounds
            is_black_or_white = (r < threshold and g < threshold and b < threshold) or \
                                (r > 240 and g > 240 and b > 240)
            
            # 3. NEW: Check for fake checkerboard colors (typically pure gray #808080 or light gray #c0c0c0)
            # This catches the specific gray-and-white grids common in fake transparent web images.
            is_checker_gray = (abs(r - g) < 5 and abs(g - b) < 5 and abs(r - b) < 5) and (115 < r < 205)

            if is_black_or_white or is_checker_gray:
                new_data.append((0, 0, 0, 0)) # Zap it to completely transparent
            else:
                new_data.append((r, g, b, a))
                
        img.putdata(new_data)
        return img
    # ── Button PNGs ───────────────────────────────────────────────────────────
    def _load_buttons(self):
        for fname in self._button_files:
            key  = fname.replace(".png", "")
            path = os.path.join(self.assets_dir, fname)
            try:
                img = self._remove_bg(Image.open(path))
                self.buttons[key] = img
            except Exception:
                self.buttons[key] = None

    # ── Keyboard images ───────────────────────────────────────────────────────
    def _load_keyboard(self):
        kb_w = CW - 200
        for key, fname in [("kb_normal", "keyboard_normal.png"),
                            ("kb_used",   "keyboard_key_used.png")]:
            path = os.path.join(self.assets_dir, fname)
            try:
                img    = self._remove_bg(Image.open(path))
                ow, oh = img.size
                ratio  = kb_w / ow
                kb_h   = int(oh * ratio)
                img    = img.resize((kb_w, kb_h), Image.LANCZOS)
                base   = Image.new("RGBA", (kb_w, kb_h), (0, 0, 0, 0))
                img    = Image.alpha_composite(base, img)
                self.buttons[key] = img
            except Exception:
                self.buttons[key] = None

        kb = self.buttons.get("kb_normal")
        self.kb_photo = ImageTk.PhotoImage(kb) if kb else None
        self.kb_size  = kb.size if kb else (kb_w, 180)

    # ── Heart images ──────────────────────────────────────────────────────────
    def _load_hearts(self):
        HEART_SIZE = (36, 36)
        for key, fname in [("heart_full",  "heart_full.png"),
                            ("heart_empty", "heart_empty.png")]:
            path = os.path.join(self.assets_dir, fname)
            try:
                img = self._remove_bg(Image.open(path))
                img = img.resize(HEART_SIZE, Image.LANCZOS)
                self.buttons[key] = ImageTk.PhotoImage(img)
            except Exception:
                self.buttons[key] = None

    # ── Helpers ───────────────────────────────────────────────────────────────
    def get_button(self, key: str, width: int = None, height: int = None):
        img = self.buttons.get(key)
        if img is None or isinstance(img, ImageTk.PhotoImage):
            return img
        if width or height:
            ow, oh = img.size
            if width and not height:
                height = int(oh * width / ow)
            elif height and not width:
                width = int(ow * height / oh)
            img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def get_frames(self, difficulty: str):
        return self.frames.get(difficulty, [])


# Lightweight audio manager — safe no-op when pygame isn't available
class AudioManager:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.current = None
        self.available = False
        try:
            if _PYGAME_OK:
                pygame.mixer.init()
                self.available = True
                print('[AudioManager] pygame.mixer initialized:', pygame.mixer.get_init())
        except Exception:
            self.available = False
            print('[AudioManager] pygame.mixer init failed')

    def _file(self, name: str) -> str:
        return os.path.join(self.assets_dir, "audio", name)

    def play(self, filename: str, loops: int = -1, fade_ms: int = 0, volume: float = 1.0):
        if not self.available:
            print(f"[AudioManager] play('{filename}') skipped: audio not available")
            return
        path = self._file(filename)
        print(f"[AudioManager] play called -> file={path} loops={loops} fade_ms={fade_ms} volume={volume}")
        try:
            if not os.path.exists(path):
                print(f"[AudioManager] file not found: {path}")
                return
            # If same track already playing, leave it
            if self.current == path and pygame.mixer.music.get_busy():
                print('[AudioManager] same track already playing; skipping')
                return
            print('[AudioManager] loading:', path)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            if fade_ms:
                pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            else:
                pygame.mixer.music.play(loops=loops)
            self.current = path
            print('[AudioManager] play started')
        except Exception:
            print('[AudioManager] error during play', flush=True)
            import traceback
            traceback.print_exc()

    def stop(self, fade_ms: int = 0):
        if not self.available:
            print('[AudioManager] stop() skipped: audio not available')
            return
        try:
            if fade_ms:
                print(f"[AudioManager] fading out ({fade_ms}ms)")
                pygame.mixer.music.fadeout(fade_ms)
            else:
                print('[AudioManager] stopping music')
                pygame.mixer.music.stop()
            self.current = None
        except Exception:
            print('[AudioManager] error during stop', flush=True)
            import traceback
            traceback.print_exc()


# ═════════════════════════════════════════════════════════════════════════════
# APP
# ═════════════════════════════════════════════════════════════════════════════
class HangmanApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Regular Hangman")
        self.master.resizable(True, True)
        self.master.configure(bg=BASE_BG)

        self.master.geometry(f"{CW}x{CH}")
        self._center_window(CW, CH)
        
        self.is_fullscreen = False
        
        # --- Add this background tracking variable ---
        self.bg_label = None
        self._bg_photo_full = None
        
        self.master.bind("<F11>", self._toggle_fullscreen)
        self.master.bind("<Escape>", self._exit_fullscreen)
        
        # --- Bind the resize event ---
        self.master.bind("<Configure>", self._on_window_resize)
        self.title_font = tkfont.Font(family="Courier New", size=20, weight="bold")
        self.word_font  = tkfont.Font(family="Courier New", size=18, weight="bold")
        self.body_font  = tkfont.Font(family="Courier New", size=11)
        self.small_font = tkfont.Font(family="Courier New", size=9)

        self.game:       HangmanGame | None = None
        self.difficulty: str  = "medium"
        self.timer_id          = None
        self._photo_refs       = []

        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        self.loader = SpriteLoader(assets_dir)
        # Initialize optional audio manager
        self.audio = AudioManager(assets_dir)

        self._show_main_menu()

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 0 — Main Menu
    # ═════════════════════════════════════════════════════════════════════════
    def _show_main_menu(self):
        self._cancel_timer()
        self._clear()

        canvas = tk.Canvas(
            self.master,
            width=CW,
            height=CH,
            highlightthickness=0,
            bg="black"
        )
        canvas.pack(expand=True)
        self._draw_canvas_background(canvas)
        try:
            # menu music loops indefinitely
            self.audio.play("menu.mp3", loops=-1, volume=0.7)
        except Exception:
            pass

        # Title
        title = self.loader.get_button("Regular_Game", width=520)
        if title:
            canvas.create_image(CW // 2, 130, anchor=tk.CENTER, image=title)
            self._photo_refs.append(title)
        else:
            canvas.create_text(CW // 2, 130, text="REGULAR HANGMAN",
                               font=self.title_font, fill=BASE_TEXT)

        # Buttons
        btn_data = [
            ("New_Game",          320, lambda: self._start_game(self.difficulty)),
            ("Change_Difficulty", 420, self._show_difficulty_screen),
            ("Exit_Game",         520, self.master.quit),
        ]
        for key, y, cmd in btn_data:
            photo = self.loader.get_button(key, width=300)
            if photo:
                lbl = tk.Label(canvas, image=photo, bg="#0f0f0f",
                               cursor="hand2", borderwidth=0, highlightthickness=0)
                lbl.image = photo
                lbl.bind("<Button-1>", lambda e, c=cmd: c())
                canvas.create_window(CW // 2, y, window=lbl)
            else:
                tag = f"btn_{key}"
                canvas.create_text(CW // 2, y, text=key.replace("_", " ").upper(),
                                   font=self.body_font, fill=BASE_TEXT, tags=(tag,))
                canvas.tag_bind(tag, "<Button-1>", lambda e, c=cmd: c())

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 1 — Difficulty Selection
    # ═════════════════════════════════════════════════════════════════════════
    def _show_difficulty_screen(self):
        self._cancel_timer()
        self._clear()

        canvas = tk.Canvas(
            self.master,
            width=CW,
            height=CH,
            highlightthickness=0,
            bg="black"
        )
        canvas.pack(expand=True)
        self._draw_canvas_background(canvas)

        # Header
        hdr = self.loader.get_button("Change_Difficulty", width=440)
        if hdr:
            canvas.create_image(CW // 2, 120, anchor=tk.CENTER, image=hdr)
            self._photo_refs.append(hdr)
        else:
            canvas.create_text(CW // 2, 120, text="CHANGE DIFFICULTY",
                               font=self.title_font, fill=BASE_TEXT)

        # Difficulty buttons
        diff_data = [
            ("Easy",   "easy",   260),
            ("Medium", "medium", 380),
            ("Hard",   "hard",   490),
        ]
        for key, diff, y in diff_data:
            photo = self.loader.get_button(key, width=240)
            if photo:
                lbl = tk.Label(canvas, image=photo, bg="#0f0f0f",
                               cursor="hand2", borderwidth=0, highlightthickness=0)
                lbl.image = photo
                lbl.bind("<Button-1>", lambda e, d=diff: self._change_difficulty(d))
                canvas.create_window(CW // 2, y, window=lbl)
            else:
                tag = f"diff_{key}"
                canvas.create_text(CW // 2, y, text=key.upper(),
                                   font=self.body_font, fill=BASE_TEXT, tags=(tag,))
                canvas.tag_bind(tag, "<Button-1>", lambda e, d=diff: self._change_difficulty(d))

        # Back button
        back = self.loader.get_button("Back", width=140)
        if back:
            lbl = tk.Label(canvas, image=back, bg="#0f0f0f",
                           cursor="hand2", borderwidth=0, highlightthickness=0)
            lbl.image = back
            lbl.bind("<Button-1>", lambda e: self._show_main_menu())
            canvas.create_window(90, CH - 60, window=lbl)
        else:
            canvas.create_text(90, CH - 60, text="← BACK",
                               font=self.small_font, fill="#aaa", tags=("back",))
            canvas.tag_bind("back", "<Button-1>", lambda e: self._show_main_menu())

    def _change_difficulty(self, difficulty: str):
        """Set the selected difficulty without starting a game, then return to main menu."""
        self.difficulty = difficulty
        try:
            print(f"[HangmanApp] difficulty set to {difficulty}")
        except Exception:
            pass
        # Return to main menu so player can press New Game when ready
        self._show_main_menu()

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 2 — Game Screen
    # ═════════════════════════════════════════════════════════════════════════
    def _start_game(self, difficulty: str):
        self._cancel_timer()
        try:
            # stop any menu music before starting the round
            self.audio.stop(fade_ms=300)
        except Exception:
            pass
        self.difficulty = difficulty
        word, category  = get_random_word(difficulty)
        self.game       = HangmanGame(word, difficulty, category)
        self._show_game_screen()

    def _show_game_screen(self):
        self._cancel_timer()
        self._clear()

        theme = THEME[self.difficulty]
        cfg   = get_config(self.difficulty)

        self.master.configure(bg=theme["bg"])

        self.canvas = tk.Canvas(
            self.master,
            width=CW,
            height=CH,
            highlightthickness=0,
            bg="black"
        )
        self.canvas.pack(expand=True)
        self._draw_canvas_background(self.canvas)
        try:
            # play the long gameplay track once (no loop)
            self.audio.play("game.mp3", loops=0, volume=0.7)
        except Exception:
            pass

        # ── Layout constants ──────────────────────────────────────────────────
        KB_H       = self.loader.kb_size[1]
        KB_Y       = CH - KB_H - 10
        CHAR_Y     = KB_Y - TARGET_SIZES[self.difficulty][1] + 20
        HEART_Y    = 12
        WORD_Y     = 140
        RIGHT_X    = 510
        FEEDBACK_Y = WORD_Y + 120

        # ── Character sprite (left side) ──────────────────────────────────────
        self.sprite_frames = self.loader.get_frames(self.difficulty)
        self.canvas_sprite = None
        if self.sprite_frames:
            self.current_sprite_photo = self.sprite_frames[0]
            self.canvas_sprite = self.canvas.create_image(
                0, CHAR_Y, anchor=tk.NW, image=self.current_sprite_photo)

        # ── Hearts top left ───────────────────────────────────────────────────
        self.heart_items = []
        heart_full  = self.loader.buttons.get("heart_full")
        heart_empty = self.loader.buttons.get("heart_empty")
        hx = 12
        for i in range(self.game.max_attempts):
            item = self.canvas.create_image(hx, HEART_Y, anchor=tk.NW,
                                            image=heart_full)
            self.heart_items.append(item)
            if heart_full:
                self._photo_refs.append(heart_full)
            hx += 42

        # ── Difficulty badge + Menu button (top right) ────────────────────────
        # Try to show a difficulty badge image (Easy/Medium/Hard) if available
        diff_key = self.difficulty.capitalize()
        diff_img = self.loader.get_button(diff_key, width=140)
        if diff_img:
            # Place label on the canvas (so it moves/scales with canvas) and keep a ref
            diff_lbl = tk.Label(self.canvas, image=diff_img, bg=theme["bg"], borderwidth=0)
            diff_lbl.image = diff_img
            self._photo_refs.append(diff_img)
            # compute height for spacing
            try:
                diff_h = diff_img.height()
            except Exception:
                diff_h = 18
            self.canvas.create_window(CW - 10, 14, window=diff_lbl, anchor=tk.NE)
        else:
            self.canvas.create_text(
                CW - 10, 14, text=f"[ {self.difficulty.upper()} ]",
                font=self.body_font, fill=theme["accent"], anchor=tk.NE)

        # Menu button: try several common keys (request a reasonable width)
        menu_img = (self.loader.get_button("Menu", width=120)
                or self.loader.get_button("menu_btn", width=120)
                or self.loader.get_button("Menu_Btn", width=120))
        if menu_img:
            menu_lbl = tk.Label(self.canvas, image=menu_img, bg=theme["bg"], cursor="hand2", borderwidth=0)
            menu_lbl.image = menu_img
            self._photo_refs.append(menu_img)
            menu_lbl.bind("<Button-1>", lambda e: self._show_main_menu())
            # place menu below difficulty badge if diff image exists
            try:
                menu_y = 14 + (diff_h if 'diff_h' in locals() else 18) + 6
            except Exception:
                menu_y = 34
            self.canvas.create_window(CW - 10, menu_y, window=menu_lbl, anchor=tk.NE)
        else:
            menu_tag = "menu_btn"
            self.canvas.create_text(
                CW - 10, 34, text="↩ Menu",
                font=self.small_font, fill="#aaa",
                anchor=tk.NE, tags=(menu_tag,))
            self.canvas.tag_bind(menu_tag, "<Button-1>", lambda e: self._show_main_menu())

        # ── Category (easy only) ──────────────────────────────────────────────
        if cfg["show_category"]:
            self.canvas.create_text(
                CW - 10, 54, text=f"Category: {self.game.category}",
                font=self.small_font, fill="#aaa", anchor=tk.NE)

        # ── Timer text (hard mode) ────────────────────────────────────────────
        self.timer_text = self.canvas.create_text(
            CW - 10, 72, text="",
            font=self.body_font, fill="#f87171", anchor=tk.NE)

        # ── Word letter boxes ─────────────────────────────────────────────────
        self._build_word_display(RIGHT_X, WORD_Y, theme)

        # ── Feedback text ─────────────────────────────────────────────────────
        panel_cx = RIGHT_X + (CW - RIGHT_X) // 2
        self.feedback_text = self.canvas.create_text(
            panel_cx, FEEDBACK_Y, text="",
            font=self.body_font, fill=theme["text"],
            width=CW - RIGHT_X - 10, anchor=tk.CENTER)

        # ── Keyboard (bottom) ─────────────────────────────────────────────────
        self._build_keyboard(KB_Y, theme)

        # ── Hint button (easy + medium) ───────────────────────────────────────
        if cfg["hint_available"]:
            hint_tag = "hint_btn"
            self.canvas.create_text(
                CW - 15, KB_Y - 20,
                text="💡 HINT", font=self.body_font,
                fill="#facc15", anchor=tk.NE, tags=(hint_tag,))
            self.canvas.tag_bind(hint_tag, "<Button-1>", lambda e: self._on_hint())
            self._hint_tag          = hint_tag
            self._hint_used_display = False

        # ── Physical keyboard binding ─────────────────────────────────────────
        self.master.bind("<Key>", self._on_key_press)

        # ── Hard mode timer ───────────────────────────────────────────────────
        if cfg["timer_seconds"]:
            self._start_countdown(cfg["timer_seconds"])

    # ── Word letter boxes ─────────────────────────────────────────────────────
    def _build_word_display(self, start_x: int, y: int, theme: dict):
        word    = self.game.word
        panel_w = CW - start_x - 10

        if len(word) <= 5:
            box_w, box_h, gap = 44, 50, 6
        elif len(word) <= 8:
            box_w, box_h, gap = 36, 44, 5
        elif len(word) <= 12:
            box_w, box_h, gap = 28, 36, 4
        else:
            box_w, box_h, gap = 22, 30, 3

        total_w = len(word) * (box_w + gap) - gap

        # Force fit if still too wide
        if total_w > panel_w:
            box_w   = (panel_w - (len(word) - 1) * gap) // len(word)
            box_h   = int(box_w * 1.1)
            total_w = len(word) * (box_w + gap) - gap

        ox = start_x + (panel_w - total_w) // 2

        self._letter_boxes = []
        self._box_font = tkfont.Font(
            family="Courier New",
            size=max(8, box_h // 3),
            weight="bold")

        for i, letter in enumerate(word):
            x0 = ox + i * (box_w + gap)
            x1 = x0 + box_w
            y0 = y
            y1 = y + box_h
            rect = self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill="#1a1a2e", outline=theme["accent"], width=2)
            txt = self.canvas.create_text(
                (x0 + x1) // 2, (y0 + y1) // 2,
                text="", font=self._box_font,
                fill=theme["accent"])
            self._letter_boxes.append((rect, txt, letter))

    # ── Keyboard ──────────────────────────────────────────────────────────────
    def _build_keyboard(self, kb_y: int, theme: dict):
        kb_x = (CW - self.loader.kb_size[0]) // 2
        if self.loader.kb_photo:
            self.canvas.create_image(kb_x, kb_y, anchor=tk.NW,
                                     image=self.loader.kb_photo)
            self._photo_refs.append(self.loader.kb_photo)

        kw, kh      = self.loader.kb_size
        max_keys    = max(len(r) for r in QWERTY)
        key_w       = kw / max_keys
        key_h       = kh / len(QWERTY)
        row_offsets = [0, key_w * 0.5, key_w * 1.5]

        self._key_regions: dict[str, tuple] = {}
        for ri, row in enumerate(QWERTY):
            for ci, letter in enumerate(row):
                rx0 = kb_x + row_offsets[ri] + ci * key_w
                ry0 = kb_y + ri * key_h
                rx1 = rx0 + key_w
                ry1 = ry0 + key_h
                self._key_regions[letter] = (rx0, ry0, rx1, ry1)

        self.canvas.bind("<Button-1>", self._on_canvas_click)

    # ═════════════════════════════════════════════════════════════════════════
    # INPUT HANDLERS
    # ═════════════════════════════════════════════════════════════════════════
    def _on_canvas_click(self, event):
        for letter, (x0, y0, x1, y1) in self._key_regions.items():
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                self._process_guess(letter)
                return

    def _on_key_press(self, event):
        key = event.char.upper()
        if key.isalpha() and len(key) == 1:
            self._process_guess(key)

    def _process_guess(self, letter: str):
        if self.game.get_status() != "ongoing":
            return

        result = self.game.guess(letter)
        self._refresh_display()

        if result == "already":
            self._set_feedback(f"'{letter}' was already guessed.", "#aaa")
        elif result == "wrong":
            self._set_feedback(f"✗  '{letter}' is not in the word!", "#f87171")
            self._mark_key_used(letter)
        else:
            self._set_feedback(f"✓  '{letter}' is correct!", "#4ade80")
            self._mark_key_used(letter)

        self._check_end()

        cfg = get_config(self.difficulty)
        if cfg["timer_seconds"] and self.game.get_status() == "ongoing":
            self._cancel_timer()
            self._start_countdown(cfg["timer_seconds"])

    def _on_hint(self):
        if getattr(self, "_hint_used_display", False):
            return
        letter = self.game.use_hint()
        if letter:
            self._set_feedback(f"💡 Hint: '{letter}' has been revealed!", "#facc15")
            self._refresh_display()
            self._mark_key_used(letter)
            self._hint_used_display = True
            try:
                self.canvas.itemconfig(self._hint_tag, fill="#555")
            except Exception:
                pass
            self._check_end()
        else:
            self._set_feedback("No hints available.", "#aaa")

    def _mark_key_used(self, letter: str):
        region = self._key_regions.get(letter)
        if not region:
            return
        x0, y0, x1, y1 = region
        self.canvas.create_rectangle(
            x0 + 2, y0 + 2, x1 - 2, y1 - 2,
            fill="#222222", outline="", stipple="gray50")

    # ═════════════════════════════════════════════════════════════════════════
    # TIMER
    # ═════════════════════════════════════════════════════════════════════════
    def _start_countdown(self, seconds: int):
        self._remaining_time = seconds
        self._tick()

    def _tick(self):
        if self._remaining_time <= 0:
            self.game.remaining_attempts -= 1
            self._set_feedback("⏱ Time's up! You lost an attempt.", "#f87171")
            self._refresh_display()
            if self.game.get_status() == "ongoing":
                self._start_countdown(get_config(self.difficulty)["timer_seconds"])
            else:
                self._check_end()
            return

        color = "#f87171" if self._remaining_time <= 10 else "#facc15"
        try:
            self.canvas.itemconfig(self.timer_text,
                                   text=f"⏱ {self._remaining_time}s",
                                   fill=color)
        except Exception:
            pass
        self._remaining_time -= 1
        self.timer_id = self.master.after(1000, self._tick)

    def _cancel_timer(self):
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

    # ═════════════════════════════════════════════════════════════════════════
    # DISPLAY REFRESH
    # ═════════════════════════════════════════════════════════════════════════
    def _refresh_display(self):
        # Letter boxes
        guessed = self.game.guessed_letters
        for rect, txt, letter in self._letter_boxes:
            if letter in guessed:
                self.canvas.itemconfig(txt, text=letter)

        # Hearts
        remaining   = self.game.remaining_attempts
        heart_full  = self.loader.buttons.get("heart_full")
        heart_empty = self.loader.buttons.get("heart_empty")
        for i, item in enumerate(self.heart_items):
            img = heart_full if i < remaining else heart_empty
            if img:
                self.canvas.itemconfig(item, image=img)

        # Sprite
        wrongs = self.game.max_attempts - self.game.remaining_attempts
        if getattr(self, "sprite_frames", None):
            idx = min(wrongs, len(self.sprite_frames) - 1)
            self.current_sprite_photo = self.sprite_frames[idx]
            try:
                self.canvas.itemconfig(self.canvas_sprite,
                                       image=self.current_sprite_photo)
            except Exception:
                pass

    def _set_feedback(self, msg: str, color: str = "#e5e5e5"):
        try:
            self.canvas.itemconfig(self.feedback_text, text=msg, fill=color)
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════════
    # WIN / LOSE
    # ═════════════════════════════════════════════════════════════════════════
    def _check_end(self):
        status = self.game.get_status()
        if status == "win":
            self._cancel_timer()
            try:
                self.canvas.itemconfig(self.timer_text, text="")
            except Exception:
                pass
            self._unbind_input()
            self._show_play_again()

        elif status == "lose":
            self._cancel_timer()
            try:
                self.canvas.itemconfig(self.timer_text, text="")
            except Exception:
                pass
            # Reveal all letters
            for rect, txt, letter in self._letter_boxes:
                self.canvas.itemconfig(txt, text=letter)
            self._unbind_input()
            self._show_play_again()

    def _unbind_input(self):
        self.master.unbind("<Key>")
        self.canvas.unbind("<Button-1>")

    def _show_play_again(self):
        theme  = THEME[self.difficulty]
        status = self.game.get_status()
        score  = self.game.get_score()

        # Overlay slightly darkened
        self.canvas.create_rectangle(0, 0, CW, CH, fill="#000000", stipple="gray25", outline="")

        # Try to use existing button art for consistency
        pw, ph = 480, 220
        px     = (CW - pw) // 2
        py     = (CH - ph) // 2

        panel_fill = theme.get("bg", "#1a1a2e")
        panel_outline = theme.get("accent", "#4ade80")
        self.canvas.create_rectangle(px, py, px + pw, py + ph, fill=panel_fill, outline=panel_outline, width=3)

        # Title text (subtle)
        msg = "YOU WIN!" if status == "win" else "GAME OVER"
        title_color = theme.get("accent", "#facc15")
        self.canvas.create_text(CW // 2, py + 44, text=msg, font=self.title_font, fill=title_color, anchor=tk.CENTER)

        # Word & score line
        sub = f"Word: {self.game.word}   |   Score: {score} pts"
        self.canvas.create_text(CW // 2, py + 82, text=sub, font=self.body_font, fill=BASE_TEXT, anchor=tk.CENTER)

        # Use existing button PNGs where available
        play_img = self.loader.get_button("New_Game", width=220)
        menu_img = self.loader.get_button("Back", width=180)

        # Place Play Again button (image if available)
        if play_img:
            lbl = tk.Label(self.master, image=play_img, bg=panel_fill, borderwidth=0)
            lbl.image = play_img
            lbl.bind("<Button-1>", lambda e: self._start_game(self.difficulty))
            self.canvas.create_window(px + 110, py + 150, window=lbl)
        else:
            again_tag = "again_btn"
            self.canvas.create_rectangle(px + 60, py + 140, px + 240, py + 185, fill=theme["btn"], outline="")
            self.canvas.create_text(px + 150, py + 162, text="▶ Play Again", font=self.body_font, fill="#fff", tags=(again_tag,))
            self.canvas.tag_bind(again_tag, "<Button-1>", lambda e: self._start_game(self.difficulty))

        # Place Menu button (image if available)
        if menu_img:
            lbl2 = tk.Label(self.master, image=menu_img, bg=panel_fill, borderwidth=0)
            lbl2.image = menu_img
            lbl2.bind("<Button-1>", lambda e: self._show_main_menu())
            self.canvas.create_window(px + pw - 110, py + 150, window=lbl2)
        else:
            menu_tag = "end_menu_btn"
            self.canvas.create_rectangle(px + 260, py + 140, px + 420, py + 185, fill="#333", outline="")
            self.canvas.create_text(px + 340, py + 162, text="↩ Menu", font=self.body_font, fill="#ccc", tags=(menu_tag,))
            self.canvas.tag_bind(menu_tag, "<Button-1>", lambda e: self._show_main_menu())

    # ═════════════════════════════════════════════════════════════════════════
    # UTILS
    # ═════════════════════════════════════════════════════════════════════════
    
    def _clear(self):
        self._photo_refs.clear()
        self.master.unbind("<Key>")
        self.master.configure(bg=BASE_BG)
        for w in self.master.winfo_children():
            w.destroy()
    
    def _draw_canvas_background(self, canvas):
        if self.loader.bg_photo:
            canvas.create_image(
                0,
                0,
                anchor=tk.NW,
                image=self.loader.bg_photo
            )
            self._photo_refs.append(self.loader.bg_photo)

    def _center_window(self, w: int, h: int):
        self.master.update_idletasks()
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x  = (sw // 2) - (w // 2)
        y  = (sh // 2) - (h // 2)
        self.master.geometry(f"{w}x{h}+{x}+{y}")
    
    # ═════════════════════════════════════════════════════════════════════════
    # FULLSCREEN CONTROLS
    # ═════════════════════════════════════════════════════════════════════════
    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.master.attributes("-fullscreen", self.is_fullscreen)
        return "break"  # Prevents the event from propagating further

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.master.attributes("-fullscreen", False)
        return "break"
    
    def _on_window_resize(self, event):
        # Only trigger if the main window itself changes size
        if event.widget != self.master:
            return
            
        # Get the new dimensions of the window
        ww = event.width
        wh = event.height
        
        # If the background raw image exists, scale it edge-to-edge
        if hasattr(self.loader, 'bg_image_raw') and self.loader.bg_image_raw:
            resized_img = self.loader.bg_image_raw.resize((ww, wh), Image.LANCZOS)
            self._bg_photo_full = ImageTk.PhotoImage(resized_img)
            self.loader.bg_photo = self._bg_photo_full