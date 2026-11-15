#!/usr/bin/env python3
'''
Hardy-Pomeau-Pazzis (HPP) model
Square lattice: 4 velocities
'''
from enum import IntFlag, auto
from collections import Counter
from graphics import ColourScheme, GraphicStyle
import sys, time, shutil, random


# Simulation configuration
DELAY_SECONDS = 0.05
MAX_SIMULATION_TICKS = 1200
SMOOTH_FILTER = True
OBSTACLE_RADIUS = 12
OBSTACLE_SHAPE = "none"
VOID_OBSTACLE = False
SMOOTH_FILTER = True
SOURCE_CHANNEL = []

# Customise appearance
COLOUR_SCHEME = ColourScheme.BLUE
GRAPHIC_STYLE = GraphicStyle.BLOCK4


PARTICLE_DENSITY = {
    GraphicStyle.ARROW4: ["  ", "..", "++", "%%", "@@"],
    GraphicStyle.BLOCK4: ["  ", "░░", "▒▒", "▓▓", "██"]
}


class Particle(IntFlag):
    EMPTY = 0
    N = auto()  # 1
    S = auto()  # 2
    E = auto()  # 4
    W = auto()  # 8

    def opposite(self) -> Particle:
        match self:
            case Particle.N: return Particle.S
            case Particle.S: return Particle.N
            case Particle.E: return Particle.W
            case Particle.W: return Particle.E
        return Particle.EMPTY 

    def __str__(self) -> str:
        particle_count = len(self)
        if GRAPHIC_STYLE == GraphicStyle.ARROW4:
            if particle_count >= 2:
                if self == (Particle.E | Particle.W): return "→←"
                if self == (Particle.N | Particle.S): return "↑↓"
            if particle_count >= 1:
                if self == Particle.N: return "↑ "
                if self == Particle.S: return "↓ "
                if self == Particle.E: return "→ "
                if self == Particle.W: return " ←"
        return PARTICLE_DENSITY[GRAPHIC_STYLE][particle_count]


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


class Lattice:
    # Head-on collision between two particles only (N+S, E+W)
    COLLISION_RULES = {
       0b1100: 0b0011,
       0b0011: 0b1100
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
                    Particle.N: wraparound(x-1,y),
                    Particle.S: wraparound(x+1,y),
                    Particle.W: wraparound(x,y-1),
                    Particle.E: wraparound(x,y+1)
                }
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
    
    def __str__(self) -> str:
        chars = []
        for x, row in enumerate(self.particles):
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
    world = Lattice(ROWS, COLS, spawn=spawn, source=SOURCE_CHANNEL)
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
