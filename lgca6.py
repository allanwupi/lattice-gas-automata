#!/usr/bin/env python3
'''
Frisch-Hasslacher-Pomeau (FHP) model
Hexagonal lattice: 7 velocities (6 directions + stationary)
'''
from enum import IntFlag, auto
from lattice import Lattice, simulate
from graphics import ColourScheme, GraphicStyle
import sys, shutil


# Simulation configuration
TARGET_FRAME_RATE = 15
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


class FHPLattice(Lattice):
    PARTICLE = Particle
    EMPTY = Particle.EMPTY
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

    def opposite(self, direction: IntFlag) -> IntFlag:
        match direction:
            case Particle.SE: return Particle.NW
            case Particle.SW: return Particle.NE
            case Particle.W: return Particle.E
            case Particle.NW: return Particle.SE
            case Particle.NE: return Particle.SW
            case Particle.E: return Particle.W
        return Particle.EMPTY 

    def build_neighbourhood(self, x: int, y: int, wraprows: bool, wrapcols: bool) -> None:
        def wraparound(x: int, y: int):
            return (
                (x+self.rows) % self.rows if self.wraprows else x,
                (y+self.cols) % self.cols if self.wrapcols else y
            )
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

    def row_prefix(self, row: int) -> str:
        if row % 2 == 1:  # Odd row, offset by half
            return " "
        return ""


if __name__ == "__main__":
    size = shutil.get_terminal_size()
    ROWS = size.lines-1
    COLS = size.columns // 2
    spawn = [0,8,8,8]
    if len(sys.argv) > 1:
        spawn = []
        for x in sys.argv[1:]:
            value = int(x)
            if value == 0:
                spawn.extend([0]*len(x))
            else:
                spawn.append(value)
    WORLD = FHPLattice(
        ROWS, COLS,
        spawn=spawn,
        source=SOURCE_CHANNEL,
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
