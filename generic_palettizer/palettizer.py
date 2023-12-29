import shutil
import typing
import tempfile

import ct_gen.ct_gen as ct_gen

import pygame
import os

pygame.init()

def expand_diagonals(surf: pygame.Surface) -> pygame.Surface:
    out = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            out.set_at((x, y), surf.get_at((x, y)))

            if surf.get_at((x, y))[3] == 0:
                adj = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                adj_colors = []
                for xoff, yoff in adj:
                    try:
                        c = surf.get_at((x + xoff, y + yoff))
                    except IndexError:
                        continue
                    if c[3] > 0:
                        adj_colors.append(c)
                if len(adj_colors) >= 2:
                    r, g, b = [v[0] for v in adj_colors], [v[1] for v in adj_colors], [v[2] for v in adj_colors]
                    avg_col = (round(sum(r)/len(r)), round(sum(g)/len(g)), round(sum(b)/len(b)))
                    out.set_at((x, y), avg_col)
    return out


def vertical_strip_to_horizontal_kryppers(surf: pygame.Surface) -> pygame.Surface:
    out = pygame.Surface((32, 32))
    out.blit(surf.subsurface(0, 0, 16, 16), (16, 16))
    out.blit(surf.subsurface(0, 32, 16, 16), (0, 16))
    out.blit(surf.subsurface(0, 16, 16, 16), (16, 0))
    out.blit(surf.subsurface(0, 0, 16, 8), (0, 0))
    out.blit(surf.subsurface(0, 40, 16, 8), (0, 8))
    return out

def vertical_strip_to_horizontal_kryppers_single(surf: pygame.Surface) -> pygame.Surface:
    out = pygame.Surface((16, 16))
    out.blit(surf.subsurface(0, 0, 16, 8), (0, 0))
    out.blit(surf.subsurface(0, 40, 16, 8), (0, 8))
    return out

def dup_range(rng: range) -> range:
    return range(rng.start, rng.stop, rng.step)

def shift_horiz(y_range: range, x_amt: int):
    def f(surf: pygame.Surface) -> pygame.Surface:
        new_surf = surf.copy()
        for y in y_range:
            for x in range(new_surf.get_width()):
                old_x = x - x_amt
                if old_x < 0 or old_x >= surf.get_width():
                    new_surf.set_at((x, y), (0, 0, 0, 0))
                else:
                    new_surf.set_at((x, y), surf.get_at((old_x, y)))
        return new_surf
    return f

def half_scale(surf: pygame.Surface) -> pygame.Surface:
    return pygame.transform.scale(surf, (surf.get_width() / 2, surf.get_height() / 2))

def split_vertically_auto(surf: pygame.Surface, divider_height: int = 2) -> list[pygame.Surface]:
    ranges: list[range] = [] # [start, end)
    start: int | None = None

    for y in range(surf.get_height()):
        is_empty_row = True
        is_bottom_empty_row = True
        for x in range(surf.get_width()):
            if surf.get_at((x, y))[3] > 10:
                is_empty_row = False
                break
            elif y + 1 < surf.get_height() and surf.get_at((x, y+1))[3] > 10:
                is_empty_row = False
                is_bottom_empty_row = False
                break

        if is_empty_row:
            if start is not None:
                ranges.append(range(start, y))
                start = None
            else:
                continue
        elif start is None and is_bottom_empty_row:
            start = y

    if start is not None:
        ranges.append(range(start, y+1))

    return [surf.subsurface((0, r.start, surf.get_width(), r.stop - r.start)) for r in ranges]

def split_horizontally_auto(surf: pygame.Surface, divider_width: int = 2) -> list[pygame.Surface]:
    ranges: list[range] = [] # [start, end)
    start: int | None = None

    for x in range(surf.get_width()):
        is_empty_col = True
        is_right_empty_col = True
        for y in range(surf.get_height()):
            if surf.get_at((x, y))[3] > 10:
                is_empty_col = False
                break
            elif x + 1 < surf.get_width() and surf.get_at((x+1, y))[3] > 10:
                is_empty_col = False
                is_right_empty_col = False
                break

        if is_empty_col:
            if start is not None:
                ranges.append(range(start, x))
                start = None
            else:
                continue
        elif start is None and is_right_empty_col:
            start = x

    if start is not None:
        ranges.append(range(start, x+1))

    return [surf.subsurface((r.start, 0, r.stop - r.start, surf.get_height())) for r in ranges]

