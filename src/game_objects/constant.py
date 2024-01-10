import os
import datetime
from enum import Enum


SCREEN_WIDTH = 400
SCREEN_HEIGHT = 750
BACKGROUND_SCROLL_SPEED = 0.6

MODEL_URL = 'https://github.com/vicksEmmanuel/drone_reinforcement/blob/main/model/model.pth'

class Direction(Enum):
    None_ = 0
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4
    SHARP_DOWN = 5
    STEADY = 6

class DirectionValue(Enum):
    None_ = [0,0,0,0]
    LEFT = [1,0,0,0]
    RIGHT = [0,1,0,0]
    UP = [0,0,1,0] 
    DOWN = [0,0,0,1]



# Model config
OUTPUT_NUMBER = 4
INPUT_NUMBER = 29
CONV_INPUT_NUMBER = 4
FRAME_STACK_SIZE=4
CONV_OUTPUT_NUMBER = 4
LAYERS = 400

DRONE_HEALTH = 100


# DRONE CONFIG
DESIRED_LPS=100.0
DESIRED_FPS = 60.0

THINK_PERIOD = datetime.timedelta(seconds=1.0 / DESIRED_LPS)
NEXT_THINK = datetime.datetime.now()
DRAW_PERIOD = datetime.timedelta(seconds=1.0 / DESIRED_FPS)
NEXT_DRAW = datetime.datetime.now()


SURVIVAL_REWARD = 200
COLLISION_PENALTY = -100
SAFE_ALTITUDE_REWARD = 10
GROUND_PROXIMITY_PENALTY = -50  # This can be scaled based on proximity
EDGE_PROXIMITY_PENALTY = -10    # This can be scaled based on proximity
OPTIMAL_ALTITUDE = 100 


FILE_PATH = os.path.join(os.path.dirname(__file__), "assets")