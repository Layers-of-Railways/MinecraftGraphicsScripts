import typing
from typing import Iterator

import pygame
pygame.init()

# directions
class Direction:
    __count = 0
    def __init__(self):
        self.idx = Direction.__count
        Direction.__count += 1

    def __int__(self):
        return self.idx
N = Direction()
NE = Direction()
E = Direction()
SE = Direction()
S = Direction()
SW = Direction()
W = Direction()
NW = Direction()

# sides
class Side:
    __count = 0
    ALL: list["Side"] = []
    def __init__(self, direction: Direction):
        self.idx = Side.__count
        Side.__count += 1
        self.direction = direction
        Side.ALL.append(self)

    def __int__(self):
        return self.idx
TOP = Side(N)
RIGHT = Side(E)
BOTTOM = Side(S)
LEFT = Side(W)

# corners
class Corner:
    ALL: list["Corner"] = []
    __count = 0
    def __init__(self, direction: Direction, sides: tuple[Side, Side], start_coord: tuple[int, int]):
        self.idx = Corner.__count
        Corner.__count += 1
        self.direction = direction
        self.sides = sides
        Corner.ALL.append(self)
        self.start_coord = start_coord
        self.x, self.y = start_coord

    def __int__(self):
        return self.idx
TOP_RIGHT = Corner(NE, (TOP, RIGHT), (8, 0))
BOTTOM_RIGHT = Corner(SE, (BOTTOM, RIGHT), (8, 8))
BOTTOM_LEFT = Corner(SW, (BOTTOM, LEFT), (0, 8))
TOP_LEFT = Corner(NW, (TOP, LEFT), (0, 0))


T = typing.TypeVar("T")

DirectionLike = typing.Union[Direction, Side, Corner]

class DirectionList(typing.Generic[T], typing.Iterable):
    def __iter__(self) -> Iterator[T]:
        return iter(self._backing_list)

    def __init__(self, backing_list: list[T]):
        self._backing_list: list[T] = backing_list

    def __getitem__(self, direction: DirectionLike) -> T:
        if not isinstance(direction, Direction):
            direction = direction.direction
        direction: Direction
        return self._backing_list[int(direction)]

    def __setitem__(self, direction: DirectionLike, value: T):
        if not isinstance(direction, Direction):
            direction = direction.direction
        direction: Direction
        self._backing_list[int(direction)] = value

    def __len__(self):
        return len(self._backing_list)


class TileDef:
    def __init__(self, empty: bool = False):
        self.adjacent: DirectionList[bool] = DirectionList([False, False, False, False, False, False, False, False])
        self.empty = empty

    def is_island(self) -> bool:
        return sum(self.adjacent) == 0

    def is_borderless(self):
        return sum(self.adjacent) == 8

    def draw_edge(self, side: Side) -> bool:
        # draw an edge if there is no adjacent tile on that side
        return not self.adjacent[side]

    def draw_corner(self, corner: Corner) -> bool:
        return self.draw_edge(corner.sides[0]) and self.draw_edge(corner.sides[1])

    def draw_inner_corner(self, corner: Corner) -> bool:
        return (not self.draw_edge(corner.sides[0])) and (not self.draw_edge(corner.sides[1])) and not self.adjacent[corner]

    def draw_fancy_corner(self, corner: Corner) -> bool:
        for other_corner in Corner.ALL:
            if self.draw_inner_corner(other_corner):
                return False
            if self.draw_corner(other_corner) ^ (other_corner == corner):
                return False
        return True

    @staticmethod
    def from_str(s: str) -> "TileDef":
        out = TileDef()
        d = {
            "n": N,
            "ne": NE,
            "e": E,
            "se": SE,
            "s": S,
            "sw": SW,
            "w": W,
            "nw": NW
        }
        for v in s.split(" "):
            if v == "":
                continue
            out.adjacent[d[v]] = True
        return out


EMPTY_TILE = TileDef(True)

