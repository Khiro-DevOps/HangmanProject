class HangmanGame:
    def __init__(self, word="PYTHON", max_attempts=6):
        self.word = word.upper()
        self.guessed_letters = []
        self.remaining_attempts = max_attempts

    def guess(self, letter: str):
        letter = letter.upper()

        if letter in self.guessed_letters:
            return "already"

        self.guessed_letters.append(letter)

        if letter not in self.word:
            self.remaining_attempts -= 1
            return "wrong"

        return "correct"

    def get_display_word(self):
        return " ".join(
            letter if letter in self.guessed_letters else "_"
            for letter in self.word
        )

    def get_status(self):
        if all(letter in self.guessed_letters for letter in self.word):
            return "win"
        elif self.remaining_attempts <= 0:
            return "lose"
        return "ongoing"

    def get_guessed_letters(self):
        return ", ".join(self.guessed_letters)