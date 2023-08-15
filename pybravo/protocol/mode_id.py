from enum import Enum


class ModeID(Enum):
    """The different modes of the Bravo Arm."""

    STANDBY = 0
    DISABLE = 1
    POSITION = 2
    VELOCITY = 3
    CURRENT = 4