def build_sheet_splitter(sheet_tex: str, steps: list[typing.Callable[[pygame.Surface], list[pygame.Surface]]]) -> typing.Callable[["PaletteConf"], dict[str, pygame.Surface]]:
    def f(conf: PaletteConf) -> dict[str, pygame.Surface]:
        images = [conf.ld(sheet_tex)]

        for i, step in enumerate(steps):
            new_images = []
            for image in images:
                new_images += step(image)
            images = new_images

            for j, image in enumerate(images):
                conf.sv(image, "palettized_steps", f"step_{i + 1}_{j + 1}.png")

        assert len(images) == len(conf.color_names), f"Color names ({len(conf.color_names)}) & split images ({len(images)}) have differing counts"
        return dict(zip(conf.color_names, images))
    return f

# Palette should have sets of colors with a column of whitespace in btw (one row)
class PaletteConf:
    def __init__(self, name: str, base_tex: str, palette_tex: str, color_names: list[str], base_color_name: str,
                 palette_processors: list[typing.Callable[[pygame.Surface], pygame.Surface]] = None,
                 sectors: dict[str, tuple[int, int, int, int, bool]] | None = None,
                 palettized_src: typing.Callable[["PaletteConf"], dict[str, pygame.Surface]] | None = None):
        self.name = name
        self.base_tex = base_tex
        self.palette_tex = palette_tex
        self.color_names = color_names
        self.base_color_name = base_color_name
        self.palette_processors = palette_processors or []
        self.palettized_src = palettized_src
        assert base_color_name in color_names

        self.sectors: dict[str, tuple[int, int, int, int, bool]] | None = sectors

        self._palette_surf: pygame.Surface | None = None
        self.mkdirs()

    def _mkpath(self, *parts: str) -> str:
        return os.path.join("sets", self.name, *parts)

    def ld(self, *path: str) -> pygame.Surface:
        return pygame.image.load(self._mkpath(*path))

    def sv(self, surf: pygame.Surface, *path: str):
        pygame.image.save(surf, self._mkpath(*path))

    def mkdirs(self):
        for ext in ["palette_process_steps", "preview_rps"] + [os.path.join("output", c) for c in self.color_names] + ([] if self.palettized_src is None else ["palettized_steps"]):
            os.makedirs(self._mkpath(ext), exist_ok=True)

    def get_base_surf(self) -> pygame.Surface:
        return self.ld(self.base_tex)

    def get_palette_surf(self) -> pygame.Surface:
        if self._palette_surf is not None:
            return self._palette_surf
        surf = pygame.image.load(os.path.join("sets", self.name, self.palette_tex))
        for i, processor in enumerate(self.palette_processors):
            surf = processor(surf)
            self.sv(surf, "palette_process_steps", f"step_{i + 1}.png")
        self._palette_surf = surf
        return surf

    def _split_palette(self) -> dict[str, list[tuple[int, int, int]]]:
        pal = self.get_palette_surf()

        ranges: list[range] = [] # [start, end)
        start: int | None = None

        for x in range(pal.get_width()):
            is_empty_column = True
            for y in range(pal.get_height()):
                if pal.get_at((x, y))[3] > 10:
                    is_empty_column = False
                    break

            if is_empty_column:
                if start is not None:
                    ranges.append(range(start, x))
                    start = None
                else:
                    continue
            elif start is None:
                start = x

        if start is not None:
            ranges.append(range(start, x+1))

        #print("Ranges:")
        #for r in ranges:
        #    print(f"\t{r}")
        assert len(ranges) == len(self.color_names), f"Color names ({len(self.color_names)}) & detected colors ({len(ranges)}) have differing counts\n" + "\n".join(str(v) for v in ranges)

        # step 1 - build color lists for palettes
        palettes = {}

        for i, rng in enumerate(ranges):
            col = self.color_names[i]
            palettes[col] = []

            for x in dup_range(rng):
                for y in range(pal.get_height()):
                    c = pal.get_at((x, y))
                    if c[3] > 10:
                        palettes[col].append(c[:3])
        palette_length = None
        for color_name, palette in palettes.items():
            if palette_length is None:
                palette_length = len(palette)
            else:
                assert len(palette) == palette_length, f"Mismatched palette size for color {color_name}"
        print(f"Palette size: {palette_length}")
        return palettes

    def palettize(self):
        if self.palettized_src is not None:
            palette_surfs = self.palettized_src(self)
            for color_name in self.color_names:
                self.sv(palette_surfs[color_name], "output", color_name, "0_full_base.png")
            return
        palettes = self._split_palette()
        base_img = self.get_base_surf()

        w, h = base_img.get_width(), base_img.get_height()

        # step 1: Show overlay
        used_indexes = set()
        overlay_img = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(w):
            for y in range(h):
                c = base_img.get_at((x, y))
                if c[3] <= 10: continue
                if c[:3] not in palettes[self.base_color_name]:
                    overlay_img.set_at((x, y), c[:3])
                else:
                    used_indexes.add(palettes[self.base_color_name].index(c[:3]))
        print(f"Used index count: {len(used_indexes)}")
        print("Colors in base palette")
        for c in palettes[self.base_color_name]:
            r, g, b = c
            print(f"\t{r:02x}{g:02x}{b:02x}")
        self.sv(overlay_img, "overlay.png")

        for color_name in self.color_names:
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            for x in range(w):
                for y in range(h):
                    c = base_img.get_at((x, y))
                    if c[3] <= 10: continue
                    c = c[:3]
                    if c not in palettes[self.base_color_name]:
                        img.set_at((x, y), c)
                    else:
                        idx = palettes[self.base_color_name].index(c)
                        img.set_at((x, y), palettes[color_name][idx])
            self.sv(img, "output", color_name, "0_full_base.png")

    def sectorize(self):
        if self.sectors is None: return
        # sector fmt:   x,  y,  w,  h, make power of 2

        for color_name in self.color_names:
            out = self.ld("output", color_name, "0_full_base.png")

            for sector_name, params in self.sectors.items():
                x_0, y_0, w, h, make_power_of_2 = params[:5]
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

                if len(params) == 6: # 6th element is a list of postprocessor functions
                    processors: list[typing.Callable[[pygame.Surface], pygame.Surface]] = params[5]
                    for processor in processors:
                        sector: pygame.Surface = processor(sector)

                self.sv(sector, "output", color_name, f"{sector_name}.png")

                if "template" in sector_name:
                    self.sv(ct_gen.generate_ct(sector), "output", color_name, f"{sector_name.replace('template', 'full')}.png")

    def gen_preview_rp(self):
        if self.name != "boiler": return
        if self.sectors is None: return
        textures = [v.replace("template", "full") for v in self.sectors.keys() if "template" in v]
        if len(textures) is None: return

        casings = ["andesite", "brass", "copper", "railway", "refined_radiance", "shadow_steel"]

        for color in self.color_names:
            tmp_dir = tempfile.mkdtemp()

            cmd = f"cp -r \"rp_base\" \"{tmp_dir}\""
            os.system(cmd)

            dst = os.path.join(tmp_dir, "rp_base", "assets", "create", "textures", "block")
            print(dst)

            copies = {
                "smokebox_door.png": "../../../../pack.png"
            }

            for i, con_tex in enumerate(textures):
                norm_tex = con_tex.replace("_ct_full", "")

                casing = casings[i]

                copies[norm_tex + ".png"] = f"{casing}_casing.png"
                copies[con_tex + ".png"] = f"{casing}_casing_connected.png"

            for frm, to in copies.items():
                frm_path = os.path.abspath(self._mkpath("output", color, frm.replace("$", color)))
                to_path = os.path.join(dst, to)
                cmd = f"cp \"{frm_path}\" \"{to_path}\""
                os.system(cmd)

            with open(os.path.join(tmp_dir, "rp_base", "pack.mcmeta"), "r") as f:
                contents = f.read()
            with open(os.path.join(tmp_dir, "rp_base", "pack.mcmeta"), "w") as f:
                f.write(contents.replace("<NAME>", self.name).replace("<COLOR>", color))

            os.system(f"cd \"{os.path.join(tmp_dir, 'rp_base')}\"; zip -r ../preview_rp.zip .")

            preview_rp_path = self._mkpath("preview_rps", f"locometal_preview_{color}.zip")
            os.system(f"cp \"{os.path.join(tmp_dir, 'preview_rp.zip')}\" \"{preview_rp_path}\"")
            shutil.rmtree(tmp_dir, ignore_errors=True)


