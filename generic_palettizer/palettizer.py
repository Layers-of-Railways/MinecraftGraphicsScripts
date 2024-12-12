import os
import shutil
import sys
import tempfile
import typing

import pygame

import ct_gen.ct_gen as ct_gen

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

def shift_horiz(y_range: range | None, x_amt: int):
    def f(surf: pygame.Surface) -> pygame.Surface:
        new_surf = surf.copy()
        for y in (y_range or range(surf.get_height())):
            for x in range(new_surf.get_width()):
                old_x = x - x_amt
                if old_x < 0 or old_x >= surf.get_width():
                    new_surf.set_at((x, y), (0, 0, 0, 0))
                else:
                    new_surf.set_at((x, y), surf.get_at((old_x, y)))
        return new_surf
    return f

def shift_vert(x_range: range | None, y_amt: int):
    def f(surf: pygame.Surface) -> pygame.Surface:
        new_surf = surf.copy()
        for x in (x_range or range(surf.get_width())):
            for y in range(new_surf.get_height()):
                old_y = y - y_amt
                if old_y < 0 or old_y >= surf.get_height():
                    new_surf.set_at((x, y), (0, 0, 0, 0))
                else:
                    new_surf.set_at((x, y), surf.get_at((x, old_y)))
        return new_surf
    return f

def half_scale(surf: pygame.Surface) -> pygame.Surface:
    return pygame.transform.scale(surf, (surf.get_width() / 2, surf.get_height() / 2))

def split_vertically_auto(surf: pygame.Surface) -> list[pygame.Surface]:
    ranges: list[range] = [] # [start, end)
    start: int | None = None

    y = 0
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

def split_horizontally_auto(surf: pygame.Surface) -> list[pygame.Surface]:
    ranges: list[range] = [] # [start, end)
    start: int | None = None

    x = 0
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

def split_palettes_lining_sheet(surf: pygame.Surface) -> list[pygame.Surface]:
    vertical_splits = split_vertically_auto(surf)
    wrapped_slashed = split_horizontally_auto(vertical_splits[0])[1:] + split_horizontally_auto(vertical_splits[1])
    wrapped_boilers = split_horizontally_auto(vertical_splits[2])[1:]

    assert len(wrapped_slashed) == len(wrapped_boilers), f"Wrapped slashed ({len(wrapped_slashed)}) & wrapped boilers ({len(wrapped_boilers)}) have differing counts"

    return [join_atlas_vert([wrapped_slashed[i], wrapped_boilers[i]]) for i in range(len(wrapped_slashed))]

def build_sheet_splitter(sheet_tex: str, steps: list[typing.Callable[[pygame.Surface], list[pygame.Surface]]], step_prefixes: list[str] | None = None) -> typing.Callable[["PaletteConf"], dict[str, pygame.Surface]]:
    def f(conf: PaletteConf) -> dict[str, pygame.Surface]:
        images = [conf.ld(sheet_tex)]

        for i, step in enumerate(steps):
            new_images = []
            for image in images:
                new_images += step(image)
            images = new_images

            for j, image in enumerate(images):
                if step_prefixes is None:
                    prefix = ""
                else:
                    prefix = "_" + ("_".join(step_prefixes))
                conf.sv(image, "palettized_steps", f"step{prefix}_{i + 1}_{j + 1}.png")

        assert len(images) == len(conf.color_names), f"Color names ({len(conf.color_names)}) & split images ({len(images)}) have differing counts"
        return dict(zip(conf.color_names, images))
    return f

def join_atlas(images: list[pygame.Surface]) -> pygame.Surface:
    w = sum(img.get_width() for img in images)
    h = max(img.get_height() for img in images)
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    x = 0
    for img in images:
        out.blit(img, (x, 0))
        x += img.get_width()
    return out

def join_atlas_vert(images: list[pygame.Surface]) -> pygame.Surface:
    w = max(img.get_width() for img in images)
    h = sum(img.get_height() for img in images)
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    y = 0
    for img in images:
        out.blit(img, (0, y))
        y += img.get_height()
    return out

