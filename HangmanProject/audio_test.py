import time
import os
try:
    import pygame
except Exception as e:
    print('pygame import error:', e)
    raise

print('pygame:', pygame)
print('mixer init before init():', pygame.mixer.get_init())
try:
    pygame.mixer.init()
    print('mixer init after init():', pygame.mixer.get_init())
except Exception as e:
    print('mixer.init() failed:', e)

base = os.path.join(os.path.dirname(__file__), 'assets', 'audio')
menu = os.path.join(base, 'menu.mp3')
game = os.path.join(base, 'game.mp3')
print('menu exists:', os.path.exists(menu), menu)
print('game exists:', os.path.exists(game), game)

if os.path.exists(menu):
    try:
        print('Loading menu...')
        pygame.mixer.music.load(menu)
        print('Playing menu for 3s...')
        pygame.mixer.music.play(loops=-1)
        time.sleep(3)
        print('Stopping music')
        pygame.mixer.music.stop()
    except Exception as e:
        print('Error playing menu:', e)

print('Done')
