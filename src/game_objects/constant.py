from enum import Enum


SCREEN_WIDTH = 400
SCREEN_HEIGHT = 750
BACKGROUND_SCROLL_SPEED = 0.6


class Direction(Enum):
    None_ = 0
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4
    SHARP_DOWN = 5
    STEADY = 6

class DirectionValue(Enum):
    None_ = [0,0,0,0,0,0]
    LEFT = [1,0,0,0,0,0]
    RIGHT = [0,1,0,0,0,0]
    UP = [0,0,1,0,0,0]
    DOWN = [0,0,0,1,0,0]
    SHARP_DOWN = [0,0,0,0,1,0]
    STEADY = [0,0,0,0,0,1]



# Model config
OUTPUT_NUMBER = 6
INPUT_NUMBER = 26
LAYERS = 400

DRONE_HEALTH = 10