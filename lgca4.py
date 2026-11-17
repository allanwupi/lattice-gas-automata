#!/usr/bin/env python3
'''
Hardy-Pomeau-Pazzis (HPP) model
Square lattice: 4 velocities
'''
from enum import IntFlag, auto
from lattice import Lattice, simulate
from graphics import ColourScheme, GraphicStyle, PARTICLE_DENSITY
import sys, shutil


# Simulation configuration
TARGET_FRAME_RATE = 20
MAX_SIMULATION_TICKS = 1200
SMOOTH_FILTER = True
OBSTACLE_RADIUS = 30
OBSTACLE_SHAPE = "circle"
VOID_OBSTACLE = True
SMOOTH_FILTER = True

# Customise appearance
COLOUR_SCHEME = ColourScheme.BLUE
GRAPHIC_STYLE = GraphicStyle.BLOCK4


class Particle(IntFlag):
    EMPTY = 0
    N = auto()  # 1
    S = auto()  # 2
    E = auto()  # 4
    W = auto()  # 8

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


class HHPLattice(Lattice):
    PARTICLE = Particle
    EMPTY = Particle.EMPTY
    # Collision rules: north-south, east-west only
    COLLISION_RULES = {
        0b1100: 0b0011,
        0b0011: 0b1100
    }

    def opposite(self, direction: IntFlag) -> IntFlag:
        match direction:
            case Particle.N: return Particle.S
            case Particle.S: return Particle.N
            case Particle.E: return Particle.W
            case Particle.W: return Particle.E
        return Particle.EMPTY 

    def build_neighbourhood(self, x: int, y: int, wraprows: bool, wrapcols: bool) -> None:
        def wraparound(x: int, y: int):
            return (
                (x+self.rows) % self.rows if self.wraprows else x,
                (y+self.cols) % self.cols if self.wrapcols else y
            )
        self.neighbourhood[x][y] = {
            Particle.N: wraparound(x-1,y),
            Particle.S: wraparound(x+1,y),
            Particle.W: wraparound(x,y-1),
            Particle.E: wraparound(x,y+1)
        }

    def row_prefix(self, row: int) -> str:
        return ""


if __name__ == "__main__":
    size = shutil.get_terminal_size()
    ROWS = size.lines-1
    COLS = size.columns // 2
    source = []
    spawn = []
    if len(sys.argv) > 1:
        for x in sys.argv[1:]:
            if ',' in x:
                source.extend([int(s) for s in x.split(',') if s])
                continue
    WORLD = HHPLattice(
        ROWS, COLS,
        spawn=spawn,
        source=source,
        shape=OBSTACLE_SHAPE,
        radius=OBSTACLE_RADIUS,
        void=VOID_OBSTACLE,
        smooth=SMOOTH_FILTER
    )
    simulate(
        rows=ROWS,
        cols=COLS,
        world=WORLD,
        frame_rate=TARGET_FRAME_RATE,
        simulation_ticks=MAX_SIMULATION_TICKS,
        colour=COLOUR_SCHEME
    )
