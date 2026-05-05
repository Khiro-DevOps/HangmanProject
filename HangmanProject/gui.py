import tkinter as tk
from tkinter import font as tkfont
from game_logic import HangmanGame
from word_bank import get_random_word, get_config
import os
from PIL import Image, ImageTk

# ── Sprite & Asset Loader ─────────────────────────────────────────────────────
class SpriteLoader:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.bg_photo = None
        self.frames = {"easy": [], "medium": [], "hard": []}
        self.buttons = {}

        self._sheets = {
            "easy":   ("Rigby8.png",    8),
            "medium": ("Mordecai6.png", 6),
            "hard":   ("Benson4.png",   4),
        }
        self._button_files = [
            "RegularGame.png",
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

    # ── Background ────────────────────────────────────────────────────────────
    def _load_bg(self):
        path = os.path.join(self.assets_dir, "housebg.jpg")
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize((800, 600), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img)
        except Exception:
            self.bg_photo = None

    # ── Sprite Sheets ─────────────────────────────────────────────────────────
    def _load_sheets(self):
        for diff, (fname, count) in self._sheets.items():
            path = os.path.join(self.assets_dir, fname)
            try:
                sheet = Image.open(path).convert("RGBA")
                sheet_w, sheet_h = sheet.size
                frame_w = sheet_w // count
                frames = []
                for i in range(count):
                    box = (i * frame_w, 0, (i + 1) * frame_w, sheet_h)
                    frame = sheet.crop(box)
                    frames.append(ImageTk.PhotoImage(frame))
                self.frames[diff] = frames
            except Exception:
                placeholder = Image.new("RGBA", (300, 400), (50, 50, 50, 180))
                self.frames[diff] = [ImageTk.PhotoImage(placeholder) for _ in range(count)]

    # ── Button PNGs ───────────────────────────────────────────────────────────
    def _load_buttons(self):
        for fname in self._button_files:
            key = fname.replace(".png", "")
            path = os.path.join(self.assets_dir, fname)
            try:
                img = Image.open(path).convert("RGBA")
                self.buttons[key] = img  # store as PIL Image so we can resize on demand
            except Exception:
                self.buttons[key] = None

    def get_button(self, key: str, width: int = None, height: int = None):
        """Return a resized ImageTk.PhotoImage for the button key."""
        img = self.buttons.get(key)
        if img is None:
            return None
        if width or height:
            orig_w, orig_h = img.size
            if width and not height:
                ratio = width / orig_w
                height = int(orig_h * ratio)
            elif height and not width:
                ratio = height / orig_h
                width = int(orig_w * ratio)
            img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def get_bg(self):
        return self.bg_photo

    def get_frames(self, difficulty: str):
        return self.frames.get(difficulty, [])


# ── Colors & Theme ────────────────────────────────────────────────────────────
THEME = {
    "easy":   {"bg": "#1a2e1a", "accent": "#4ade80", "btn": "#16a34a", "text": "#dcfce7"},
    "medium": {"bg": "#1e1e2e", "accent": "#facc15", "btn": "#ca8a04", "text": "#fefce8"},
    "hard":   {"bg": "#2e1a1a", "accent": "#f87171", "btn": "#dc2626", "text": "#fee2e2"},
}
BASE_BG   = "#0f0f0f"
BASE_TEXT = "#e5e5e5"


class HangmanApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Regular Hangman")
        self.master.resizable(False, False)
        self.master.configure(bg=BASE_BG)

        # Fonts
        self.title_font    = tkfont.Font(family="Courier New", size=20, weight="bold")
        self.word_font     = tkfont.Font(family="Courier New", size=22, weight="bold")
        self.body_font     = tkfont.Font(family="Courier New", size=11)
        self.small_font    = tkfont.Font(family="Courier New", size=9)

        self.game: HangmanGame | None = None
        self.difficulty: str = "medium"
        self.timer_id = None

        # Keep PhotoImage references alive (prevents garbage collection)
        self._photo_refs = []

        # Load all assets once
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.sprite_loader = SpriteLoader(assets_dir)

        self._show_main_menu()

    # ═══════════════════════════════════════════════════════════════════════════
    # SCREEN 0 — Main Menu
    # ═══════════════════════════════════════════════════════════════════════════
    def _show_main_menu(self):
        self._cancel_timer()
        self._clear()
        self.master.geometry("800x600")
        self._center_window(800, 600)

        canvas = tk.Canvas(self.master, width=800, height=600,
                           bg=BASE_BG, highlightthickness=0)
        canvas.pack()

        # Background
        bg = self.sprite_loader.get_bg()
        if bg:
            canvas.create_image(0, 0, anchor=tk.NW, image=bg)
            self._photo_refs.append(bg)

        # Title — RegularGame.png
        title_photo = self.sprite_loader.get_button("RegularGame", width=500)
        if title_photo:
            canvas.create_image(400, 110, anchor=tk.CENTER, image=title_photo)
            self._photo_refs.append(title_photo)
        else:
            canvas.create_text(400, 110, text="REGULAR HANGMAN",
                               font=self.title_font, fill=BASE_TEXT)

        # Menu buttons
        btn_data = [
            ("New_Game",          320, self._show_difficulty_screen),
            ("Change_Difficulty", 410, self._show_difficulty_screen),
            ("Exit_Game",         490, self.master.quit),
        ]
        for key, y, cmd in btn_data:
            photo = self.sprite_loader.get_button(key, width=280)
            if photo:
                lbl = tk.Label(canvas, image=photo, bg="", cursor="hand2",
                               borderwidth=0, highlightthickness=0)
                lbl.image = photo  # keep ref
                lbl.bind("<Button-1>", lambda e, c=cmd: c())
                canvas.create_window(400, y, window=lbl)
            else:
                # Fallback text button
                canvas.create_text(400, y, text=key.replace("_", " ").upper(),
                                   font=self.body_font, fill=BASE_TEXT,
                                   tags=(key,))
                canvas.tag_bind(key, "<Button-1>", lambda e, c=cmd: c())

    # ═══════════════════════════════════════════════════════════════════════════
    # SCREEN 1 — Difficulty Selection
    # ═══════════════════════════════════════════════════════════════════════════
    def _show_difficulty_screen(self):
        self._cancel_timer()
        self._clear()
        self.master.geometry("800x600")
        self._center_window(800, 600)

        canvas = tk.Canvas(self.master, width=800, height=600,
                           bg=BASE_BG, highlightthickness=0)
        canvas.pack()

        # Background
        bg = self.sprite_loader.get_bg()
        if bg:
            canvas.create_image(0, 0, anchor=tk.NW, image=bg)
            self._photo_refs.append(bg)

        # "Change Difficulty" header
        header_photo = self.sprite_loader.get_button("Change_Difficulty", width=420)
        if header_photo:
            canvas.create_image(400, 100, anchor=tk.CENTER, image=header_photo)
            self._photo_refs.append(header_photo)
        else:
            canvas.create_text(400, 100, text="CHANGE DIFFICULTY",
                               font=self.title_font, fill=BASE_TEXT)

        # Difficulty buttons
        diff_data = [
            ("Easy",   "easy",   250),
            ("Medium", "medium", 360),
            ("Hard",   "hard",   470),
        ]
        for key, diff, y in diff_data:
            photo = self.sprite_loader.get_button(key, width=220)
            if photo:
                lbl = tk.Label(canvas, image=photo, bg="", cursor="hand2",
                               borderwidth=0, highlightthickness=0)
                lbl.image = photo
                lbl.bind("<Button-1>", lambda e, d=diff: self._start_game(d))
                canvas.create_window(400, y, window=lbl)
            else:
                canvas.create_text(400, y, text=key.upper(),
                                   font=self.body_font, fill=BASE_TEXT,
                                   tags=(key,))
                canvas.tag_bind(key, "<Button-1>",
                                lambda e, d=diff: self._start_game(d))

        # Back button
        back_photo = self.sprite_loader.get_button("Back", width=140)
        if back_photo:
            lbl = tk.Label(canvas, image=back_photo, bg="", cursor="hand2",
                           borderwidth=0, highlightthickness=0)
            lbl.image = back_photo
            lbl.bind("<Button-1>", lambda e: self._show_main_menu())
            canvas.create_window(100, 550, window=lbl)
        else:
            canvas.create_text(80, 560, text="← BACK",
                               font=self.small_font, fill="#aaa",
                               tags="back")
            canvas.tag_bind("back", "<Button-1>", lambda e: self._show_main_menu())

    # ═══════════════════════════════════════════════════════════════════════════
    # SCREEN 2 — Game Screen
    # ═══════════════════════════════════════════════════════════════════════════
    def _start_game(self, difficulty: str):
        self._cancel_timer()
        self.difficulty = difficulty
        word, category = get_random_word(difficulty)
        self.game = HangmanGame(word, difficulty, category)
        self._show_game_screen()

    def _show_game_screen(self):
        self._cancel_timer()
        self._clear()

        theme = THEME[self.difficulty]
        cfg   = get_config(self.difficulty)

        self.master.geometry("820x760")
        self._center_window(820, 760)
        self.master.configure(bg=theme["bg"])

        root = tk.Frame(self.master, bg=theme["bg"], padx=6, pady=6)
        root.pack(fill=tk.BOTH, expand=True)

        # ── Canvas ────────────────────────────────────────────────────────────
        self.canvas = tk.Canvas(root, width=800, height=600,
                                bg=theme["bg"], highlightthickness=0)
        self.canvas.pack()

        # Background
        self.bg_photo = self.sprite_loader.get_bg()
        if self.bg_photo:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)

        # Sprite — show frame 0 (no wrong guesses yet)
        self.sprite_frames = self.sprite_loader.get_frames(self.difficulty)
        self.canvas_sprite = None
        if self.sprite_frames:
            self.current_sprite_photo = self.sprite_frames[0]
            self.canvas_sprite = self.canvas.create_image(
                250, 50, anchor=tk.NW, image=self.current_sprite_photo)

        # ── Canvas text elements ───────────────────────────────────────────────
        self.word_text = self.canvas.create_text(
            520, 120, text=self.game.get_display_word(),
            font=self.word_font, fill=theme["accent"], anchor=tk.CENTER)

        self.attempts_text = self.canvas.create_text(
            520, 180, text="", font=self.body_font,
            fill=theme["text"], anchor=tk.CENTER)

        self.guessed_text = self.canvas.create_text(
            520, 210, text="", font=self.small_font,
            fill="#aaa", anchor=tk.CENTER)

        self.timer_text = self.canvas.create_text(
            760, 20, text="", font=self.body_font,
            fill="#f87171", anchor=tk.NE)

        self.feedback_text = self.canvas.create_text(
            520, 250, text="", font=self.body_font,
            fill=theme["text"], width=420, anchor=tk.N)

        self._refresh_info_vars()

        # ── Header row ─────────────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=theme["bg"])
        hdr.pack(fill=tk.X)

        tk.Label(hdr, text=f"[ {self.difficulty.upper()} ]",
                 font=self.body_font, bg=theme["bg"],
                 fg=theme["accent"]).pack(side=tk.LEFT)

        tk.Button(hdr, text="↩ Menu", font=self.small_font,
                  relief=tk.FLAT, bg=theme["bg"], fg="#888",
                  cursor="hand2",
                  command=self._show_main_menu).pack(side=tk.RIGHT)

        # ── Category label (easy only) ─────────────────────────────────────────
        cat_text = f"Category: {self.game.category}" if cfg["show_category"] else ""
        self.category_label = tk.Label(root, text=cat_text,
                                       font=self.small_font,
                                       bg=theme["bg"], fg="#aaa")
        self.category_label.pack(anchor="w")

        # ── Input row ──────────────────────────────────────────────────────────
        inp = tk.Frame(root, bg=theme["bg"])
        inp.pack(pady=8, fill=tk.X)

        self.entry = tk.Entry(inp, font=self.word_font, width=3,
                              justify="center", bg="#1a1a1a",
                              fg=theme["accent"],
                              insertbackground=theme["accent"],
                              relief=tk.FLAT, highlightthickness=1,
                              highlightbackground=theme["accent"])
        self.entry.pack(side=tk.LEFT, padx=6)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self._on_guess())

        tk.Button(inp, text="GUESS", font=self.body_font,
                  relief=tk.FLAT, bg=theme["btn"], fg="#fff",
                  cursor="hand2", activebackground=theme["accent"],
                  command=self._on_guess).pack(side=tk.LEFT, padx=4)

        # ── Hint button (easy + medium) ────────────────────────────────────────
        if cfg["hint_available"]:
            self.hint_btn = tk.Button(inp, text="💡 HINT",
                                      font=self.body_font,
                                      relief=tk.FLAT, bg="#333",
                                      fg="#facc15", cursor="hand2",
                                      command=self._on_hint)
            self.hint_btn.pack(side=tk.LEFT, padx=4)

        # ── Start countdown for hard ───────────────────────────────────────────
        if cfg["timer_seconds"]:
            self._start_countdown(cfg["timer_seconds"])

    # ═══════════════════════════════════════════════════════════════════════════
    # GAME ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    def _on_guess(self):
        guess = self.entry.get().strip().upper()
        self.entry.delete(0, tk.END)

        if not guess or len(guess) != 1 or not guess.isalpha():
            self._set_feedback("⚠ Enter a single letter.", "#f87171")
            return

        result = self.game.guess(guess)
        self._refresh_display()

        if result == "already":
            self._set_feedback(f"'{guess}' was already guessed.", "#aaa")
        elif result == "wrong":
            self._set_feedback(f"✗  '{guess}' is not in the word!", "#f87171")
        else:
            self._set_feedback(f"✓  '{guess}' is correct!", "#4ade80")

        self._check_end()

        cfg = get_config(self.difficulty)
        if cfg["timer_seconds"] and self.game.get_status() == "ongoing":
            self._cancel_timer()
            self._start_countdown(cfg["timer_seconds"])

    def _on_hint(self):
        letter = self.game.use_hint()
        if letter:
            self._set_feedback(f"💡 Hint: '{letter}' has been revealed!", "#facc15")
            self._refresh_display()
            if hasattr(self, "hint_btn"):
                self.hint_btn.config(state=tk.DISABLED, fg="#555")
            self._check_end()
        else:
            self._set_feedback("No hints available.", "#aaa")

    # ═══════════════════════════════════════════════════════════════════════════
    # TIMER (hard mode only)
    # ═══════════════════════════════════════════════════════════════════════════
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
            self.canvas.itemconfig(
                self.timer_text,
                text=f"⏱ {self._remaining_time}s remaining",
                fill=color)
        except Exception:
            pass

        self._remaining_time -= 1
        self.timer_id = self.master.after(1000, self._tick)

    def _cancel_timer(self):
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    def _refresh_display(self):
        # Update word display
        try:
            self.canvas.itemconfig(self.word_text,
                                   text=self.game.get_display_word())
        except Exception:
            pass

        self._refresh_info_vars()

        # Swap sprite frame based on wrong guess count
        wrongs = self.game.max_attempts - self.game.remaining_attempts
        if getattr(self, "sprite_frames", None):
            idx = min(wrongs, len(self.sprite_frames) - 1)
            self.current_sprite_photo = self.sprite_frames[idx]
            try:
                self.canvas.itemconfig(self.canvas_sprite,
                                       image=self.current_sprite_photo)
            except Exception:
                self.canvas_sprite = self.canvas.create_image(
                    250, 50, anchor=tk.NW, image=self.current_sprite_photo)

    def _refresh_info_vars(self):
        hearts = ("❤" * self.game.remaining_attempts +
                  "🖤" * (self.game.max_attempts - self.game.remaining_attempts))
        attempts_text = f"{hearts}  ({self.game.remaining_attempts} left)"
        guessed_text  = f"Guessed: {self.game.get_guessed_letters()}"
        try:
            self.canvas.itemconfig(self.attempts_text, text=attempts_text)
            self.canvas.itemconfig(self.guessed_text,  text=guessed_text)
        except Exception:
            pass

    def _set_feedback(self, msg: str, color: str = "#e5e5e5"):
        try:
            self.canvas.itemconfig(self.feedback_text, text=msg, fill=color)
        except Exception:
            pass

    def _check_end(self):
        status = self.game.get_status()
        if status == "win":
            self._cancel_timer()
            # Clear timer display
            try:
                self.canvas.itemconfig(self.timer_text, text="")
            except Exception:
                pass
            score = self.game.get_score()
            self._set_feedback(
                f"🎉 YOU WIN!  Score: {score} pts\nWord was: {self.game.word}",
                "#4ade80")
            self._disable_input()
            self._show_play_again()

        elif status == "lose":
            self._cancel_timer()
            # Clear timer display
            try:
                self.canvas.itemconfig(self.timer_text, text="")
            except Exception:
                pass
            # Show full word on loss
            try:
                self.canvas.itemconfig(self.word_text, text=self.game.word)
            except Exception:
                pass
            self._set_feedback(
                f"💀 GAME OVER!  Word was: {self.game.word}",
                "#f87171")
            self._disable_input()
            self._show_play_again()

    def _disable_input(self):
        try:
            self.entry.config(state=tk.DISABLED)
        except Exception:
            pass

    def _show_play_again(self):
        theme = THEME[self.difficulty]
        frame = tk.Frame(self.master, bg=theme["bg"])
        frame.pack(pady=6)

        tk.Button(frame, text="▶ Play Again", font=self.body_font,
                  relief=tk.FLAT, bg=theme["btn"], fg="#fff",
                  cursor="hand2",
                  command=lambda: self._start_game(self.difficulty)
                  ).pack(side=tk.LEFT, padx=6)

        tk.Button(frame, text="↩ Menu", font=self.body_font,
                  relief=tk.FLAT, bg="#333", fg="#ccc",
                  cursor="hand2",
                  command=self._show_main_menu
                  ).pack(side=tk.LEFT, padx=6)

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILS
    # ═══════════════════════════════════════════════════════════════════════════
    def _clear(self):
        self._photo_refs.clear()
        for w in self.master.winfo_children():
            w.destroy()

    def _center_window(self, w: int, h: int):
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.master.winfo_screenheight() // 2) - (h // 2)
        self.master.geometry(f"{w}x{h}+{x}+{y}")