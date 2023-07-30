import pygame
import os
import colorsys

COLOR = (25, 32, 34, 255)
COLOR = (255, 0, 0, 255)

pygame.init()

def avg_color(surf: pygame.Surface) -> tuple[float, float, float]:
    r, g, b = 0, 0, 0
    count = 0

    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            col = surf.get_at((x, y))
            if col[3] > 10:
                cr, cg, cb, _ = col
                r += cr
                g += cg
                b += cb
                count += 1

    return r/count, g/count, b/count

for name in os.listdir("input"):
    src = pygame.image.load(os.path.join("input", name))
    dst = pygame.Surface((src.get_width(), src.get_height()), pygame.SRCALPHA)

    dst.fill((0, 0, 0, 0))

    avg_value = colorsys.rgb_to_hsv(*avg_color(src))[2]
    print(avg_value)

    for x in range(src.get_width()):
        for y in range(src.get_height()):
            """if src.get_at((x, y))[3] > 50:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue

                        new_x = x + dx
                        new_y = y + dy
                        if new_x < 0 or new_y < 0 or new_x >= src.get_width() or new_y >= src.get_height() or src.get_at((new_x, new_y))[3] < 50:
                            dst.set_at((x, y), COLOR)
                            break"""
            col = src.get_at((x, y))
#            dst.set_at((x, y), [int(v) for v in avg_color(src)])
            if col[3] > 50 and colorsys.rgb_to_hsv(*col[:3])[2] < avg_value * 0.95:
                dst.set_at((x, y), COLOR)

    pygame.image.save(dst, os.path.join("output", name))