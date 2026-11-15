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
COLOUR_SCHEME = "blue"
GRAPHIC_STYLE = "block"
SMOOTH_FILTER = True


class HPPChannel(IntFlag):
    EMPTY = 0
    N = auto()
    S = auto()
    E = auto()
    W = auto()

    def __str__(self) -> str:
        PARTICLE_DENSITY = {
            "arrow": ["  ", "..", "++", "%%", "@@"],
            "block": ["  ", "░░", "▒▒", "▓▓", "██"]
        }
        particle_count = len(self)
        if GRAPHIC_STYLE == "arrow":
            if particle_count >= 2:
                if self == (HPPChannel.E | HPPChannel.W): return "→←"
                if self == (HPPChannel.N | HPPChannel.S): return "↑↓"
            if particle_count >= 1:
                if self == HPPChannel.N: return "↑ "
                if self == HPPChannel.S: return "↓ "
                if self == HPPChannel.E: return "→ "
                if self == HPPChannel.W: return " ←"
        return PARTICLE_DENSITY[GRAPHIC_STYLE][particle_count]


def collision_step(grid: list[list[HPPChannel]]) -> None:
    # Head-on collision between two particles
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell == (HPPChannel.N | HPPChannel.S):
                grid[i][j] = (HPPChannel.E | HPPChannel.W)
            if cell == (HPPChannel.E | HPPChannel.W):
                grid[i][j] = (HPPChannel.N | HPPChannel.S)


def transport_step(grid: list[list[HPPChannel]], wraprows: bool = False, wrapcols: bool = False) -> list[list[HPPChannel]]:
    rows, cols = len(grid), len(grid[0])
    update = [[HPPChannel.EMPTY for _ in range(cols)] for _ in range(rows)]
    for i, line in enumerate(grid):
        for j, cell in enumerate(line):
            if HPPChannel.N in cell:  # North
                if (i-1) >= 0:
                    update[i-1][j] |= HPPChannel.N
                elif wraprows:
                    update[rows-1][j] |= HPPChannel.N
                else:
                    update[i][j] |= HPPChannel.S
            if HPPChannel.S in cell:  # South
                if (i+1) < rows:
                    update[i+1][j] |= HPPChannel.S
                elif wraprows:
                    update[0][j] |= HPPChannel.S
                else:
                    update[i][j] |= HPPChannel.N
            if HPPChannel.E in cell:  # East
                if (j+1) < cols:
                    update[i][j+1] |= HPPChannel.E
                elif wrapcols:
                    update[i][0] |= HPPChannel.E
                else:
                    update[i][j] |= HPPChannel.W
            if HPPChannel.W in cell:  # West
                if (j-1) >= 0:
                    update[i][j-1] |= HPPChannel.W
                elif wrapcols:
                    update[i][cols-1] |= HPPChannel.W
                else:
                    update[i][j] |= HPPChannel.E
    return update


def display_grid(grid: list[list[HPPChannel]]):
    for row in grid:
        for cell in row:
            print(str(cell), end="")
        print()


def random_world(rows: int, cols: int, spawn: list[int], smoothing: int = 2) -> list[list[HPPChannel]]:
    grid = [[HPPChannel(random.choice(spawn)) for _ in range(cols)] for _ in range(rows)]
    if not SMOOTH_FILTER:
        return grid
    # Repeatedly apply a majority filter to produce smooth blobs
    for _ in range(smoothing):
        updated = [[HPPChannel.EMPTY for _ in range(cols)] for _ in range(rows)]
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
                    updated[i][j] = HPPChannel(random.choice(spawn))
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
    if COLOUR_SCHEME == "blue":
        print("\x1b[1;94;44m")
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