# TODO: Palette is not complete, there is a color (#352b2b) not in the palette... GAHAHHAHAHAHAAARRRR
def _16(x: int, y: int) -> tuple[int, int, int, int, bool]:
    return x, y, 16, 16, True
def _ct(x: int, y: int) -> tuple[int, int, int, int, bool]:
    return x, y, 64, 32, True

class ImageBundle:
    def __init__(self, name: str, inputs: list[str], output: str):
        self.name = name
        self.inputs = inputs
        self.output = output
        self._sectors: dict[str, tuple[int, int, int, int, bool]] | None = None

    def _mkpath(self, *parts: str) -> str:
        return os.path.join("sets", self.name, *parts)

    def ld(self, *path: str) -> pygame.Surface:
        return pygame.image.load(self._mkpath(*path))

    def sv(self, surf: pygame.Surface, *path: str):
        pygame.image.save(surf, self._mkpath(*path))

    def sectors(self) -> dict[str, tuple[int, int, int, int, bool]]:
        if self._sectors is not None:
            return self._sectors
        self._sectors = {}
        images = [(inp, self.ld(inp)) for inp in self.inputs]
        width = sum(img.get_width() for _, img in images)
        height = max(img.get_height() for _, img in images)
        out = pygame.Surface((width, height), pygame.SRCALPHA)
        x = 0
        for name, img in images:
            out.blit(img, (x, 0))
            self._sectors[name.removesuffix(".png")] = (x, 0, img.get_width(), img.get_height(), False)
            x += img.get_width()
        self.sv(out, self.output)
        return self._sectors


