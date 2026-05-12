import tkinter as tk
from tkinter import font as tkfont
from game_logic import HangmanGame
from word_bank import get_random_word, get_config
import os
from PIL import Image, ImageTk

# ── QWERTY layout ─────────────────────────────────────────────────────────────
QWERTY = [
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]

# ── Per-character display sizes (preserves aspect ratio at same height) ────────
TARGET_SIZES = {
    "easy":   (366, 352),
    "medium": (489, 352),
    "hard":   (472, 352),
}

# ── Canvas dimensions ─────────────────────────────────────────────────────────
CW, CH = 900, 650   # canvas width, height

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
        self.bg_menu    = None
        self.bg_game    = None
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
            "Back.png",
        ]

        self._load_bg()
        self._load_sheets()
        self._load_buttons()
        self._load_keyboard()
        self._load_hearts()

    # ── Background ────────────────────────────────────────────────────────────
    def _load_bg(self):
        path = os.path.join(self.assets_dir, "housebg.jpg")
        try:
            img = Image.open(path).convert("RGBA")
            self.bg_menu = ImageTk.PhotoImage(img.resize((800, 600), Image.LANCZOS))
            self.bg_game = ImageTk.PhotoImage(img.resize((CW, CH),   Image.LANCZOS))
        except Exception:
            self.bg_menu = None
            self.bg_game = None

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

    # ── Button PNGs ───────────────────────────────────────────────────────────
    def _load_buttons(self):
        for fname in self._button_files:
            key  = fname.replace(".png", "")
            path = os.path.join(self.assets_dir, fname)
            try:
                self.buttons[key] = Image.open(path).convert("RGBA")
            except Exception:
                self.buttons[key] = None

    # ── Keyboard images ───────────────────────────────────────────────────────
    def _load_keyboard(self):
        kb_w = CW - 200
        for key, fname in [("kb_normal", "keyboard_normal.png"),
                            ("kb_used",   "keyboard_key_used.png")]:
            path = os.path.join(self.assets_dir, fname)
            try:
                img    = Image.open(path).convert("RGBA")
                ow, oh = img.size
                ratio  = kb_w / ow
                kb_h   = int(oh * ratio)
                img    = img.resize((kb_w, kb_h), Image.LANCZOS)

                # ── Fix: composite onto transparent base to kill checkerboard ──
                base = Image.new("RGBA", (kb_w, kb_h), (0, 0, 0, 0))
                img  = Image.alpha_composite(base, img)

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
                img = Image.open(path).convert("RGBA").resize(HEART_SIZE, Image.LANCZOS)
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


