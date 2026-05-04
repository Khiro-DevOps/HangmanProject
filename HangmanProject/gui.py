import tkinter as tk
from tkinter import font as tkfont
from game_logic import HangmanGame
from word_bank import get_random_word, get_config
import os
from PIL import Image, ImageTk

# ── Sprite loader (loads bg + slices sprite sheets) ─────────────────────────
class SpriteLoader:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.bg_photo = None
        self.frames = {"easy": [], "medium": [], "hard": []}
        self._load_bg()
        # map difficulty to (filename, frame_count)
        self._sheets = {
            "easy":   ("Rigby8.png", 8),
            "medium": ("Mordecai6.png", 6),
            "hard":   ("Benson4.png", 4),
        }
        self._frame_w = 300
        self._frame_h = 400
        self._load_sheets()

    def _load_bg(self):
        try:
            path = os.path.join(self.assets_dir, "housebg.jpg")
            img = Image.open(path).convert("RGBA")
            img = img.resize((800, 600), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img)
        except Exception:
            # missing bg -> leave None (canvas will use background color)
            self.bg_photo = None

    def _load_sheets(self):
        for diff, (fname, count) in self._sheets.items():
            path = os.path.join(self.assets_dir, fname)
            try:
                sheet = Image.open(path).convert("RGBA")
                frames = []
                for i in range(count):
                    box = (i * self._frame_w, 0, (i + 1) * self._frame_w, self._frame_h)
                    try:
                        frame = sheet.crop(box)
                    except Exception:
                        # fallback to blank frame on crop failure
                        frame = Image.new("RGBA", (self._frame_w, self._frame_h), (0, 0, 0, 0))
                    frames.append(ImageTk.PhotoImage(frame))
                self.frames[diff] = frames
            except Exception:
                # on missing sheet produce transparent placeholder frames
                placeholder = Image.new("RGBA", (self._frame_w, self._frame_h), (50, 50, 50, 255))
                self.frames[diff] = [ImageTk.PhotoImage(placeholder) for _ in range(count)]

    def get_bg(self):
        return self.bg_photo

    def get_frames(self, difficulty: str):
        return self.frames.get(difficulty, [])

# ── Hangman ASCII stages (easy=8, medium=6, hard=4) ──────────────────────────
STAGES = {
    8: [
        # 8 wrong → dead
        """
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
========""",
        """
  +---+
  |   |
  O   |
 /|\\  |
 /    |
      |
========""",
        """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
========""",
        """
  +---+
  |   |
  O   |
 /|   |
      |
      |
========""",
        """
  +---+
  |   |
  O   |
  |   |
      |
      |
========""",
        """
  +---+
  |   |
  O   |
      |
      |
      |
========""",
        """
  +---+
  |   |
      |
      |
      |
      |
========""",
        """
  +---+
      |
      |
      |
      |
      |
========""",
        """
       
      |
      |
      |
      |
      |
========""",
    ],
    6: [
        """
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
========""",
        """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
========""",
        """
  +---+
  |   |
  O   |
  |   |
      |
      |
========""",
        """
  +---+
  |   |
  O   |
      |
      |
      |
========""",
        """
  +---+
  |   |
      |
      |
      |
      |
========""",
        """
  +---+
      |
      |
      |
      |
      |
========""",
        """
       
      |
      |
      |
      |
      |
========""",
    ],
    4: [
        """
  +---+
  |   |
  O   |
 /|\\  |
 / \\  |
      |
========""",
        """
  +---+
  |   |
  O   |
 /|\\  |
      |
      |
========""",
        """
  +---+
  |   |
  O   |
      |
      |
      |
========""",
        """
  +---+
  |   |
      |
      |
      |
      |
========""",
        """
       
      |
      |
      |
      |
      |
========""",
    ],
}

# ── Colors ────────────────────────────────────────────────────────────────────
THEME = {
    "easy":   {"bg": "#1a2e1a", "accent": "#4ade80", "btn": "#16a34a", "text": "#dcfce7"},
    "medium": {"bg": "#1e1e2e", "accent": "#facc15", "btn": "#ca8a04", "text": "#fefce8"},
    "hard":   {"bg": "#2e1a1a", "accent": "#f87171", "btn": "#dc2626", "text": "#fee2e2"},
}
BASE_BG   = "#0f0f0f"
BASE_TEXT = "#e5e5e5"


