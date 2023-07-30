import sys
import ct_gen.ct_gen as ct_gen

import pygame
import os

pygame.init()

names = [
    "brown",
    "red",
    "orange",
    "tan",
    "grass_green",
    "deep_green",
    "sea_green",
    "light_blue",
    "blue",
    "purple",
    "magenta",
    "burnt_orange",
    "white",
    "light_gray",
    "gray",
    "black"
]

base_palette_name = "red"

# start by splitting palette

full_palette = pygame.image.load("input/colorpallets.png")

start_x = 0
second_row = False

palette_idx = 0
palettes = {k: [0, pygame.Surface((20, 1), pygame.SRCALPHA), []] for k in names}

for y in range(full_palette.get_height()):
    if second_row:
        palette_idx = 8
    else:
        palette_idx = 0
    for x in range(full_palette.get_width()):
        if 4 <= y <= 6:
            palette_idx = 8
            second_row = True
            continue
        if full_palette.get_at((x, 4)) == (0, 0, 0, 255): # added black dots as markers
            # print("advancing palette index")
            palette_idx += 1
            if not second_row:
                palette_idx %= 8
            else:
                palette_idx = 8 + ((palette_idx - 8) % 8)

        color = full_palette.get_at((x, y))
        if color[3] == 0: # skip transparent
            continue

        # print(color, names[palette_idx], palettes[names[palette_idx]][0])

        palette_surf = palettes[names[palette_idx]][1]
        palette_surf.set_at((palettes[names[palette_idx]][0], 0), color)
        palettes[names[palette_idx]][0] += 1
        palettes[names[palette_idx]][2].append(color)

for k, v in palettes.items():
    pygame.image.save(v[1], f"output/palettes/{k}.png")


# make colorized texture for each palette
reference_palette = palettes[base_palette_name][2]

base_img = pygame.image.load("input/trainthings.png")

sectors = { #              x,  y,  w,  h, make power of 2
    "connected_template": (0, 18, 64, 32, False),
    "connected_template_white": (92, 18, 64, 32, False),
    "single_outline": (52, 0, 16, 16, False),
    "single_outline_white": (88, 0, 16, 16, False),
    "single": (52, 52, 16, 16, False),
    "single_white": (89, 52, 16, 16, False),
    "boiler_front": (66, 22, 24, 24, True)
}

for name, data in palettes.items():
    _, _, colors = data
    out = pygame.Surface((base_img.get_width(), base_img.get_height()), pygame.SRCALPHA)
    for y in range(base_img.get_height()):
        for x in range(base_img.get_width()):
            color = base_img.get_at((x, y))
            if color[3] == 0:
                continue
            if color in reference_palette:
                idx = reference_palette.index(color)
                color = colors[idx]
            else:
                print("color not found in reference palette", color, file=sys.stderr)
            out.set_at((x, y), color)

    os.makedirs(f"output/colorized/{name}", exist_ok=True)
    pygame.image.save(out, f"output/colorized/{name}/full.png")

    # split into sectors

    for sector_name, params in sectors.items():
        x_0, y_0, w, h, make_power_of_2 = params
        sector = out.subsurface((x_0, y_0, w, h))

        if make_power_of_2:
            lowest_pow_2_width = 1
            while lowest_pow_2_width < sector.get_width():
                lowest_pow_2_width *= 2
            lowest_pow_2_height = 1
            while lowest_pow_2_height < sector.get_height():
                lowest_pow_2_height *= 2

            new_sector = pygame.Surface((lowest_pow_2_width, lowest_pow_2_height), pygame.SRCALPHA)
            new_sector.blit(sector, (0, 0))
            sector = new_sector

        pygame.image.save(sector, f"output/colorized/{name}/{sector_name}.png")

        if "template" in sector_name:
            pygame.image.save(ct_gen.generate_ct(sector), f"output/colorized/{name}/{sector_name.replace('template', 'full')}.png")

os.system(f"cd output/colorized; zip -r ../colorized.zip .")