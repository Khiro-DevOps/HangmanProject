import random

# ─── Difficulty Settings ───────────────────────────────────────────────────────
DIFFICULTY_CONFIG = {
    "easy": {
        "attempts": 8,
        "hint_available": True,
        "timer_seconds": None,       # no timer
        "show_category": True,       # category is revealed upfront
        "description": "8 attempts · Category shown · Hint allowed",
    },
    "medium": {
        "attempts": 6,
        "hint_available": True,
        "timer_seconds": None,
        "show_category": False,      # category hidden
        "description": "6 attempts · No category · 1 hint allowed",
    },
    "hard": {
        "attempts": 4,
        "hint_available": False,
        "timer_seconds": 30,         # 30-second countdown per guess
        "show_category": False,
        "description": "4 attempts · No hints · 30-sec timer per guess",
    },
}

# ─── Word Bank ─────────────────────────────────────────────────────────────────
WORD_BANK = {
    "easy": {
        "Animals":    ["CAT", "DOG", "BIRD", "FISH", "BEAR", "FROG", "LION", "WOLF", "DUCK", "DEER"],
        "Fruits":     ["APPLE", "MANGO", "GRAPE", "LEMON", "PEACH", "MELON", "PLUM", "GUAVA", "LIME", "PEAR"],
        "Colors":     ["RED", "BLUE", "GREEN", "PINK", "GOLD", "GREY", "CYAN", "TEAL", "ROSE", "AMBER"],
        "Body Parts": ["ARM", "LEG", "EYE", "EAR", "NOSE", "HAND", "FOOT", "KNEE", "BACK", "NECK"],
    },
    "medium": {
        "Animals":     ["ELEPHANT", "GIRAFFE", "PENGUIN", "DOLPHIN", "CHEETAH", "GORILLA", "PANTHER", "LEOPARD"],
        "Countries":   ["BRAZIL", "CANADA", "GERMANY", "THAILAND", "NIGERIA", "ICELAND", "UKRAINE", "VIETNAM"],
        "Sports":      ["BADMINTON", "SWIMMING", "ARCHERY", "GYMNASTICS", "FOOTBALL", "BASEBALL", "WRESTLING"],
        "Programming": ["PYTHON", "VARIABLE", "FUNCTION", "DEBUGGING", "ITERATOR", "TERMINAL", "COMPILER"],
    },
    "hard": {
        "Science":     ["PHOTOSYNTHESIS", "MITOCHONDRIA", "CHROMOSOME", "HYPOTHESIS",
                        "EVAPORATION", "OXIDIZATION", "EQUILIBRIUM", "PRECIPITATION"],
        "Geography":   ["MOZAMBIQUE", "AZERBAIJAN", "KYRGYZSTAN", "LIECHTENSTEIN",
                        "MADAGASCAR", "LUXEMBOURG", "MAURITANIA", "PHILIPPINES"],
        "Programming": ["POLYMORPHISM", "ENCAPSULATION", "ASYNCHRONOUS", "ABSTRACTION",
                        "INHERITANCE", "CONCURRENCY", "REFACTORING", "RECURSION"],
        "Vocabulary":  ["SERENDIPITY", "EPHEMERAL", "MELANCHOLY", "PERSPICACIOUS",
                        "SURREPTITIOUS", "IDIOSYNCRATIC", "MAGNANIMOUS", "UBIQUITOUS"],
    },
}


def get_random_word(difficulty: str = "medium"):
    """Return (word, category) for the given difficulty."""
    difficulty = difficulty.lower()
    if difficulty not in WORD_BANK:
        difficulty = "medium"
    pool = WORD_BANK[difficulty]
    category = random.choice(list(pool.keys()))
    word = random.choice(pool[category])
    return word, category


def get_hint(word: str, guessed_letters: list):
    """Reveal one random un-guessed letter as a hint. Returns the letter or None."""
    hidden = [ch for ch in word if ch not in guessed_letters]
    if hidden:
        return random.choice(hidden)
    return None


def get_difficulties():
    return list(DIFFICULTY_CONFIG.keys())


def get_config(difficulty: str):
    return DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["medium"])   