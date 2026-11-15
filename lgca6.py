#!/usr/bin/env python3
'''
Frisch-Hasslacher-Pomeau (FHP) model
Hexagonal lattice: 7 velocities (6 directions + stationary)
'''
from enum import IntFlag, auto
from collections import Counter
from graphics import ColourScheme, GraphicStyle
import sys, time, shutil, random


# Simulation configuration
DELAY_SECONDS = 0.067
MAX_SIMULATION_TICKS = 6000
OBSTACLE_RADIUS = 30
OBSTACLE_SHAPE = "circle"
VOID_OBSTACLE = False
SMOOTH_FILTER = True
SOURCE_CHANNEL = [0, 32]

# Customise appearance
COLOUR_SCHEME = ColourScheme.BLUE
GRAPHIC_STYLE = GraphicStyle.BLOCK6


PARTICLE_DENSITY = {
    GraphicStyle.DOT6: ["  ", ". ", ": ", "+ ", "* ", "% ", "@ ", "@@"],
    GraphicStyle.ARROW6: ["  ", ". ", "= ", "++", "**", "##", "%%", "@@"],
    GraphicStyle.BLOCK6: ["  ", "░░", "▒▒", "▒▒", "▓▓", "▓▓", "██", "██"]
}


class Particle(IntFlag):
    EMPTY = 0
    SE = auto()     # 1
    SW = auto()     # 2
    W = auto()      # 4
    NW = auto()     # 8
    NE = auto()     # 16
    E = auto()      # 32
    REST = auto()   # 64

    def opposite(self) -> Particle:
        match self:
            case Particle.SE: return Particle.NW
            case Particle.SW: return Particle.NE
            case Particle.W: return Particle.E
            case Particle.NW: return Particle.SE
            case Particle.NE: return Particle.SW
            case Particle.E: return Particle.W
        return Particle.EMPTY 

    def __str__(self) -> str:
        if GRAPHIC_STYLE == GraphicStyle.ARROW6:
            match self:
                case Particle.NW: return "↖ "
                case Particle.NE: return " ↗"
                case Particle.SE: return " ↘"
                case Particle.SW: return "↙ "
                case Particle.E: return "→ "
                case Particle.W: return " ←"
        return PARTICLE_DENSITY[GRAPHIC_STYLE][len(self)]


class Lattice:
    # REST | E N NW | W SW SE
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

    def __init__(self, rows: int, cols: int, spawn: list[int], source: list[int], wraprows: bool = False, wrapcols: bool = False):
        if not spawn:
            spawn = [0]
        if not source:
            source = SOURCE_CHANNEL
        grid = [[Particle(random.choice(spawn)) for _ in range(cols)] for _ in range(rows)]
        cx, cy = rows//2, cols//2
        self.rows, self.cols = rows, cols
        self.source_channel = source
        self.particles = [[Particle.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.walls = [[False for _ in range(cols)] for _ in range(rows)]
        self.neighbourhood = [[dict() for _ in range(cols)] for _ in range(rows)]
        self.wraprows = wraprows
        self.wrapcols = wrapcols
        def wraparound(x: int, y: int):
            return ((x+rows) % rows if self.wraprows else x, (y+cols) % cols if self.wrapcols else y)
        for x in range(rows):
            for y in range(cols):
                neighbours = {
                    Particle.REST: (x,y),
                    Particle.W: wraparound(x,y-1),
                    Particle.E: wraparound(x,y+1)
                }
                if x % 2 == 0:  # Even rows
                    neighbours[Particle.NW] = wraparound(x-1,y-1)
                    neighbours[Particle.NE] = wraparound(x-1,y)
                    neighbours[Particle.SW] = wraparound(x+1,y-1)
                    neighbours[Particle.SE] = wraparound(x+1,y)
                else:  # Odd rows
                    neighbours[Particle.NW] = wraparound(x-1,y)
                    neighbours[Particle.NE] = wraparound(x-1,y+1)
                    neighbours[Particle.SW] = wraparound(x+1,y)
                    neighbours[Particle.SE] = wraparound(x+1,y+1)
                self.neighbourhood[x][y] = neighbours
                if obstacle(x-cx, y-cy):
                    if VOID_OBSTACLE:
                        continue
                    self.walls[x][y] = True
                    continue
                if not SMOOTH_FILTER:
                    self.particles[x][y] = grid[x][y]
                    continue
                # Apply a majority filter to produce smooth blobs
                neighbors = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < rows and 0 <= ny < cols:
                            neighbors.append(grid[nx][ny])
                # Add occasional noise to prevent uniform results
                if random.random() < 0.1:
                    self.particles[x][y] = Particle(random.choice(spawn))
                else:
                    self.particles[x][y] = Counter(neighbors).most_common(1)[0][0]

    def collision_step(self) -> None:
        for x, row in enumerate(self.particles):
            for y, cell in enumerate(row):
                next_state = cell
                out_states = Lattice.COLLISION_RULES.get(cell, None)
                if out_states is not None:
                    if isinstance(out_states, list):
                        next_state = Particle(random.choice(out_states))
                    else:
                        next_state = Particle(out_states)
                self.particles[x][y] = next_state

    def transport_step(self) -> None:
        update = [[Particle.EMPTY for _ in row] for row in self.particles]
        def within_bounds(nx: int, ny: int):
            return 0 <= nx < self.rows and 0 <= ny < self.cols and not self.walls[nx][ny]
        for x, line in enumerate(self.particles):
            for y, cell in enumerate(line):
                if self.source_channel:
                    if y == 0:
                        update[x][0] |= Particle(random.choice(self.source_channel))
                    elif y == self.cols-1:
                        continue
                if self.walls[x][y]:
                    continue
                if not cell:
                    continue
                neighbours = self.neighbourhood[x][y]
                for direction in Particle:
                    if direction in cell:
                        nx, ny = neighbours[direction]
                        if within_bounds(nx, ny):  # Free: move 1 lattice unit in that direction
                            update[nx][ny] |= direction
                        else:  # Reflect off boundary/wall
                            update[x][y] |= direction.opposite()
        self.particles = update

    def __str__(self) -> str:
        chars = []
        for x, row in enumerate(self.particles):
            if x % 2 == 1:  # Odd row, offset by half
                chars.append(" ")
            for y, cell in enumerate(row):
                if self.walls[x][y]:
                    chars.append("  ")
                else:
                    chars.append(str(cell))
            chars.append("\n")
        return "".join(chars)


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


def main():
    size = shutil.get_terminal_size()
    ROWS = size.lines-1
    COLS = size.columns // 2 - 1
    CLEAR_LINE = "\x1b[1F\x1b[2K"  # ANSI escape code string
    CLEAR_SCREEN = CLEAR_LINE * ROWS
    spawn = []
    if len(sys.argv) > 1:
        for x in sys.argv[1:]:
            value = int(x)
            if value == 0:
                spawn.extend([0]*len(x))
            else:
                spawn.append(value)
    world = Lattice(ROWS, COLS, spawn, source=SOURCE_CHANNEL)
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