smoke_bundle = ImageBundle("smoke",["chimneypush_medium_dyeable.png",
                                    "chimneypush_small_dyeable.png",
                                    "mediumpuff_dyeable.png",
                                    "smallpuff_dyeable.png"], "smoke_sheet.png")

palette_sets = [
    PaletteConf("boiler", "boiler_v2.png", "palette_new.png",
                ['brown', 'red', 'orange', 'yellow', 'lime', 'green', 'cyan', 'light_blue', 'blue', 'purple',
                'magenta', 'pink', 'white', 'light_gray', 'gray', 'black', 'netherite'],
                "netherite",
                palette_processors=[shift_horiz(range(2), -1), half_scale],
                sectors={
                    "slashed":              _16(0,  0),
                    "riveted":              _16(16, 0),
                    "riveted_pillar_top":   _16(32, 0),
                    "smokebox_tank_top":    _16(48, 0),
                    "sheeting":             _16(64, 0),
                    "annexed_slashed":      _16(0,  16),
                    "annexed_riveted":      _16(16, 16),
                    "riveted_pillar_side":  _16(32, 16),
                    "tank_side":            _16(48, 16),

                    "boiler_gullet": (0,  33, 30, 30, True, [expand_diagonals]),
                    "smokebox_door": (34, 33, 30, 30, True, [expand_diagonals]),

                    "boiler_side":                   (65, 24, 16, 48, True, [vertical_strip_to_horizontal_kryppers_single]),
                    "boiler_side_connected":         (65, 24, 16, 48, True, [vertical_strip_to_horizontal_kryppers]),
                    "wrapped_boiler_side":           (65, 81, 16, 48, True, [vertical_strip_to_horizontal_kryppers_single]),
                    "wrapped_boiler_side_connected": (65, 81, 16, 48, True, [vertical_strip_to_horizontal_kryppers]),

                    "wrapped_slashed": _16(64, 138),

                    "slashed_ct_template":          _ct(0, 64),
                    "riveted_ct_template":          _ct(0, 97),
                    "wrapped_slashed_ct_template":  _ct(0, 130)
                },
                palettized_src=build_sheet_splitter("boilers.png", [
                    split_vertically_auto,
                    split_horizontally_auto
                ])
                ),
    PaletteConf("smoke", "smoke_sheet.png", "steam_palette.png",
                ['brown', 'red', 'orange', 'yellow', 'lime', 'green', 'cyan', 'light_blue', 'blue', 'purple',
                    'magenta', 'pink', 'white', 'light_gray', 'gray', 'black'],
                'white',
                sectors=smoke_bundle.sectors()),
]

for palette_set in palette_sets:
    palette_set.palettize()
    palette_set.sectorize()
    palette_set.gen_preview_rp()


"""
exit()

base_names = [
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

second_row = False

palette_idx = 0

extension_names = []

for k, v in extensions.items():
    extension_names += v[1]


all_names = [] + base_names + extension_names

palettes = {k: [0, pygame.Surface((20, 1), pygame.SRCALPHA), []] for k in all_names}

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

        palette_surf = palettes[base_names[palette_idx]][1]
        palette_surf.set_at((palettes[base_names[palette_idx]][0], 0), color)
        palettes[base_names[palette_idx]][0] += 1
        palettes[base_names[palette_idx]][2].append(color)

for extension_name, dat in extensions.items():
    count, color_list = dat
    extension_img = pygame.image.load(f"input/extra_palettes/{extension_name}.png")
    sub_idx = 0
    for y in range(extension_img.get_height()):
        sub_idx = 0
        for x in range(extension_img.get_width()):
            if full_palette.get_at((x, 4)) == (0, 0, 0, 255): # added black dots as markers
                sub_idx += 1
                sub_idx %= count

            color = extension_img.get_at((x, y))
            if color[3] == 0: # skip transparent
                continue

            palette_surf = palettes[color_list[sub_idx]][1]
            palette_surf.set_at((palettes[color_list[sub_idx]][0], 0), color)
            palettes[color_list[sub_idx]][0] += 1
            palettes[color_list[sub_idx]][2].append(color)

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
"""
