import typing

import pygame
import colorsys

pygame.init()

colors = {
    "white": 16777215,
    "orange": 14188339,
    "magenta": 11685080,
    "light_blue": 6724056,
    "yellow": 15066419,
    "lime": 8375321,
    "pink": 15892389,
    "gray": 5000268,
    "light_gray": 10066329,
    "cyan": 5013401,
    "purple": 8339378,
    "blue": 3361970,
    "brown": 6704179,
    "green": 6717235,
    "red": 10040115,
    "black": 1644825
}

forced_saturation = {
    # "brown": "max($/2 + 0.2, 0.35)"
}


def rgb_to_hex(rgb):
    return '%02x%02x%02x' % (rgb[:3])


def rgb(i):
    r = (i >> 16) & 255
    g = (i >> 8) & 255
    b = (i >> 0) & 255
    return r, g, b


def div_mul(col: tuple, base: tuple, target: tuple) -> tuple:
    out = []
    for i in range(3):
        out.append((col[i]/base[i])*target[i])
    return tuple(to_255(out, 1))


def to_255(tup: typing.Iterable, mul=255) -> list:
    return [min(255, max(round(v * mul), 0)) for v in tup]


def div(tup: tuple) -> tuple:
    return tuple([v / 255 for v in tup])[:3]


def hue(rgb_col: tuple) -> float:
    return colorsys.rgb_to_hsv(*div(rgb_col))[0]


def luminance(rgb_col: tuple) -> float:
    return colorsys.rgb_to_hsv(*div(rgb_col))[2]


def saturation(rgb_col: tuple) -> float:
    return colorsys.rgb_to_hsv(*div(rgb_col))[1]


mask = pygame.image.load("mask_conductor_cap.png")
blue_cap = pygame.image.load("blue_conductor_cap.png")
blue_col = tuple(pygame.transform.average_color(pygame.image.load("wool/blue_wool.png")))
# blue_col = rgb(colors["blue"])

for name, int_color in colors.items():
    if name == "blue" and False:
        continue

    wool = pygame.image.load(f"wool/{name}_wool.png")

    cap = pygame.Surface((64, 64), pygame.SRCALPHA)
    cap_col = tuple(pygame.transform.average_color(wool))#rgb(int_color)

    print(name, rgb_to_hex(cap_col))

    for x in range(64):
        for y in range(64):
            old_col = blue_cap.get_at((x, y))

            hue_diff = hue(old_col) - hue(blue_col)
            luminance_diff = luminance(old_col) / luminance(blue_col)
            saturation_diff = saturation(old_col) / saturation(blue_col) * 0.9

            old_hls = list(colorsys.rgb_to_hsv(*div(old_col)))

            old_hls[0] = hue_diff + hue(cap_col)
            old_hls[2] = luminance_diff * luminance(cap_col) # hsv better
            old_hls[1] = saturation_diff * min(
                eval(forced_saturation.get(name, "$").replace("$", str(saturation(cap_col)))),
                saturation(blue_col) + 0.1)

            new_col = list(to_255(colorsys.hsv_to_rgb(*old_hls))) + [old_col[3]]

            if mask.get_at((x, y)) != (255, 255, 255, 255):
                new_col = old_col

            if 30 < y < 40:
                new_col = cap_col[:3]
            elif 40 < y < 50:
                new_col = list(pygame.transform.average_color(wool))
                new_col[3] = 255

            cap.set_at((x, y), new_col)
    pygame.image.save(cap, f"out_pictures/{name}_conductor_cap.png")
