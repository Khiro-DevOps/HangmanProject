import tkinter as tk
from gui import HangmanApp


def main():
    root = tk.Tk()
    app = HangmanApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()