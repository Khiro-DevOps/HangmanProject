import tkinter as tk
from tkinter import font
from game_logic import HangmanGame


class HangmanGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("Hangman Game")
        self.master.resizable(False, False)

        self.width = 420
        self.height = 300
        self._center_window()

        self.title_font = font.Font(family="Arial", size=16, weight="bold")
        self.body_font = font.Font(family="Arial", size=12)

        # Game instance
        self.game = HangmanGame()

        # UI variables
        self.word_var = tk.StringVar()
        self.info_var = tk.StringVar()

        self._build_ui()
        self._update_display()

    def _center_window(self):
        self.master.geometry(f"{self.width}x{self.height}")
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth() // 2) - (self.width // 2)
        y = (self.master.winfo_screenheight() // 2) - (self.height // 2)
        self.master.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _build_ui(self):
        container = tk.Frame(self.master, padx=12, pady=12)
        container.pack(fill=tk.BOTH, expand=True)

        # Title
        tk.Label(container, text="Hangman Game", font=self.title_font).pack()

        # Word display
        tk.Label(container, textvariable=self.word_var, font=("Arial", 18)).pack(pady=10)

        # Input
        input_frame = tk.Frame(container)
        input_frame.pack()

        self.entry = tk.Entry(input_frame, font=self.body_font, width=5, justify="center")
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.focus()

        tk.Button(input_frame, text="Guess", command=self.on_submit).pack(side=tk.LEFT)

        # Info display
        tk.Label(container, textvariable=self.info_var, font=self.body_font, justify=tk.LEFT).pack(pady=10)

    def _update_display(self):
        self.word_var.set(self.game.get_display_word())

        info = (
            f"Attempts left: {self.game.remaining_attempts}\n"
            f"Guessed: {self.game.get_guessed_letters()}"
        )

        self.info_var.set(info)

    def on_submit(self):
        guess = self.entry.get().strip().upper()
        self.entry.delete(0, tk.END)

        if not guess or len(guess) != 1 or not guess.isalpha():
            self.info_var.set("Enter a single valid letter.")
            return

        result = self.game.guess(guess)
        status = self.game.get_status()

        self._update_display()

        if result == "already":
            self.info_var.set(self.info_var.get() + f"\n'{guess}' already guessed.")
        elif result == "wrong":
            self.info_var.set(self.info_var.get() + f"\n'{guess}' is wrong.")
        else:
            self.info_var.set(self.info_var.get() + f"\n'{guess}' is correct!")

        if status == "win":
            self.info_var.set(self.info_var.get() + "\n🎉 You win!")
        elif status == "lose":
            self.info_var.set(self.info_var.get() + f"\n💀 You lose! Word was: {self.game.word}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HangmanGUI(root)
    root.mainloop()