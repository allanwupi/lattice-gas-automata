#!/usr/bin/env python3
'''
Frisch-Hasslacher-Pomeau (FHP) model
Hexagonal lattice: 7 velocities (6 directions + stationary)
'''
from enum import IntFlag, auto
from random import choice, randint
import sys, time, shutil

PARTICLE_DENSITY = [
    "  ",
    ". ",
    ": ",
    "= ",
    "++",
    "**",
    "%%",
    "@@",
]
DELAY_SECONDS = 0.05
MAX_SIMULATION_TICKS = 600


COLLISION_RULES = {
    # REST E NE NW W SW SE
    # 0123456:   0123456
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
        return PARTICLE_DENSITY[len(self)]


def neighbourhood(i: int, j: int) -> dict[FHPChannel, tuple[int, int]]:
    neighbours = {
        FHPChannel.W: (i,j-1),
        FHPChannel.E: (i,j+1)
    }
    if i % 2 == 0:  # Even rows
        neighbours[FHPChannel.NW] = (i-1,j-1)
        neighbours[FHPChannel.NE] = (i-1,j)
        neighbours[FHPChannel.SW] = (i+1,j-1)
        neighbours[FHPChannel.SE] = (i+1,j)
    else:  # Odd rows
        neighbours[FHPChannel.NW] = (i-1,j)
        neighbours[FHPChannel.NE] = (i-1,j+1)
        neighbours[FHPChannel.SW] = (i+1,j)
        neighbours[FHPChannel.SE] = (i+1,j+1)
    return neighbours
    

def collision_step(grid: list[list[FHPChannel]]) -> None:
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            next_state = cell
            out_states = COLLISION_RULES.get(cell, None)
            if out_states is not None:
                if isinstance(out_states, list):
                    next_state = FHPChannel(choice(out_states))
                else:
                    next_state = FHPChannel(out_states)
            grid[i][j] = next_state


def transport_step(grid: list[list[FHPChannel]]):
    rows, cols = len(grid), len(grid[0])
    update = [[FHPChannel.EMPTY for _ in range(cols)] for _ in range(rows)]
    def within_bounds(cell: tuple[int, int]):
        return (0 <= cell[0] < rows and 0 <= cell[1] < cols)
    for i, line in enumerate(grid):
        for j, cell in enumerate(line):
            neighbours = neighbourhood(i, j)
            if FHPChannel.E in cell:
                if within_bounds(neighbours[FHPChannel.E]):
                    ii, jj = neighbours[FHPChannel.E]
                    update[ii][jj] |= FHPChannel.E
                else:
                    update[i][j] |= FHPChannel.W
            if FHPChannel.NE in cell:
                if within_bounds(neighbours[FHPChannel.NE]):
                    ii, jj = neighbours[FHPChannel.NE]
                    update[ii][jj] |= FHPChannel.NE
                else:
                    update[i][j] |= FHPChannel.SW
            if FHPChannel.NW in cell:
                if within_bounds(neighbours[FHPChannel.NW]):
                    ii, jj = neighbours[FHPChannel.NW]
                    update[ii][jj] |= FHPChannel.NW
                else:
                    update[i][j] |= FHPChannel.SE
            if FHPChannel.W in cell:
                if within_bounds(neighbours[FHPChannel.W]):
                    ii, jj = neighbours[FHPChannel.W]
                    update[ii][jj] |= FHPChannel.W
                else:
                    update[i][j] |= FHPChannel.E
            if FHPChannel.SW in cell:
                if within_bounds(neighbours[FHPChannel.SW]):
                    ii, jj = neighbours[FHPChannel.SW]
                    update[ii][jj] |= FHPChannel.SW
                else:
                    update[i][j] |= FHPChannel.NE
            if FHPChannel.SE in cell:
                if within_bounds(neighbours[FHPChannel.SE]):
                    ii, jj = neighbours[FHPChannel.SE]
                    update[ii][jj] |= FHPChannel.SE
                else:
                    update[i][j] |= FHPChannel.NW
            if FHPChannel.REST in cell:
                update[i][j] |= FHPChannel.REST
    return update

                   
def display_grid(grid: list[list[FHPChannel]]):
    for i, row in enumerate(grid):
        if i % 2 == 1:  # Odd row, offset by half
            print(" ", end="")
        for cell in row:
            print(cell, end="")
        print()


def main():
    size = shutil.get_terminal_size()
    ROWS = size.lines-1
    COLS = size.columns // 2 - 1
    CLEAR_LINE = "\x1b[1F\x1b[2K"  # ANSI escape code string
    seed = [2**i for i in range(len(FHPChannel))]
    seed.extend([0 for _ in range(len(FHPChannel))])
    if len(sys.argv) > 1:
        seed = []
        for x in sys.argv[1:]:
            value = int(x)
            if value == 0:
                seed.extend([0]*len(x))
            else:
                seed.append(value)
    world = [[FHPChannel(choice(seed)) for _ in range(COLS)] for _ in range(ROWS)]
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


if __name__ == "__main__":
    main()
