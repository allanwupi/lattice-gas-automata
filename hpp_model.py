#!/usr/bin/env python3
'''
Hardy-Pomeau-Pazzis (HPP) model
Square lattice: 4 velocities
'''

DELAY_SECONDS = 0.05
MAX_SIMULATION_TICKS = 600
PARTICLE_DENSITY = [
    "  ",
    "░░",
    "▒▒",
    "▓▓",
    "██",
]

from enum import IntFlag, auto

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
            if self == (Channel.E | Channel.W): return "←→"
            if self == (Channel.N | Channel.S): return "↑↓"
            return "++"
        if count >= 1:
            if self == Channel.N: return "↑ "
            if self == Channel.S: return " ↓"
            if self == Channel.E: return " →"
            if self == Channel.W: return "← "
        return "  "


def collision_step(grid: list[list[Channel]]) -> None:
    # Head-on collision between two particles
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell == (Channel.N | Channel.S):
                grid[i][j] = (Channel.E | Channel.W)
            if cell == (Channel.E | Channel.W):
                grid[i][j] = (Channel.N | Channel.S)


def transport_step(grid: list[list[Channel]], wraprows: bool = False, wrapcols: bool = True) -> list[list[Channel]]:
    rows = len(grid)
    cols = len(grid[0])
    update = [[Channel.EMPTY for _ in range(cols)] for _ in range(rows)]
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            # North movement
            if Channel.N in cell:
                if (i-1) >= 0:
                    update[i-1][j] |= Channel.N
                elif wraprows:
                    update[rows-1][j] |= Channel.N
                else:
                    update[i][j] |= Channel.S
            # South movement
            if Channel.S in cell:
                if (i+1) <= rows-1:
                    update[i+1][j] |= Channel.S
                elif wraprows:
                    update[0][j] |= Channel.S
                else:
                    update[i][j] |= Channel.N
            # East movement
            if Channel.E in cell:
                if (j+1) <= cols-1:
                    update[i][j+1] |= Channel.E
                elif wrapcols:
                    update[i][0] |= Channel.E
                else:
                    update[i][j] |= Channel.W
            # West movement
            if Channel.W in cell:
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


def random_world(rows: int, cols: int, seed: list[int] = [0, 1]) -> list[list[Channel]]:
    from random import choice
    return [
        [Channel(choice(seed)) for _ in range(cols)]
        for _ in range(rows)
    ]


def main():
    import sys, time, shutil
    size = shutil.get_terminal_size()
    ROWS = size.lines
    COLS = size.columns // 2
    CLEAR_LINE = "\x1b[1F\x1b[2K"  # ANSI escape code string
    seed = [0,1,1,1]
    if len(sys.argv) > 1:
        seed = [int(x, 16) for x in sys.argv[1]]
    world = random_world(ROWS, COLS, seed=seed)
    try:
        for _ in range(MAX_SIMULATION_TICKS):
            start = time.perf_counter()
            display_grid(world, shade=False)
            collision_step(world)
            world = transport_step(world)
            delay = DELAY_SECONDS - time.perf_counter() + start
            if delay > 0:
                time.sleep(delay)
            print(CLEAR_LINE*ROWS, end="")
    except KeyboardInterrupt:
        print(CLEAR_LINE*ROWS, end="")


if __name__ == "__main__":
    main()