import tkinter as tk
from tkinter import font


class HangmanGUI:
	"""A clean, modular Tkinter GUI for a Hangman game.

	Responsibilities:
	- Build and layout UI components
	- Handle user input events and update the UI
	"""

	def __init__(self, master: tk.Tk) -> None:
		self.master = master
		self.master.title("Hangman Game")
		self.master.resizable(False, False)

		# Fixed window size
		self.width = 400
		self.height = 250
		self._center_window()

		# Fonts
		self.title_font = font.Font(family="Arial", size=16, weight="bold")
		self.body_font = font.Font(family="Arial", size=12)

		# State variables
		self.output_var = tk.StringVar(value="Welcome to Hangman!")

		# Setup UI
		self._build_ui()

	def _center_window(self) -> None:
		self.master.geometry(f"{self.width}x{self.height}")
		self.master.update_idletasks()
		screen_width = self.master.winfo_screenwidth()
		screen_height = self.master.winfo_screenheight()
		x = (screen_width // 2) - (self.width // 2)
		y = (screen_height // 2) - (self.height // 2)
		self.master.geometry(f"{self.width}x{self.height}+{x}+{y}")

	def _build_ui(self) -> None:
		container = tk.Frame(self.master, padx=12, pady=12)
		container.pack(fill=tk.BOTH, expand=True)

		# Title label
		title_label = tk.Label(
			container,
			text="Hangman Game",
			font=self.title_font,
			pady=6,
		)
		title_label.pack(anchor=tk.N)

		# Input frame
		input_frame = tk.Frame(container, pady=10)
		input_frame.pack(fill=tk.X)

		self.entry = tk.Entry(input_frame, font=self.body_font)
		self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
		self.entry.focus_set()

		submit_button = tk.Button(
			input_frame,
			text="Submit",
			font=self.body_font,
			width=10,
			command=self.on_submit,
		)
		submit_button.pack(side=tk.RIGHT)

		# Output label
		output_label = tk.Label(
			container,
			textvariable=self.output_var,
			font=self.body_font,
			anchor=tk.W,
			justify=tk.LEFT,
			wraplength=self.width - 24,
			pady=6,
		)
		output_label.pack(fill=tk.X)

	def on_submit(self) -> None:
		"""Handle Submit button click: read input, clear, and update output label."""
		guess = self.entry.get().strip()
		# Clear the input field after capturing value
		self.entry.delete(0, tk.END)

		if not guess:
			self.output_var.set("Please enter a guess.")
			return

		# Update GUI output with entered value (no print statements)
		self.output_var.set(f"You entered: {guess}")


if __name__ == "__main__":
	root = tk.Tk()
	app = HangmanGUI(root)
	root.mainloop()

