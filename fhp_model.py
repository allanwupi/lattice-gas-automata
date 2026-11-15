#!/usr/bin/env python3
'''
Frisch-Hasslacher-Pomeau (FHP) model
Hexagonal lattice: 7 velocities (6 directions + stationary)
'''
from enum import IntFlag, auto
from collections import Counter
import sys, time, shutil, random


DELAY_SECONDS = 0.05
MAX_SIMULATION_TICKS = 1200
OBSTACLE_RADIUS = 12
OBSTACLE_SHAPE = "circle"
COLOUR_SCHEME = False
DRAW_ARROWS = False
EMITTER_WALL = False
PARTICLE_DENSITY = [
    "  ",
    ". ",
    ": ",
    "+ ",
    "* ",
    "% ",
    "@ ",
    "$ ",
]

# REST E NE NW W SW SE
COLLISION_RULES = {
    # 3x Type (a)
    0b0_100_100: [0b0_010_010, 0b0_001_001],
    0b0_010_010: [0b0_001_001, 0b0_100_100],
    0b0_001_001: [0b0_100_100, 0b0_010_010],
    # 2x Type (b)
    0b0_101_010: 0b0_010_101,
    0b0_010_101: 0b0_101_010,
    # 6x Type (c)
    0b0_010_001: 0b1_100_000,
    0b0_101_000: 0b1_010_000,
    0b0_010_100: 0b1_001_000,
    0b0_001_010: 0b1_000_100,
    0b0_000_101: 0b1_000_010,
    0b0_100_010: 0b1_000_001,
    # 6x Type (d)
    0b1_100_000: 0b0_010_001,
    0b1_010_000: 0b0_101_000,
    0b1_001_000: 0b0_010_100,
    0b1_000_100: 0b0_001_010,
    0b1_000_010: 0b0_000_101,
    0b1_000_001: 0b0_100_010,
    # 3x Type (e)
    0b1_100_100: [0b1_010_010, 0b1_001_001],
    0b1_010_010: [0b1_001_001, 0b1_100_100],
    0b1_001_001: [0b1_100_100, 0b1_010_010],
    # 12x Type (f)
    0b0_100_110: [0b0_001_011, 0b1_000_101],
    0b0_100_101: [0b0_010_011, 0b1_100_010],
    0b0_110_100: [0b0_011_001, 0b1_101_000],
    0b0_101_100: [0b0_011_010, 0b1_010_100],
    0b0_010_011: [0b0_100_101, 0b1_100_010],
    0b0_110_010: [0b0_101_001, 0b1_010_001],
    0b0_011_010: [0b0_101_100, 0b1_010_100],
    0b0_010_110: [0b0_001_101, 0b1_001_010],
    0b0_001_101: [0b0_010_110, 0b1_001_010],
    0b0_001_011: [0b0_100_110, 0b1_000_101],
    0b0_101_001: [0b0_110_010, 0b1_010_001],
    0b0_011_001: [0b0_110_100, 0b1_101_000],
    # Duals
    0b1_011_011: [0b1_101_101, 0b1_110_110],
    0b1_101_101: [0b1_110_110, 0b1_011_011],
    0b1_110_110: [0b1_011_011, 0b1_101_101],
    0b1_010_101: 0b1_101_010,
    0b1_101_010: 0b1_010_101,
    0b1_101_110: 0b0_011_111,
    0b1_010_111: 0b0_101_111,
    0b1_101_011: 0b0_110_111,
    0b1_110_101: 0b0_111_011,
    0b1_111_010: 0b0_111_101,
    0b1_011_101: 0b0_111_110,
    0b0_011_111: 0b1_101_110,
    0b0_101_111: 0b1_010_111,
    0b0_110_111: 0b1_101_011,
    0b0_111_011: 0b1_110_101,
    0b0_111_101: 0b1_111_010,
    0b0_111_110: 0b1_011_101,
    0b0_011_011: [0b0_101_101, 0b0_110_110],
    0b0_101_101: [0b0_110_110, 0b0_011_011],
    0b0_110_110: [0b0_011_011, 0b0_101_101],
    0b1_011_001: [0b1_110_100, 0b0_111_010],
    0b1_011_010: [0b1_101_100, 0b0_011_101],
    0b1_001_011: [0b1_100_110, 0b0_010_111],
    0b1_010_011: [0b1_100_101, 0b0_101_011],
    0b1_101_100: [0b1_011_010, 0b0_011_101],
    0b1_001_101: [0b1_010_110, 0b0_101_110],
    0b1_100_101: [0b1_010_011, 0b0_101_011],
    0b1_101_001: [0b1_110_010, 0b0_110_101],
    0b1_110_010: [0b1_101_001, 0b0_110_101],
    0b1_110_100: [0b1_011_001, 0b0_111_010],
    0b1_010_110: [0b1_001_101, 0b0_101_110],
    0b1_100_110: [0b1_001_011, 0b0_010_111],
}


