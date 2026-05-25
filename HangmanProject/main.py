import pygame
from gui import HangmanApp


def main():
    pygame.init()
    app = HangmanApp()
    app.run()


if __name__ == "__main__":
    main()