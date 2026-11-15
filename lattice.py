from abc import ABC, abstractmethod
from collections import Counter
from enum import IntFlag
from typing import ClassVar
import random


def obstacle(dx: int, dy: int, shape: str, radius: int):
    match shape:
        case "circle":  # Euclidian distance
            return abs(dx)**2 + abs(dy)**2 <= radius**2
        case "square":  # Chebyshev distance
            return max(abs(dx), abs(dy)) <= radius
        case "diamond":  # Manhattan distance
            return abs(dx) + abs(dy) <= radius
        case _:
            return False


# Lattice is an abstract class: collision rules and particle velocities must be specified
class Lattice(ABC):
    PARTICLE: ClassVar[type[IntFlag]]
    EMPTY: ClassVar[IntFlag]
    COLLISION_RULES = {}

    def __init__(self, rows: int, cols: int, spawn: list[int], source: list[int], shape: str, radius: int, void: bool = False, smooth: bool = False, wraprows: bool = False, wrapcols: bool = False):
        if not spawn:
            spawn = [0]
        grid = [[self.PARTICLE(random.choice(spawn)) for _ in range(cols)] for _ in range(rows)]
        cx, cy = rows//2, cols//2
        self.rows, self.cols = rows, cols
        self.source_channel = source
        self.particles = [[self.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.walls = [[False for _ in range(cols)] for _ in range(rows)]
        self.neighbourhood = [[dict() for _ in range(cols)] for _ in range(rows)]
        self.wraprows = wraprows
        self.wrapcols = wrapcols
        def wraparound(x: int, y: int):
            return ((x+rows) % rows if self.wraprows else x, (y+cols) % cols if self.wrapcols else y)
        for x in range(rows):
            for y in range(cols):
                if obstacle(x-cx, y-cy, shape, radius):
                    if void:
                        continue
                    self.walls[x][y] = True
                    continue
                if not smooth:
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
                    self.particles[x][y] = self.PARTICLE(random.choice(spawn))
                else:
                    self.particles[x][y] = Counter(neighbors).most_common(1)[0][0]

    @abstractmethod
    def build_neighbourhood(self, x: int, y: int, wraprows: bool, wrapcols: bool):
        raise NotImplementedError

    @abstractmethod
    def opposite(self, direction: IntFlag) -> IntFlag:
        raise NotImplementedError
    
    def collision_step(self) -> None:
        for x, row in enumerate(self.particles):
            for y, cell in enumerate(row):
                next_state = cell
                out_states = self.COLLISION_RULES.get(cell, None)
                if out_states is None:
                    continue
                if isinstance(out_states, list):
                    next_state = self.PARTICLE(random.choice(out_states))
                else:
                    next_state = self.PARTICLE(out_states)
                self.particles[x][y] = next_state

    def transport_step(self) -> None:
        update = [[self.EMPTY for _ in row] for row in self.particles]
        def within_bounds(nx: int, ny: int):
            return 0 <= nx < self.rows and 0 <= ny < self.cols and not self.walls[nx][ny]
        for x, line in enumerate(self.particles):
            for y, cell in enumerate(line):
                if self.source_channel:
                    if y == 0:
                        update[x][0] |= self.PARTICLE(random.choice(self.source_channel))
                    elif y == self.cols-1:
                        continue
                if self.walls[x][y]:
                    continue
                if not cell:
                    continue
                neighbours = self.neighbourhood[x][y]
                for direction in self.PARTICLE:
                    if direction in cell:
                        nx, ny = neighbours[direction]
                        if within_bounds(nx, ny):  # Free: move 1 lattice unit in that direction
                            update[nx][ny] |= direction
                        else:  # Reflect off boundary/wall
                            update[x][y] |= self.opposite(direction)
        self.particles = update

    @abstractmethod
    def row_prefix(self, row: int) -> str:
        #if x % 2 == 1:  # Odd row, offset by half
        #    chars.append(" ")
        return ""

    def __str__(self) -> str:
        chars = []
        for x, row in enumerate(self.particles):
            chars.append(self.row_prefix(x))
            for y, cell in enumerate(row):
                if self.walls[x][y]:
                    chars.append("  ")
                else:
                    chars.append(str(cell))
            chars.append("\n")
        return "".join(chars)