class FHPChannel(IntFlag):
    EMPTY = 0
    SE = auto()
    SW = auto()
    W = auto()
    NW = auto()
    NE = auto()
    E = auto()
    REST = auto()

    def __str__(self) -> str:
        if DRAW_ARROWS:
            match self:
                case FHPChannel.NW: return "↖ "
                case FHPChannel.NE: return " ↗"
                case FHPChannel.SE: return " ↘"
                case FHPChannel.SW: return "↙ "
                case FHPChannel.E: return "→ "
                case FHPChannel.W: return " ←"
        return PARTICLE_DENSITY[len(self)]


def neighbourhood(x: int, y: int, rows: int, cols: int, wraprows: bool = False, wrapcols: bool = True) -> dict[FHPChannel, tuple[int, int]]:
    def wraparound(x: int, y: int):
        nx, ny = x, y
        if wraprows:
            nx = (x+rows) % rows
        if wrapcols:
            ny = (y+cols) % cols
        return (nx, ny)
    neighbours = {
        FHPChannel.W: wraparound(x,y-1),
        FHPChannel.E: wraparound(x,y+1)
    }
    if x % 2 == 0:  # Even rows
        neighbours[FHPChannel.NW] = wraparound(x-1,y-1)
        neighbours[FHPChannel.NE] = wraparound(x-1,y)
        neighbours[FHPChannel.SW] = wraparound(x+1,y-1)
        neighbours[FHPChannel.SE] = wraparound(x+1,y)
    else:  # Odd rows
        neighbours[FHPChannel.NW] = wraparound(x-1,y)
        neighbours[FHPChannel.NE] = wraparound(x-1,y+1)
        neighbours[FHPChannel.SW] = wraparound(x+1,y)
        neighbours[FHPChannel.SE] = wraparound(x+1,y+1)
    return neighbours


def obstacle(dx: int, dy: int, shape: str = OBSTACLE_SHAPE):
    match shape:
        case "circle":  # Euclidian distance
            return abs(dx)**2 + abs(dy)**2 <= OBSTACLE_RADIUS**2
        case "square":  # Chebyshev distance
            return max(abs(dx), abs(dy)) <= OBSTACLE_RADIUS
        case "diamond":  # Manhattan distance
            return abs(dx) + abs(dy) <= OBSTACLE_RADIUS
        case _:
            return False
    

def collision_step(grid: list[list[FHPChannel]]) -> None:
    for x, row in enumerate(grid):
        for y, cell in enumerate(row):
            next_state = cell
            out_states = COLLISION_RULES.get(cell, None)
            if out_states is not None:
                if isinstance(out_states, list):
                    next_state = FHPChannel(random.choice(out_states))
                else:
                    next_state = FHPChannel(out_states)
            grid[x][y] = next_state


