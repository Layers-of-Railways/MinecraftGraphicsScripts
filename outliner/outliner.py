import pygame
import os

COLOR = (25, 32, 34, 255)
COLOR = (255, 0, 0, 255)

pygame.init()

for name in os.listdir("input"):
    src = pygame.image.load(os.path.join("input", name))
    dst = pygame.Surface((src.get_width(), src.get_height()), pygame.SRCALPHA)

    dst.fill((0, 0, 0, 0))

    for x in range(src.get_width()):
        for y in range(src.get_height()):
            print(src.get_at((x, y)))
            if src.get_at((x, y))[3] > 50:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue

                        new_x = x + dx
                        new_y = y + dy
                        if new_x < 0 or new_y < 0 or new_x >= src.get_width() or new_y >= src.get_height() or src.get_at((new_x, new_y))[3] < 50:
                            dst.set_at((x, y), COLOR)
                            break

    pygame.image.save(dst, os.path.join("output", name))