# Frisch–Hasslacher–Pomeau (FHP) model
# Hexagonal lattice: 7 velocities (6 directions + stationary)

from enum import Flag, auto
# Note that len(flag_variable) returns the number of active bits

class FHPChannel(Flag):
    EMPTY = 0
    REST = auto()
    E = auto()
    NE = auto()
    NW = auto()
    W = auto()
    SW = auto()
    SE = auto()

    def __str__(self) -> str:
        density = len(self)
        if density >= 7: return '@'
        if density >= 6: return '#'
        if density >= 5: return '*'
        if density >= 4: return '+'
        if density >= 3: return '='
        if density >= 2: return ':'
        if density >= 1: return '.'
        return " "

"""
ASCII gray-scale
. 1
: 2
= 3
+ 4
* 5
# 6
@ 7

.:=+*#@
.:*@
"""