def transport_step(grid: list[list[FHPChannel]]):
    rows, cols = len(grid), len(grid[0])
    update = [[FHPChannel.EMPTY for _ in range(cols)] for _ in range(rows)]
    def within_bounds(cell: tuple[int, int]):
        cx, cy = rows//2, cols//2
        x, y = cell[0], cell[1]
        return (
            0 <= x < rows
            and 0 <= y < cols
            and not obstacle(x-cx, y-cy)
        )
    for x, line in enumerate(grid):
        for y, cell in enumerate(line):
            if EMITTER_WALL:
                if y == cols-1:
                    update[x][cols-1] |= FHPChannel.W
                elif y == 0:
                    continue
            neighbours = neighbourhood(x, y, rows, cols)
            if FHPChannel.E in cell:
                nx, ny = neighbours[FHPChannel.E]
                if within_bounds((nx,ny)):
                    update[nx][ny] |= FHPChannel.E
                else:
                    update[x][y] |= FHPChannel.W
            if FHPChannel.NE in cell:
                nx, ny = neighbours[FHPChannel.NE]
                if within_bounds((nx,ny)):
                    update[nx][ny] |= FHPChannel.NE
                else:
                    update[x][y] |= FHPChannel.SW
            if FHPChannel.NW in cell:
                nx, ny = neighbours[FHPChannel.NW]
                if within_bounds((nx,ny)):
                    update[nx][ny] |= FHPChannel.NW
                else:
                    update[x][y] |= FHPChannel.SE
            if FHPChannel.W in cell:
                nx, ny = neighbours[FHPChannel.W]
                if within_bounds((nx,ny)):
                    update[nx][ny] |= FHPChannel.W
                else:
                    update[x][y] |= FHPChannel.E
            if FHPChannel.SW in cell:
                nx, ny = neighbours[FHPChannel.SW]
                if within_bounds((nx,ny)):
                    update[nx][ny] |= FHPChannel.SW
                else:
                    update[x][y] |= FHPChannel.NE
            if FHPChannel.SE in cell:
                nx, ny = neighbours[FHPChannel.SE]
                if within_bounds((nx,ny)):
                    update[nx][ny] |= FHPChannel.SE
                else:
                    update[x][y] |= FHPChannel.NW
            if FHPChannel.REST in cell:
                update[x][y] |= FHPChannel.REST
    return update

                   
def display_grid(grid: list[list[FHPChannel]]):
    for x, row in enumerate(grid):
        if x % 2 == 1:  # Odd row, offset by half
            print(" ", end="")
        for cell in row:
            print(cell, end="")
        print()


def random_world(rows: int, cols: int, spawn: list[int]) -> list[list[FHPChannel]]:
    grid = [[FHPChannel(random.choice(spawn)) for _ in range(cols)] for _ in range(rows)]
    cx, cy = rows//2, cols//2
    # Apply a majority filter to produce smooth blobs
    smoothed = [[FHPChannel.EMPTY for _ in range(cols)] for _ in range(rows)]
    for x in range(rows):
        for y in range(cols):
            if obstacle(x-cx, y-cy):
                smoothed[x][y] = FHPChannel.EMPTY
                continue
            neighbors = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < rows and 0 <= ny < cols:
                        neighbors.append(grid[nx][ny])
            # Add occasional noise to prevent uniform results
            if random.random() < 0.1:
                smoothed[x][y] = FHPChannel(random.choice(spawn))
            else:
                smoothed[x][y] = Counter(neighbors).most_common(1)[0][0]
    return smoothed


def main():
    size = shutil.get_terminal_size()
    ROWS = size.lines-1
    COLS = size.columns // 2 - 1
    CLEAR_LINE = "\x1b[1F\x1b[2K"  # ANSI escape code string
    spawn = [0, 0, 4, 4, 4]
    if len(sys.argv) > 1:
        spawn = []
        for x in sys.argv[1:]:
            value = int(x)
            if value == 0:
                spawn.extend([0]*len(x))
            else:
                spawn.append(value)
    world = random_world(ROWS, COLS, spawn)
    if COLOUR_SCHEME:
        print("\x1b[1;44m")
    try:
        for _ in range(MAX_SIMULATION_TICKS):
            start = time.perf_counter()
            display_grid(world)
            collision_step(world)
            world = transport_step(world)
            delay = DELAY_SECONDS - time.perf_counter() + start
            if delay > 0:
                time.sleep(delay)
            print(CLEAR_LINE*ROWS, end="")
    except KeyboardInterrupt:
        print(CLEAR_LINE*ROWS, end="")
    print("\x1b[0m")


if __name__ == "__main__":
    main()
