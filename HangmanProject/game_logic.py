from word_bank import get_config, get_hint


class HangmanGame:
    def __init__(self, word: str = "PYTHON", difficulty: str = "medium", category: str = ""):
        self.word = word.upper()
        self.difficulty = difficulty
        self.category = category

        config = get_config(difficulty)
        self.max_attempts = config["attempts"]
        self.remaining_attempts = self.max_attempts
        self.hint_available = config["hint_available"]
        self.timer_seconds = config["timer_seconds"]
        self.show_category = config["show_category"]

        self.guessed_letters: list[str] = []
        self.hint_used: bool = False

    # ── Core guess logic ──────────────────────────────────────────────────────
    def guess(self, letter: str) -> str:
        """Returns: 'already' | 'wrong' | 'correct'"""
        letter = letter.upper()

        if letter in self.guessed_letters:
            return "already"

        self.guessed_letters.append(letter)

        if letter not in self.word:
            self.remaining_attempts -= 1
            return "wrong"

        return "correct"

    # ── Hint ──────────────────────────────────────────────────────────────────
    def use_hint(self) -> str | None:
        """Returns a revealed letter, or None if unavailable/already used."""
        if not self.hint_available or self.hint_used:
            return None
        letter = get_hint(self.word, self.guessed_letters)
        if letter:
            self.hint_used = True
            self.guessed_letters.append(letter)   # auto-reveal the letter
            return letter
        return None

    # ── Display helpers ───────────────────────────────────────────────────────
    def get_display_word(self) -> str:
        return " ".join(
            letter if letter in self.guessed_letters else "_"
            for letter in self.word
        )

    def get_status(self) -> str:
        """Returns: 'win' | 'lose' | 'ongoing'"""
        if all(letter in self.guessed_letters for letter in self.word):
            return "win"
        elif self.remaining_attempts <= 0:
            return "lose"
        return "ongoing"

    def get_guessed_letters(self) -> str:
        return ", ".join(self.guessed_letters) if self.guessed_letters else "—"

    def get_score(self) -> int:
        """Simple score based on difficulty and remaining attempts."""
        multiplier = {"easy": 1, "medium": 2, "hard": 4}.get(self.difficulty, 1)
        return self.remaining_attempts * multiplier * 10