def get_stages(max_attempts: int):
    """Return the correct stage list for the given max_attempts."""
    if max_attempts in STAGES:
        return STAGES[max_attempts]
    # fallback: use 6
    return STAGES[6]


class HangmanApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Hangman — Choose Your Fate")
        self.master.resizable(False, False)
        self.master.configure(bg=BASE_BG)

        self.mono_font  = tkfont.Font(family="Courier New", size=10)
        self.title_font = tkfont.Font(family="Courier New", size=20, weight="bold")
        self.word_font  = tkfont.Font(family="Courier New", size=22, weight="bold")
        self.body_font  = tkfont.Font(family="Courier New", size=11)
        self.small_font = tkfont.Font(family="Courier New", size=9)

        self.game: HangmanGame | None = None
        self.difficulty: str = "medium"
        self.timer_id = None   # after() id for countdown
        # sprite loader (assets folder sibling to this file)
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.sprite_loader = SpriteLoader(assets_dir)

        self._show_difficulty_screen()

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 1 — Difficulty Selection
    # ═════════════════════════════════════════════════════════════════════════
    def _show_difficulty_screen(self):
        self._cancel_timer()
        self._clear()
        self.master.geometry("460x380")
        self._center_window(460, 380)

        frame = tk.Frame(self.master, bg=BASE_BG, padx=30, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="⚰  HANGMAN", font=self.title_font,
                 bg=BASE_BG, fg=BASE_TEXT).pack(pady=(10, 4))
        tk.Label(frame, text="Choose your difficulty to begin",
                 font=self.small_font, bg=BASE_BG, fg="#888").pack(pady=(0, 20))

        configs = {
            "easy":   ("🟢  EASY",   "#4ade80"),
            "medium": ("🟡  MEDIUM", "#facc15"),
            "hard":   ("🔴  HARD",   "#f87171"),
        }

        for diff, (label, color) in configs.items():
            cfg = get_config(diff)
            btn_frame = tk.Frame(frame, bg="#1a1a1a", padx=14, pady=10,
                                 highlightbackground=color, highlightthickness=1)
            btn_frame.pack(fill=tk.X, pady=5)

            top = tk.Frame(btn_frame, bg="#1a1a1a")
            top.pack(fill=tk.X)

            tk.Label(top, text=label, font=self.body_font,
                     bg="#1a1a1a", fg=color).pack(side=tk.LEFT)

            tk.Button(top, text="PLAY →", font=self.small_font,
                      bg=color, fg="#0f0f0f", relief=tk.FLAT,
                      cursor="hand2", activebackground=color,
                      command=lambda d=diff: self._start_game(d)).pack(side=tk.RIGHT)

            tk.Label(btn_frame, text=cfg["description"], font=self.small_font,
                     bg="#1a1a1a", fg="#888").pack(anchor="w")

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 2 — Game Screen
    # ═════════════════════════════════════════════════════════════════════════
    def _start_game(self, difficulty: str):
        self._cancel_timer()
        self.difficulty = difficulty
        word, category = get_random_word(difficulty)
        self.game = HangmanGame(word, difficulty, category)
        self._show_game_screen()

    def _show_game_screen(self):
        self._cancel_timer()
        self._clear()

        theme  = THEME[self.difficulty]
        cfg    = get_config(self.difficulty)

        # Canvas window large enough for 800x600 canvas + controls below
        self.master.geometry("820x760")
        self._center_window(820, 760)
        self.master.configure(bg=theme["bg"])

        root = tk.Frame(self.master, bg=theme["bg"], padx=6, pady=6)
        root.pack(fill=tk.BOTH, expand=True)

        # ── Canvas (800x600) ───────────────────────────────────────────────
        self.canvas = tk.Canvas(root, width=800, height=600, bg=theme["bg"], highlightthickness=0)
        self.canvas.pack()
        # draw background if available
        self.bg_photo = self.sprite_loader.get_bg()
        if self.bg_photo:
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_photo)

        # prepare sprite frames for this difficulty
        self.sprite_frames = self.sprite_loader.get_frames(self.difficulty)
        # show initial sprite (0 wrongs)
        self.canvas_sprite = None
        if self.sprite_frames:
            # keep reference to current PhotoImage to avoid GC
            self.current_sprite_photo = self.sprite_frames[0]
            self.canvas_sprite = self.canvas.create_image(250, 50, anchor=tk.NW, image=self.current_sprite_photo)
        else:
            self.canvas_sprite = None

        # ── Canvas text elements: word, attempts, guessed, feedback, timer ──
        self.word_text = self.canvas.create_text(520, 120, text=self.game.get_display_word(),
                                                 font=self.word_font, fill=theme["accent"], anchor=tk.CENTER)

        self.attempts_text = self.canvas.create_text(520, 180, text="", font=self.body_font,
                                                     fill=theme["text"], anchor=tk.CENTER)
        self.guessed_text = self.canvas.create_text(520, 210, text="", font=self.small_font,
                                                    fill="#aaa", anchor=tk.CENTER)
        self.timer_text = self.canvas.create_text(760, 20, text="", font=self.body_font,
                                                  fill="#f87171", anchor=tk.NE)
        self.feedback_text = self.canvas.create_text(520, 250, text="", font=self.body_font,
                                                     fill=theme["text"], width=420, anchor=tk.N)

        # set initial text values
        self._refresh_info_vars()  # will update attempts/guessed via canvas below
        # update the displayed word explicitly
        self.canvas.itemconfig(self.word_text, text=self.game.get_display_word())

        # ── Header row ───────────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=theme["bg"])
        hdr.pack(fill=tk.X)

        diff_label = self.difficulty.upper()
        tk.Label(hdr, text=f"[ {diff_label} ]", font=self.body_font,
                 bg=theme["bg"], fg=theme["accent"]).pack(side=tk.LEFT)

        tk.Button(hdr, text="↩ Menu", font=self.small_font, relief=tk.FLAT,
                  bg=theme["bg"], fg="#888", cursor="hand2",
                  command=self._show_difficulty_screen).pack(side=tk.RIGHT)

        # ── Category (easy only) ─────────────────────────────────────────────
        self.category_var = tk.StringVar()
        cat_text = f"Category: {self.game.category}" if cfg["show_category"] else ""
        self.category_var.set(cat_text)
        tk.Label(root, textvariable=self.category_var, font=self.small_font,
                 bg=theme["bg"], fg="#aaa").pack(anchor="w")

        # ── Input row ────────────────────────────────────────────────────────
        inp = tk.Frame(root, bg=theme["bg"])
        inp.pack(pady=8, fill=tk.X)

        self.entry = tk.Entry(inp, font=self.word_font, width=3,
                              justify="center", bg="#1a1a1a",
                              fg=theme["accent"], insertbackground=theme["accent"],
                              relief=tk.FLAT, highlightthickness=1,
                              highlightbackground=theme["accent"])
        self.entry.pack(side=tk.LEFT, padx=6)
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self._on_guess())

        tk.Button(inp, text="GUESS", font=self.body_font, relief=tk.FLAT,
                  bg=theme["btn"], fg="#fff", cursor="hand2",
                  activebackground=theme["accent"],
                  command=self._on_guess).pack(side=tk.LEFT, padx=4)

        # ── Hint button (easy + medium) ───────────────────────────────────────
        if cfg["hint_available"]:
            self.hint_btn = tk.Button(inp, text="💡 HINT", font=self.body_font,
                                      relief=tk.FLAT, bg="#333", fg="#facc15",
                                      cursor="hand2", command=self._on_hint)
            self.hint_btn.pack(side=tk.LEFT, padx=4)

        # start timer if hard
        if cfg["timer_seconds"]:
            self._start_countdown(cfg["timer_seconds"])

    # ═════════════════════════════════════════════════════════════════════════
    # GAME ACTIONS
    # ═════════════════════════════════════════════════════════════════════════
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

        # reset timer on each successful guess (hard mode)
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

    # ═════════════════════════════════════════════════════════════════════════
    # TIMER (hard mode)
    # ═════════════════════════════════════════════════════════════════════════
    def _start_countdown(self, seconds: int):
        self._remaining_time = seconds
        self._tick()

    def _tick(self):
        if self._remaining_time <= 0:
            # Time's up — count as a wrong guess
            self.game.remaining_attempts -= 1
            self._set_feedback("⏱ Time's up! You lost an attempt.", "#f87171")
            self._refresh_display()
            if self.game.get_status() == "ongoing":
                self._start_countdown(get_config(self.difficulty)["timer_seconds"])
            else:
                self._check_end()
            return

        color = "#f87171" if self._remaining_time <= 10 else "#facc15"
        # update canvas timer text
        try:
            self.canvas.itemconfig(self.timer_text, text=f"⏱ {self._remaining_time}s remaining", fill=color)
        except Exception:
            pass
        self._remaining_time -= 1
        self.timer_id = self.master.after(1000, self._tick)

    def _cancel_timer(self):
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None

    # ═════════════════════════════════════════════════════════════════════════
    # DISPLAY HELPERS
    # ═════════════════════════════════════════════════════════════════════════
    def _refresh_display(self):
        # update word on canvas
        try:
            self.canvas.itemconfig(self.word_text, text=self.game.get_display_word())
        except Exception:
            pass
        # update attempts/guessed via helper
        self._refresh_info_vars()
        # update sprite based on wrong guesses
        wrongs = self.game.max_attempts - self.game.remaining_attempts
        if getattr(self, "sprite_frames", None):
            idx = min(wrongs, len(self.sprite_frames) - 1)
            self.current_sprite_photo = self.sprite_frames[idx]
            try:
                self.canvas.itemconfig(self.canvas_sprite, image=self.current_sprite_photo)
            except Exception:
                # if sprite not yet placed, create it
                self.canvas_sprite = self.canvas.create_image(250, 50, anchor=tk.NW, image=self.current_sprite_photo)
        # update timer text (in case of quick win/lose)
        cfg = get_config(self.difficulty)
        if cfg["timer_seconds"] and self.game.get_status() == "ongoing":
            self.canvas.itemconfig(self.timer_text, text=f"⏱ {self._remaining_time}s remaining")

    def _refresh_info_vars(self):
        hearts = "❤" * self.game.remaining_attempts + "🖤" * (
            self.game.max_attempts - self.game.remaining_attempts)
        attempts_text = f"{hearts}  ({self.game.remaining_attempts} left)"
        guessed_text = f"Guessed: {self.game.get_guessed_letters()}"
        try:
            self.canvas.itemconfig(self.attempts_text, text=attempts_text)
            self.canvas.itemconfig(self.guessed_text, text=guessed_text)
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
            self.timer_var.set("")
            score = self.game.get_score()
            self._set_feedback(f"🎉 YOU WIN!  Score: {score} pts\nWord was: {self.game.word}", "#4ade80")
            self._disable_input()
            self._show_play_again()
        elif status == "lose":
            self._cancel_timer()
            self.timer_var.set("")
            # reveal word on canvas
            try:
                self.canvas.itemconfig(self.word_text, text=self.game.word)
            except Exception:
                pass
            self._set_feedback(f"💀 GAME OVER!  Word was: {self.game.word}", "#f87171")
            self._disable_input()
            self._show_play_again()

    def _disable_input(self):
        self.entry.config(state=tk.DISABLED)

    def _show_play_again(self):
        theme = THEME[self.difficulty]
        frame = tk.Frame(self.master, bg=THEME[self.difficulty]["bg"])
        frame.pack(pady=6)
        tk.Button(frame, text="▶ Play Again", font=self.body_font, relief=tk.FLAT,
                  bg=theme["btn"], fg="#fff", cursor="hand2",
                  command=lambda: self._start_game(self.difficulty)).pack(side=tk.LEFT, padx=6)
        tk.Button(frame, text="↩ Menu", font=self.body_font, relief=tk.FLAT,
                  bg="#333", fg="#ccc", cursor="hand2",
                  command=self._show_difficulty_screen).pack(side=tk.LEFT, padx=6)

    # ═════════════════════════════════════════════════════════════════════════
    # UTILS
    # ═════════════════════════════════════════════════════════════════════════
    def _clear(self):
        for w in self.master.winfo_children():
            w.destroy()

    def _center_window(self, w: int, h: int):
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.master.winfo_screenheight() // 2) - (h // 2)
        self.master.geometry(f"{w}x{h}+{x}+{y}")