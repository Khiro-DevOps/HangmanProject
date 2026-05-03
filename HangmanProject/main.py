import tkinter as tk
from gui import HangmanGUI
from word_bank import get_random_word


def main():
    root = tk.Tk()
    word = get_random_word()
    app = HangmanGUI(root)
    app.game.word = word.upper()
    app.game.guessed_letters = []
    app.game.remaining_attempts = 6
    app._update_display()
    root.mainloop()


if __name__ == "__main__":
    main()