class SheetDef:
    def __init__(self):
        self.rows: list[list[TileDef]] = []

    def next(self, tile: str) -> "SheetDef":
        self.rows[-1].append(TileDef.from_str(tile))
        return self

    def new_row(self, tile: str) -> "SheetDef":
        self.rows.append([TileDef.from_str(tile)])
        return self

    def row(self, *tile: str) -> "SheetDef":
        if len(tile) >= 1:
            self.new_row(tile[0])
        for t in tile[1:]:
            self.next(t)
        return self

    def get(self, x: int, y: int):
        if 8 <= x < 0 or 8 <= y < 0:
            return EMPTY_TILE
        try:
            return self.rows[y][x]
        except IndexError:
            return EMPTY_TILE


SHEET = SheetDef()\
    .row("", "n", "s", "n s")\
    .row("w", "n w", "s w", "n s w", "n nw w", "s sw w")\
    .row("e", "n e", "s e", "n s e", "n ne e", "s se e")\
    .row("e w", "n e w", "s e w", "n e s w", "ne n e s w", "nw n e s w", "ne nw n e s w")\
    .row("n s w sw", "n s w nw", "n s w nw sw", "sw n e s w", "ne sw n e s w", "nw sw n e s w", "nw ne sw n e s w")\
    .row("n e s se", "n e s ne", "n e s ne se", "se n e s w", "ne se n e s w", "nw se n e s w", "nw ne se n e s w")\
    .row("n e w nw", "n e w ne", "n e w nw ne", "sw se n e s w", "ne sw se n e s w", "nw sw se n e s w", "nw ne sw se n e s w")\
    .row("e s w sw", "e s w se", "e s w se sw")

EMPTY_SURF = pygame.Surface((16, 16), pygame.SRCALPHA)

def generate_ct(img: pygame.Surface) -> pygame.Surface:
    out = pygame.Surface((128, 128), pygame.SRCALPHA)
    cells: list[pygame.Surface] = []
    for j in range(2):
        for i in range(4):
            cells.append(img.subsurface((i * 16, j * 16, 16, 16)))
    default_corners, inner_corners, horizontal_borders, vertical_borders, default_bg, borderless_bg, fancy_corners, standalone = cells
    for x in range(8):
        for y in range(8):
            tile_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
            tile: TileDef = SHEET.get(x, y)
            if tile.empty:
                pass
            elif tile.is_island():
                tile_surf.blit(standalone, (0, 0))
            elif tile.is_borderless():
                tile_surf.blit(borderless_bg, (0, 0))
            else:
                # draw order:
                # 1. Background
                # 2. Edges
                # 3. Corners

                # 1. Background
                tile_surf.blit(default_bg, (0, 0))

                # 2. Edges
                if tile.draw_edge(LEFT) and tile.draw_edge(RIGHT):
                    tile_surf.blit(vertical_borders, (0, 0))
                elif tile.draw_edge(LEFT):
                    tile_surf.blit(vertical_borders.subsurface((0, 0, 8, 16)), (0, 0))
                elif tile.draw_edge(RIGHT):
                    tile_surf.blit(vertical_borders.subsurface((8, 0, 8, 16)), (8, 0))

                if tile.draw_edge(TOP) and tile.draw_edge(BOTTOM):
                    tile_surf.blit(horizontal_borders, (0, 0))
                elif tile.draw_edge(TOP):
                    tile_surf.blit(horizontal_borders.subsurface((0, 0, 16, 8)), (0, 0))
                elif tile.draw_edge(BOTTOM):
                    tile_surf.blit(horizontal_borders.subsurface((0, 8, 16, 8)), (0, 8))

                # 3. Corners
                # Order:
                # 1. Fancy
                # 2. Inner
                # 3. Default
                for corner in Corner.ALL:
                    if tile.draw_fancy_corner(corner):
                        tile_surf.blit(fancy_corners.subsurface((corner.x, corner.y, 8, 8)), (corner.x, corner.y))
                    elif tile.draw_inner_corner(corner):
                        tile_surf.blit(inner_corners.subsurface((corner.x, corner.y, 8, 8)), (corner.x, corner.y))
                    elif tile.draw_corner(corner):
                        tile_surf.blit(default_corners.subsurface((corner.x, corner.y, 8, 8)), (corner.x, corner.y))

            out.blit(tile_surf, (x * 16, y * 16))
    return out

if __name__ == "__main__":
    pygame.image.save(generate_ct(pygame.image.load("demo_input.png")), "demo_output.png")