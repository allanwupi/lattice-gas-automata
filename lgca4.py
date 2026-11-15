#!/usr/bin/env python3
'''
Hardy-Pomeau-Pazzis (HPP) model
Square lattice: 4 velocities
'''
from enum import StrEnum, IntFlag, auto
from collections import Counter
import sys, time, shutil, random


# Simulation configuration
DELAY_SECONDS = 0.05
MAX_SIMULATION_TICKS = 1200
SMOOTH_FILTER = True

class ColourScheme(StrEnum):
    BLACK = "\033[37;40m;"
    BLUE = "\x1b[1;44m"
    DEEPBLUE = "\x1b[1;94;44m"
    RED = "\x1b[1;30;41m"
    WHITE = "\x1b[1;47m"
    RESET = "\x1b[0m"

class GraphicStyle(StrEnum):
    ARROW = auto()
    BLOCK = auto()

# Customise appearance
COLOUR_SCHEME = ColourScheme.BLUE
GRAPHIC_STYLE = GraphicStyle.BLOCK


class Particle(IntFlag):
    EMPTY = 0
    N = auto()
    S = auto()
    E = auto()
    W = auto()

    def __str__(self) -> str:
        PARTICLE_DENSITY = {
            GraphicStyle.ARROW: ["  ", "..", "++", "%%", "@@"],
            GraphicStyle.BLOCK: ["  ", "░░", "▒▒", "▓▓", "██"]
        }
        particle_count = len(self)
        if GRAPHIC_STYLE == GraphicStyle.ARROW:
            if particle_count >= 2:
                if self == (Particle.E | Particle.W): return "→←"
                if self == (Particle.N | Particle.S): return "↑↓"
            if particle_count >= 1:
                if self == Particle.N: return "↑ "
                if self == Particle.S: return "↓ "
                if self == Particle.E: return "→ "
                if self == Particle.W: return " ←"
        return PARTICLE_DENSITY[GRAPHIC_STYLE][particle_count]


class Lattice:
    def __init__(self, rows: int, cols: int, spawn: list[int], smoothing: int = 2, wraprows: bool = False, wrapcols: bool = False):
        self.grid = [[Particle(random.choice(spawn)) for _ in range(cols)] for _ in range(rows)]
        self.rows, self.cols = rows, cols
        self.wraprows = wraprows
        self.wrapcols = wrapcols
        if not SMOOTH_FILTER:
            return
        # Repeatedly apply a majority filter to produce smooth blobs
        for _ in range(smoothing):
            updated = [[Particle.EMPTY for _ in range(cols)] for _ in range(rows)]
            for i in range(rows):
                for j in range(cols):
                    neighbors = []
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            ii = i + dr
                            jj = j + dc
                            if 0 <= ii < rows and 0 <= jj < cols:
                                neighbors.append(self.grid[ii][jj])
                    # Add occasional noise to prevent uniform results
                    if random.random() < 0.1:
                        updated[i][j] = Particle(random.choice(spawn))
                    else:
                        updated[i][j] = Counter(neighbors).most_common(1)[0][0]
            self.grid = updated

    def transport_step(self) -> None:
        update = [[Particle.EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
        for i, line in enumerate(self.grid):
            for j, cell in enumerate(line):
                if Particle.N in cell:  # North
                    if (i-1) >= 0:
                        update[i-1][j] |= Particle.N
                    elif self.wraprows:
                        update[self.rows-1][j] |= Particle.N
                    else:
                        update[i][j] |= Particle.S
                if Particle.S in cell:  # South
                    if (i+1) < self.rows:
                        update[i+1][j] |= Particle.S
                    elif self.wraprows:
                        update[0][j] |= Particle.S
                    else:
                        update[i][j] |= Particle.N
                if Particle.E in cell:  # East
                    if (j+1) < self.cols:
                        update[i][j+1] |= Particle.E
                    elif self.wrapcols:
                        update[i][0] |= Particle.E
                    else:
                        update[i][j] |= Particle.W
                if Particle.W in cell:  # West
                    if (j-1) >= 0:
                        update[i][j-1] |= Particle.W
                    elif self.wrapcols:
                        update[i][self.cols-1] |= Particle.W
                    else:
                        update[i][j] |= Particle.E
        self.grid = update

    def collision_step(self) -> None:
        # Head-on collision between two particles
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                if cell == (Particle.N | Particle.S):
                    self.grid[i][j] = (Particle.E | Particle.W)
                if cell == (Particle.E | Particle.W):
                    self.grid[i][j] = (Particle.N | Particle.S)
    
    def __str__(self) -> str:
        chars = []
        for x, row in enumerate(self.grid):
            for y, cell in enumerate(row):
                chars.append(str(cell))
            chars.append("\n")
        return "".join(chars)


def main():
    size = shutil.get_terminal_size()
    ROWS = size.lines-1
    COLS = size.columns // 2
    CLEAR_LINE = "\x1b[1F\x1b[2K"  # ANSI escape code string
    CLEAR_SCREEN = CLEAR_LINE * ROWS
    spawn = [0,8,8,8]
    if len(sys.argv) > 1:
        spawn = []
        for x in sys.argv[1:]:
            value = int(x)
            if value == 0:
                spawn.extend([0]*len(x))
            else:
                spawn.append(value)
    world = Lattice(ROWS, COLS, spawn=spawn)
    print(COLOUR_SCHEME, end="")
    try:
        for _ in range(MAX_SIMULATION_TICKS):
            start = time.perf_counter()
            print(world, end="")
            world.collision_step()
            world.transport_step()
            delay = DELAY_SECONDS - time.perf_counter() + start
            if delay > 0:
                time.sleep(delay)
            print(CLEAR_SCREEN, end="")
    except KeyboardInterrupt:
        pass
    print(f"{ColourScheme.RESET}{CLEAR_SCREEN}", end="")


if __name__ == "__main__":
    main()