def merge_sheet_splitters(splitters: list[typing.Callable[["PaletteConf"], dict[str, pygame.Surface]]]) -> typing.Callable[["PaletteConf"], dict[str, pygame.Surface]]:
    def f(conf: PaletteConf) -> dict[str, pygame.Surface]:
        out: dict[str, list[pygame.Surface]] = {color: [] for color in conf.color_names}
        for splitter in splitters:
            for color, img in splitter(conf).items():
                out[color].append(img)

        ret = {name: join_atlas(images) for name, images in out.items()}
        for i, color in enumerate(conf.color_names):
            conf.sv(ret[color], "palettized_steps", f"step_merged_{i + 1}.png")

        return ret
    return f
# Palette should have sets of colors with a column of whitespace in btw (one row)
class PaletteConf:
    def __init__(self, name: str, base_tex: str, palette_tex: str, color_names: list[str], base_color_name: str,
                 palette_processors: list[typing.Callable[[pygame.Surface], pygame.Surface]] = None,
                 sectors: dict[str, tuple[int, int, int, int, bool]] | None = None,
                 palettized_src: typing.Callable[["PaletteConf"], dict[str, pygame.Surface]] | None = None,
                 permitted_palette_empty_columns: int = 0):
        self.name = name
        self.base_tex = base_tex
        self.palette_tex = palette_tex
        self.color_names = color_names
        self.base_color_name = base_color_name
        self.palette_processors = palette_processors or []
        self.palettized_src = palettized_src
        self.permitted_palette_empty_columns = permitted_palette_empty_columns
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

        x = 0
        empty_columns = 0
        for x in range(pal.get_width()):
            is_empty_column = True
            for y in range(pal.get_height()):
                if pal.get_at((x, y))[3] > 10:
                    is_empty_column = False
                    break
            if is_empty_column:
                empty_columns += 1
            else:
                empty_columns = 0

            if empty_columns > self.permitted_palette_empty_columns:
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
                try:
                    sector = out.subsurface((x_0, y_0, w, h))
                except ValueError:
                    print(f"Failed to make subsurface {(x_0, y_0, w, h)}", file=sys.stderr)
                    raise

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
        if self.sectors is None: return
        generators = {
            "boiler": self._gen_preview_rp_boiler,
            "palettes_plus": self._gen_preview_rp_palettes_plus
        }
        if self.name not in generators: return
        generators[self.name]()

    def _gen_preview_rp_palettes_plus(self):
        tmp_dir = tempfile.mkdtemp()

        cmd = f"cp -r \"rp_base\" \"{tmp_dir}\""
        os.system(cmd)

        dst = os.path.join(tmp_dir, "rp_base", "assets", "railways", "textures", "block")
        print(dst)

        os.makedirs(dst)

        output_dir = os.path.abspath(self._mkpath("output"))
        real_dst = os.path.join(dst, "palettes")

        cmd = f"cp -r \"{output_dir}\" \"{real_dst}\""
        os.system(cmd)

        if True:
            frm_path = os.path.abspath(self._mkpath("output", "turquoise", "boiler_slashed.png"))
            to_path = os.path.join(dst, "../../../../pack.png")
            cmd = f"cp \"{frm_path}\" \"{to_path}\""
            os.system(cmd)

        with open(os.path.join(tmp_dir, "rp_base", "pack.mcmeta"), "r") as f:
            contents = f.read()
        with open(os.path.join(tmp_dir, "rp_base", "pack.mcmeta"), "w") as f:
            f.write(contents.replace("<NAME>", self.name).replace("<COLOR>", "full"))

        os.system(f"cd \"{os.path.join(tmp_dir, 'rp_base')}\"; zip -r ../preview_rp.zip .")

        preview_rp_path = self._mkpath("preview_rps", f"locometal_preview.zip")
        os.system(f"cp \"{os.path.join(tmp_dir, 'preview_rp.zip')}\" \"{preview_rp_path}\"")
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def _gen_preview_rp_boiler(self):
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
def _32(x: int, y: int) -> tuple[int, int, int, int, bool]:
    return x, y, 32, 32, True
def _ct(x: int, y: int) -> tuple[int, int, int, int, bool]:
    return x, y, 64, 32, True
