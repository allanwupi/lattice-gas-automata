#!/usr/bin/env python3
'''
Hardy-Pomeau-Pazzis (HPP) model
Square lattice: 4 velocities
'''
from enum import IntFlag, auto
from collections import Counter
import sys, time, shutil, random


DELAY_SECONDS = 0.05
MAX_SIMULATION_TICKS = 1200
BLOCK_GRAPHICS = True
COLOUR_SCHEME = True
SMOOTH_FILTER = True
PARTICLE_DENSITY = [
    "  ",
    "░░",
    "▒▒",
    "▓▓",
    "██",
]


class Channel(IntFlag):
    EMPTY = 0
    N = auto()
    S = auto()
    E = auto()
    W = auto()

    def __str__(self) -> str:
        count = len(self)
        if count >= 4: return r"@@"
        if count >= 3: return r"%%"
        if count >= 2:
            if self == (Channel.E | Channel.W): return "→←"
            if self == (Channel.N | Channel.S): return "↑↓"
            return "++"
        if count >= 1:
            if self == Channel.N: return "↑ "
            if self == Channel.S: return "↓ "
            if self == Channel.E: return "→ "
            if self == Channel.W: return " ←"
        return "  "


def collision_step(grid: list[list[Channel]]) -> None:
    # Head-on collision between two particles
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell == (Channel.N | Channel.S):
                grid[i][j] = (Channel.E | Channel.W)
            if cell == (Channel.E | Channel.W):
                grid[i][j] = (Channel.N | Channel.S)


def transport_step(grid: list[list[Channel]], wraprows: bool = False, wrapcols: bool = False) -> list[list[Channel]]:
    rows, cols = len(grid), len(grid[0])
    update = [[Channel.EMPTY for _ in range(cols)] for _ in range(rows)]
    for i, line in enumerate(grid):
        for j, cell in enumerate(line):
            if Channel.N in cell:  # North
                if (i-1) >= 0:
                    update[i-1][j] |= Channel.N
                elif wraprows:
                    update[rows-1][j] |= Channel.N
                else:
                    update[i][j] |= Channel.S
            if Channel.S in cell:  # South
                if (i+1) < rows:
                    update[i+1][j] |= Channel.S
                elif wraprows:
                    update[0][j] |= Channel.S
                else:
                    update[i][j] |= Channel.N
            if Channel.E in cell:  # East
                if (j+1) < cols:
                    update[i][j+1] |= Channel.E
                elif wrapcols:
                    update[i][0] |= Channel.E
                else:
                    update[i][j] |= Channel.W
            if Channel.W in cell:  # West
                if (j-1) >= 0:
                    update[i][j-1] |= Channel.W
                elif wrapcols:
                    update[i][cols-1] |= Channel.W
                else:
                    update[i][j] |= Channel.E
    return update


def display_grid(grid: list[list[Channel]], shade: bool = False):
    for row in grid:
        for cell in row:
            if shade:
                print(PARTICLE_DENSITY[len(cell)], end="")
            else:
                print(str(cell), end="")
        print()


def random_world(rows: int, cols: int, spawn: list[int], smoothing: int = 2) -> list[list[Channel]]:
    grid = [[Channel(random.choice(spawn)) for _ in range(cols)] for _ in range(rows)]
    if not SMOOTH_FILTER:
        return grid
    # Repeatedly apply a majority filter to produce smooth blobs
    for _ in range(smoothing):
        updated = [[Channel.EMPTY for _ in range(cols)] for _ in range(rows)]
        for i in range(rows):
            for j in range(cols):
                neighbors = []
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        ii = i + dr
                        jj = j + dc
                        if 0 <= ii < rows and 0 <= jj < cols:
                            neighbors.append(grid[ii][jj])
                # Add occasional noise to prevent uniform results
                if random.random() < 0.1:
                    updated[i][j] = Channel(random.choice(spawn))
                else:
                    updated[i][j] = Counter(neighbors).most_common(1)[0][0]
        grid = updated
    return grid


def main():
    size = shutil.get_terminal_size()
    ROWS = size.lines-1
    COLS = size.columns // 2
    CLEAR_LINE = "\x1b[1F\x1b[2K"  # ANSI escape code string
    spawn = [0,8,8,8]
    if len(sys.argv) > 1:
        spawn = []
        for x in sys.argv[1:]:
            value = int(x)
            if value == 0:
                spawn.extend([0]*len(x))
            else:
                spawn.append(value)
    world = random_world(ROWS, COLS, spawn=spawn)
    if COLOUR_SCHEME:
        print("\x1b[1;94;44m")
    try:
        for _ in range(MAX_SIMULATION_TICKS):
            start = time.perf_counter()
            display_grid(world, shade=BLOCK_GRAPHICS)
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
