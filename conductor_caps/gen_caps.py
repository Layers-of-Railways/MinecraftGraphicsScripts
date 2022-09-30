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
    "brown": "max($/2 + 0.2, 0.35)"
}


def rgb(i):
    r = (i >> 16) & 255
    g = (i >> 8) & 255
    b = (i >> 0) & 255
    return r, g, b


def to_255(tup: typing.Iterable) -> list:
    return [min(255, max(round(v * 255), 0)) for v in tup]


def div(tup: tuple) -> tuple:
    return tuple([v / 255 for v in tup])[:3]


def hue(rgb_col: tuple) -> float:
    return colorsys.rgb_to_hls(*div(rgb_col))[0]


def luminance(rgb_col: tuple) -> float:
    return colorsys.rgb_to_hls(*div(rgb_col))[1]


def saturation(rgb_col: tuple) -> float:
    return colorsys.rgb_to_hls(*div(rgb_col))[2]


mask = pygame.image.load("mask_conductor_cap.png")
blue_cap = pygame.image.load("blue_conductor_cap.png")
blue_col = rgb(colors["blue"])

for name, int_color in colors.items():
    if name == "blue" and False:
        continue

    cap = pygame.Surface((64, 64), pygame.SRCALPHA)
    cap_col = rgb(int_color)

    print(name, saturation(cap_col))

    for x in range(64):
        for y in range(64):
            old_col = blue_cap.get_at((x, y))

            hue_diff = hue(old_col) - hue(blue_col)
            luminance_diff = luminance(old_col) / luminance(blue_col)
            saturation_diff = saturation(old_col) / saturation(blue_col)

            old_hls = list(colorsys.rgb_to_hls(*div(old_col)))

            old_hls[0] = hue_diff + hue(cap_col)
            old_hls[1] = luminance_diff * luminance(cap_col)
            old_hls[2] = saturation_diff * min(eval(forced_saturation.get(name, "$").replace("$", str(saturation(cap_col)))), saturation(blue_col)+0.1)

            new_col = list(to_255(colorsys.hls_to_rgb(*old_hls))) + [old_col[3]]

            if mask.get_at((x, y)) != (255, 255, 255, 255):
                new_col = old_col

            if 30 < y < 40:
                new_col = cap_col[:3]

            cap.set_at((x, y), new_col)
    pygame.image.save(cap, f"out_pictures/{name}_conductor_cap.png")