# ═════════════════════════════════════════════════════════════════════════════
# APP
# ═════════════════════════════════════════════════════════════════════════════
class HangmanApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Regular Hangman")
        self.master.resizable(False, False)
        self.master.configure(bg=BASE_BG)

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

        self._show_main_menu()

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 0 — Main Menu
    # ═════════════════════════════════════════════════════════════════════════
    def _show_main_menu(self):
        self._cancel_timer()
        self._clear()
        self.master.geometry("800x600")
        self._center_window(800, 600)

        canvas = tk.Canvas(self.master, width=800, height=600,
                           bg=BASE_BG, highlightthickness=0)
        canvas.pack()

        if self.loader.bg_menu:
            canvas.create_image(0, 0, anchor=tk.NW, image=self.loader.bg_menu)
            self._photo_refs.append(self.loader.bg_menu)

        title = self.loader.get_button("Regular_Game", width=500)
        if title:
            canvas.create_image(400, 110, anchor=tk.CENTER, image=title)
            self._photo_refs.append(title)
        else:
            canvas.create_text(400, 110, text="REGULAR GAME",
                               font=self.title_font, fill=BASE_TEXT)

        btn_data = [
            ("New_Game",          300, lambda: self._start_game(self.difficulty)),
            ("Change_Difficulty", 390, self._show_difficulty_screen),
            ("Exit_Game",         490, self.master.quit),
        ]
        for key, y, cmd in btn_data:
            photo = self.loader.get_button(key, width=280)
            if photo:
                lbl = tk.Label(canvas, image=photo, bg="#0f0f0f",
                               cursor="hand2", borderwidth=0, highlightthickness=0)
                lbl.image = photo
                lbl.bind("<Button-1>", lambda e, c=cmd: c())
                canvas.create_window(400, y, window=lbl)
            else:
                tag = f"btn_{key}"
                canvas.create_text(400, y, text=key.replace("_", " ").upper(),
                                   font=self.body_font, fill=BASE_TEXT, tags=(tag,))
                canvas.tag_bind(tag, "<Button-1>", lambda e, c=cmd: c())

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 1 — Difficulty Selection
    # ═════════════════════════════════════════════════════════════════════════
    def _show_difficulty_screen(self):
        self._cancel_timer()
        self._clear()
        self.master.geometry("800x600")
        self._center_window(800, 600)

        canvas = tk.Canvas(self.master, width=800, height=600,
                           bg=BASE_BG, highlightthickness=0)
        canvas.pack()

        if self.loader.bg_menu:
            canvas.create_image(0, 0, anchor=tk.NW, image=self.loader.bg_menu)
            self._photo_refs.append(self.loader.bg_menu)

        hdr = self.loader.get_button("Change_Difficulty", width=420)
        if hdr:
            canvas.create_image(400, 100, anchor=tk.CENTER, image=hdr)
            self._photo_refs.append(hdr)
        else:
            canvas.create_text(400, 100, text="CHANGE DIFFICULTY",
                               font=self.title_font, fill=BASE_TEXT)

        diff_data = [
            ("Easy",   "easy",   240),
            ("Medium", "medium", 360),
            ("Hard",   "hard",   470),
        ]
        for key, diff, y in diff_data:
            photo = self.loader.get_button(key, width=220)
            if photo:
                lbl = tk.Label(canvas, image=photo, bg="#0f0f0f",
                               cursor="hand2", borderwidth=0, highlightthickness=0)
                lbl.image = photo
                lbl.bind("<Button-1>", lambda e, d=diff: self._start_game(d))
                canvas.create_window(400, y, window=lbl)
            else:
                tag = f"diff_{key}"
                canvas.create_text(400, y, text=key.upper(),
                                   font=self.body_font, fill=BASE_TEXT, tags=(tag,))
                canvas.tag_bind(tag, "<Button-1>", lambda e, d=diff: self._start_game(d))

        back = self.loader.get_button("Back", width=130)
        if back:
            lbl = tk.Label(canvas, image=back, bg="#0f0f0f",
                           cursor="hand2", borderwidth=0, highlightthickness=0)
            lbl.image = back
            lbl.bind("<Button-1>", lambda e: self._show_main_menu())
            canvas.create_window(80, 560, window=lbl)
        else:
            canvas.create_text(80, 560, text="← BACK",
                               font=self.small_font, fill="#aaa", tags=("back",))
            canvas.tag_bind("back", "<Button-1>", lambda e: self._show_main_menu())

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 2 — Game Screen
    # ═════════════════════════════════════════════════════════════════════════
    def _start_game(self, difficulty: str):
        self._cancel_timer()
        self.difficulty = difficulty
        word, category  = get_random_word(difficulty)
        self.game       = HangmanGame(word, difficulty, category)
        self._show_game_screen()

    def _show_game_screen(self):
        self._cancel_timer()
        self._clear()

        theme = THEME[self.difficulty]
        cfg   = get_config(self.difficulty)

        self.master.geometry(f"{CW}x{CH}")
        self._center_window(CW, CH)
        self.master.configure(bg=theme["bg"])

        self.canvas = tk.Canvas(self.master, width=CW, height=CH,
                                bg=theme["bg"], highlightthickness=0)
        self.canvas.pack()

        # Background
        if self.loader.bg_game:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.loader.bg_game)
            self._photo_refs.append(self.loader.bg_game)

        # ── Layout constants ──────────────────────────────────────────────────
        KB_H       = self.loader.kb_size[1]
        KB_Y       = CH - KB_H - 10
        CHAR_Y     = KB_Y - TARGET_SIZES[self.difficulty][1] + 20
        HEART_Y    = 12
        WORD_Y     = 90
        RIGHT_X    = 510
        FEEDBACK_Y = WORD_Y + 110

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
        self.canvas.create_text(
            CW - 10, 14, text=f"[ {self.difficulty.upper()} ]",
            font=self.body_font, fill=theme["accent"], anchor=tk.NE)

        menu_tag = "menu_btn"
        self.canvas.create_text(
            CW - 10, 34, text="↩ Menu",
            font=self.small_font, fill="#aaa", anchor=tk.NE, tags=(menu_tag,))
        self.canvas.tag_bind(menu_tag, "<Button-1>",
                             lambda e: self._show_main_menu())

        # ── Category (easy only) ──────────────────────────────────────────────
        if cfg["show_category"]:
            self.canvas.create_text(
                CW - 10, 54, text=f"Category: {self.game.category}",
                font=self.small_font, fill="#aaa", anchor=tk.NE)

        # ── Timer text (hard mode) ────────────────────────────────────────────
        self.timer_text = self.canvas.create_text(
            CW - 10, 72, text="",
            font=self.body_font, fill="#f87171", anchor=tk.NE)

        # ── Word letter boxes (right panel) ───────────────────────────────────
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
        word         = self.game.word
        panel_w      = CW - start_x - 10

        # Scale box size down for longer words so they always fit
        if len(word) <= 5:
            box_w, box_h = 44, 50
            gap          = 6
        elif len(word) <= 8:
            box_w, box_h = 36, 44
            gap          = 5
        elif len(word) <= 12:
            box_w, box_h = 28, 36
            gap          = 4
        else:
            box_w, box_h = 22, 30
            gap          = 3

        total_w = len(word) * (box_w + gap) - gap

        # If still too wide, force fit
        if total_w > panel_w:
            box_w = (panel_w - (len(word) - 1) * gap) // len(word)
            box_h = int(box_w * 1.1)
            total_w = len(word) * (box_w + gap) - gap

        # Center in right panel
        ox = start_x + (panel_w - total_w) // 2

        self._letter_boxes  = []
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

        kw, kh     = self.loader.kb_size
        rows       = QWERTY
        max_keys   = max(len(r) for r in rows)

        # Each key is square — calculate from image width / max keys in a row
        key_w = kw / max_keys
        key_h = kh / len(rows)

        # QWERTY row indent — row 2 indented 0.5 key, row 3 indented 1.5 keys
        row_offsets = [0, key_w * 0.5, key_w * 1.5]

        self._key_regions: dict[str, tuple] = {}
        self._kb_x = kb_x  # store kb_x so overlay uses same origin

        for ri, row in enumerate(rows):
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
            score = self.game.get_score()
            self._set_feedback(f"🎉 YOU WIN!  Score: {score} pts", "#4ade80")
            self._unbind_input()
            self._show_play_again()

        elif status == "lose":
            self._cancel_timer()
            try:
                self.canvas.itemconfig(self.timer_text, text="")
            except Exception:
                pass
            for rect, txt, letter in self._letter_boxes:
                self.canvas.itemconfig(txt, text=letter)
            self._set_feedback(
                f"💀 GAME OVER!  Word was: {self.game.word}", "#f87171")
            self._unbind_input()
            self._show_play_again()

    def _unbind_input(self):
        self.master.unbind("<Key>")
        self.canvas.unbind("<Button-1>")

    def _show_play_again(self):
        theme = THEME[self.difficulty]

        # Semi-transparent dark overlay over whole canvas
        self.canvas.create_rectangle(
            0, 0, CW, CH,
            fill="#000000", stipple="gray50", outline="")

        # Popup box — dead center
        pw, ph = 400, 200
        px = (CW - pw) // 2
        py = (CH - ph) // 2

        # Popup background
        self.canvas.create_rectangle(
            px, py, px + pw, py + ph,
            fill="#1a1a2e", outline=theme["accent"], width=3)

        # Status message already shown via feedback — add word reveal
        status = self.game.get_status()
        msg    = "🎉 YOU WIN!" if status == "win" else "💀 GAME OVER"
        color  = "#4ade80"    if status == "win" else "#f87171"

        self.canvas.create_text(
            CW // 2, py + 45,
            text=msg, font=self.title_font,
            fill=color, anchor=tk.CENTER)

        self.canvas.create_text(
            CW // 2, py + 85,
            text=f"Word: {self.game.word}",
            font=self.body_font, fill=BASE_TEXT,
            anchor=tk.CENTER)

        # Play Again button
        again_tag = "again_btn"
        self.canvas.create_rectangle(
            px + 20, py + 130, px + 175, py + 170,
            fill=theme["btn"], outline="")
        self.canvas.create_text(
            px + 97, py + 150,
            text="▶ Play Again", font=self.body_font,
            fill="#fff", tags=(again_tag,), anchor=tk.CENTER)
        self.canvas.tag_bind(again_tag, "<Button-1>",
                             lambda e: self._start_game(self.difficulty))

        # Menu button
        menu_tag = "end_menu_btn"
        self.canvas.create_rectangle(
            px + 225, py + 130, px + 380, py + 170,
            fill="#333", outline="")
        self.canvas.create_text(
            px + 302, py + 150,
            text="↩ Menu", font=self.body_font,
            fill="#ccc", tags=(menu_tag,), anchor=tk.CENTER)
        self.canvas.tag_bind(menu_tag, "<Button-1>",
                             lambda e: self._show_main_menu())

    # ═════════════════════════════════════════════════════════════════════════
    # UTILS
    # ═════════════════════════════════════════════════════════════════════════
    def _clear(self):
        self._photo_refs.clear()
        self.master.unbind("<Key>")
        for w in self.master.winfo_children():
            w.destroy()

    def _center_window(self, w: int, h: int):
        self.master.update_idletasks()
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x  = (sw // 2) - (w // 2)
        y  = (sh // 2) - (h // 2)
        self.master.geometry(f"{w}x{h}+{x}+{y}")