import pygame, os
pygame.init()
cwd = os.path.dirname(__file__)
path = os.path.join(cwd, '..', 'old assets', 'Regular_Game.png')
path = os.path.normpath(path)
print('Inspecting:', path)
try:
    img = pygame.image.load(path)
    print('size=', img.get_size(), 'bitsize=', img.get_bitsize(), 'has_alpha=', img.get_alpha(), 'flags=', img.get_flags())
    w,h = img.get_size()
    coords = [(0,0),(10,0),(0,10),(10,10),(50,50),(w-1,h-1)]
    samples = []
    trans_found = False
    for x,y in coords:
        if 0 <= x < w and 0 <= y < h:
            c = img.get_at((x,y))
            samples.append((x,y,tuple(c)))
            if len(c) >= 4 and c[3] == 0:
                trans_found = True
    print('transparent_sample_found=', trans_found)
    print('sample_pixels=', samples)
except Exception as e:
    print('error loading:', e)
pygame.quit()