def _ct_pre_exp(x: int, y: int) -> tuple[int, int, int, int, bool]:
    return x, y, 128, 128, True

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
                    "wrapped_slashed_ct_template":  _ct(0, 130),

                    "iron_wrapped_slashed": _16(81, 0),
                    "iron_wrapped_slashed_ct_template": _ct(81, 0),
                    "iron_wrapped_boiler_side": (81, 32, 16, 48, True, [vertical_strip_to_horizontal_kryppers_single]),
                    "iron_wrapped_boiler_side_connected": (81, 32, 16, 48, True, [vertical_strip_to_horizontal_kryppers]),

                    "copper_wrapped_slashed": _16(161, 0),
                    "copper_wrapped_slashed_ct_template": _ct(161, 0),
                    "copper_wrapped_boiler_side": (161, 32, 16, 48, True, [vertical_strip_to_horizontal_kryppers_single]),
                    "copper_wrapped_boiler_side_connected": (161, 32, 16, 48, True, [vertical_strip_to_horizontal_kryppers]),
                },
                palettized_src=merge_sheet_splitters([
                    build_sheet_splitter("boilers.png", [
                        split_vertically_auto,
                        split_horizontally_auto
                    ], step_prefixes=["boilers"]),
                    build_sheet_splitter("iron_lined_sheet.png", [split_palettes_lining_sheet], step_prefixes=["iron_lined"]),
                    build_sheet_splitter("copper_lined_sheet.png", [split_palettes_lining_sheet], step_prefixes=["copper_lined"]),
                ])
                ),
    PaletteConf("smoke", "smoke_sheet.png", "steam_palette.png",
                ['brown', 'red', 'orange', 'yellow', 'lime', 'green', 'cyan', 'light_blue', 'blue', 'purple',
                    'magenta', 'pink', 'white', 'light_gray', 'gray', 'black'],
                'white',
                sectors=smoke_bundle.sectors()),
    PaletteConf("palettes_plus", "palettes_plus_sheet.png", "palettes_plus_palette.png",
                ['brown', 'red', 'orange', 'yellow', 'lime', 'green', 'pine_green', 'cyan', 'turquoise', 'light_blue', 'blue',
                 'royal_blue', 'purple', 'magenta', 'pink', 'white', 'light_gray', 'gray', 'black', 'netherite'],
                'netherite',
                palette_processors=[shift_horiz(None, -1), shift_vert(None, -1), half_scale],
                permitted_palette_empty_columns=1,
                sectors={
                    "slashed": _16(16, 16),
                    "slashed_connected": _ct_pre_exp(256, 16),
                    "riveted": _16(32, 16),
                    "riveted_connected": _ct_pre_exp(384, 16),
                    "sheeting": _16(48, 16),
                    "annexed_slashed": _16(64, 16),
                    "annexed_riveted": _16(80, 16),

                    "riveted_pillar_top": _16(128, 16),
                    "riveted_pillar_side": _16(128, 32),
                    "riveted_pillar_side_connected": _32(128, 64),

                    "smokebox_tank_top": _16(176, 16),
                    "tank_side": _16(176, 32),
                    "tank_side_connected": _32(176, 64),

                    # boiler doors
                    "boiler_gullet": (16, 48, 32, 32, True, [expand_diagonals]),
                    "smokebox_door": (48, 48, 32, 32, True, [expand_diagonals]),
                    "boiler_slashed": (80, 48, 32, 32, True, [expand_diagonals]),

                    # boilers
                    "boiler_side": _16(224, 16),
                    "boiler_side_connected": _32(224, 32),
                    "wrapped_boiler_side": _16(512, 31),
                    "wrapped_boiler_side_connected": _32(512, 47),
                    "copper_wrapped_boiler_side": _16(688, 31),
                    "copper_wrapped_boiler_side_connected": _32(688, 47),
                    "iron_wrapped_boiler_side": _16(848, 31),
                    "iron_wrapped_boiler_side_connected": _32(848, 47),

                    # wrapped
                    "wrapped_slashed": _16(512, 15),
                    "wrapped_slashed_connected": _ct_pre_exp(544, 15),
                    "copper_wrapped_slashed": _16(688, 15),
                    "copper_wrapped_slashed_connected": _ct_pre_exp(720, 15),
                    "iron_wrapped_slashed": _16(848, 15),
                    "iron_wrapped_slashed_connected": _ct_pre_exp(880, 15),
                })
]

for palette_set in palette_sets:
    if palette_set.name != "palettes_plus": continue
    palette_set.palettize()
    palette_set.sectorize()
    palette_set.gen_preview_rp()
