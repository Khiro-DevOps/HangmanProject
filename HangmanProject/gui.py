import tkinter as tk
from tkinter import font as tkfont
from game_logic import HangmanGame
from word_bank import get_random_word, get_config

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
        stages = get_stages(self.game.max_attempts)

        self.master.geometry("520x620")
        self._center_window(520, 620)
        self.master.configure(bg=theme["bg"])

        root = tk.Frame(self.master, bg=theme["bg"], padx=18, pady=12)
        root.pack(fill=tk.BOTH, expand=True)

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

        # ── Hangman ASCII art ────────────────────────────────────────────────
        self.ascii_var = tk.StringVar()
        self.ascii_var.set(stages[-1])   # start at the "safe" stage
        tk.Label(root, textvariable=self.ascii_var, font=self.mono_font,
                 bg=theme["bg"], fg=theme["text"],
                 justify=tk.LEFT).pack(pady=(4, 4))

        # ── Word display ─────────────────────────────────────────────────────
        self.word_var = tk.StringVar()
        self.word_var.set(self.game.get_display_word())
        tk.Label(root, textvariable=self.word_var, font=self.word_font,
                 bg=theme["bg"], fg=theme["accent"],
                 letter_spacing=4).pack(pady=(4, 2))

        # ── Attempts & guessed ───────────────────────────────────────────────
        self.attempts_var = tk.StringVar()
        self.guessed_var  = tk.StringVar()
        self._refresh_info_vars()

        tk.Label(root, textvariable=self.attempts_var, font=self.body_font,
                 bg=theme["bg"], fg=theme["text"]).pack()
        tk.Label(root, textvariable=self.guessed_var, font=self.small_font,
                 bg=theme["bg"], fg="#aaa", wraplength=460).pack()

        # ── Timer (hard only) ────────────────────────────────────────────────
        self.timer_var = tk.StringVar(value="")
        self.timer_label = tk.Label(root, textvariable=self.timer_var,
                                    font=self.body_font, bg=theme["bg"], fg="#f87171")
        self.timer_label.pack()

        # ── Input row ────────────────────────────────────────────────────────
        inp = tk.Frame(root, bg=theme["bg"])
        inp.pack(pady=8)

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

        # ── Feedback label ───────────────────────────────────────────────────
        self.feedback_var = tk.StringVar(value="")
        self.feedback_lbl = tk.Label(root, textvariable=self.feedback_var,
                                     font=self.body_font, bg=theme["bg"],
                                     fg=theme["text"], wraplength=460)
        self.feedback_lbl.pack(pady=4)

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
        self.timer_var.set(f"⏱ {self._remaining_time}s remaining")
        self.timer_label.config(fg=color)
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
        self.word_var.set(self.game.get_display_word())
        self._refresh_info_vars()
        # update ASCII
        stages  = get_stages(self.game.max_attempts)
        wrongs  = self.game.max_attempts - self.game.remaining_attempts
        idx     = min(wrongs, len(stages) - 1)
        self.ascii_var.set(stages[-(idx + 1)])

    def _refresh_info_vars(self):
        hearts = "❤" * self.game.remaining_attempts + "🖤" * (
            self.game.max_attempts - self.game.remaining_attempts)
        self.attempts_var.set(f"{hearts}  ({self.game.remaining_attempts} left)")
        self.guessed_var.set(f"Guessed: {self.game.get_guessed_letters()}")

    def _set_feedback(self, msg: str, color: str = "#e5e5e5"):
        self.feedback_var.set(msg)
        self.feedback_lbl.config(fg=color)

    def _check_end(self):
        status = self.game.get_status()
        if status == "win":
            self._cancel_timer()
            self.timer_var.set("")
            score = self.game.get_score()
            self._set_feedback(
                f"🎉 YOU WIN!  Score: {score} pts\nWord was: {self.game.word}", "#4ade80")
            self._disable_input()
            self._show_play_again()
        elif status == "lose":
            self._cancel_timer()
            self.timer_var.set("")
            self.word_var.set(self.game.word)   # reveal word
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