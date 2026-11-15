from enum import StrEnum, auto

class ColourScheme(StrEnum):
    BLACK = "\033[40;37m"
    PURPLE = "\033[40;35m"
    BLUE = "\x1b[1;44;97m"
    DEEPBLUE = "\x1b[1;44;94m"
    RED = "\x1b[1;41;30m"
    WHITE = "\x1b[1;107;30m"
    RESET = "\x1b[0m"

class GraphicStyle(StrEnum):
    ARROW4 = auto()
    BLOCK4 = auto()
    DOT6 = auto()
    ARROW6 = auto()
    BLOCK6 = auto()
