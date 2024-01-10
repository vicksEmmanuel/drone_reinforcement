
import pygame;
import os;
import datetime
import pygame
import random
import math

from game_objects.constant import DESIRED_LPS, DRAW_PERIOD, EDGE_PROXIMITY_PENALTY, FILE_PATH, NEXT_DRAW, NEXT_THINK, SAFE_ALTITUDE_REWARD, SCREEN_HEIGHT, SCREEN_WIDTH, DRONE_HEALTH, THINK_PERIOD, Direction
from game_objects.drone.drone_controller import AutoController, ManualController
from game_objects.drone.drone_sensors import Sensors

file_path = os.path.join(FILE_PATH, "Drone.png")
print("Loading image from:", file_path)

DRONE = pygame.image.load(file_path)
DRONE = pygame.transform.scale(DRONE, (40, 40))


desired_lps = 100.0
desired_fps = 60.0

think_period = THINK_PERIOD
next_think = NEXT_THINK
draw_period = DRAW_PERIOD
next_draw = NEXT_DRAW

gravity = 9.91

class Ship(object):

    def __init__(self, pos, world, controller, sensor_interface=Sensors, base_error=0, health = DRONE_HEALTH):
        self.controller = controller
        self.next_draw  = next_draw
        self.world = world
        self.pos = pos
        self.rot = -math.pi / 2
        self.l_thrust = 0
        self.r_thrust = 0
        self.vel = [0, 0]
        self.max_thrust = 100
        self.min_thrust = 0
        self.health = health
        self.mass = 1E3
        self.arm_length = 15
        self.direction = Direction.None_
        self.sensors = sensor_interface(self, base_error)

    def set_thrust(self, left, right):
        self.l_thrust = max(min(left, self.max_thrust), self.min_thrust)
        self.r_thrust = max(min(right, self.max_thrust), self.min_thrust)

    def total_thrust(self):
        return [math.cos(self.rot) * (self.l_thrust + self.r_thrust),
                math.sin(self.rot) * (self.l_thrust + self.r_thrust)]

    def update(self, reward, action):

        global new_reward
        new_reward = reward

        new_reward += self.rewarding()

        
        self.accelerate(self.total_thrust())
        nx, ny = self.pos[0] + self.vel[0], self.pos[1] + self.vel[1]

        if not self.world.check((nx, ny)):
            self.pos[0] = nx
            self.pos[1] = ny
        else:
            self.vel[0] *= 0.8
            self.vel[1] *= -0.5

        net_rot_thrust = (self.l_thrust - self.r_thrust) * 0.001
        ground_rot_thrust = 0.01
        
        if self.world.check(self.r_thruster()):
            net_rot_thrust -= ground_rot_thrust

        if self.world.check(self.l_thruster()):
            net_rot_thrust += ground_rot_thrust

        self.rot += net_rot_thrust

        # Update sensor and controller
        self.sensors.update()
        self.controller.update(self, action)


        return new_reward

    def rewarding(self):
        
        # Define safe distance thresholds from each edge
        safe_distance = SCREEN_HEIGHT * 0.10  # 10% of screen height for top and bottom
        safe_distance_x = SCREEN_WIDTH * 0.10  # 10% of screen width for left and right

        # Calculate distances from each edge
        distance_from_top = self.pos[1]
        distance_from_bottom = SCREEN_HEIGHT - self.pos[1]
        distance_from_left = self.pos[0]
        distance_from_right = SCREEN_WIDTH - self.pos[0]

        # Check if the drone is within the safe distance from any edge
        # too_close = any([
        #     distance_from_top < safe_distance,
        #     distance_from_bottom < safe_distance,
        #     distance_from_left < safe_distance_x,
        #     distance_from_right < safe_distance_x
        # ])

        # Adjust the reward based on proximity to edges
        # if too_close:
        #     new_reward -= 10  # Penalize if too close to any edge
        # else:
        #     # Increase reward if within safe bounds
        #     new_reward += 10  # Adjust this value as needed

        # Calculate the proximity penalty
        proximity_penalty =  self.calculate_proximity_penalty_reward(
            distance_from_left,distance_from_right,
            distance_from_top,distance_from_bottom , 
            safe_distance_x, safe_distance
        )
        
        return proximity_penalty

    def r_thruster(self):
        cx, cy = self.pos
        cx += math.cos(self.rot + (math.pi / 2)) * self.arm_length
        cy += math.sin(self.rot + (math.pi / 2)) * self.arm_length
        return (cx, cy)

    def l_thruster(self):
        cx, cy = self.pos
        cx += math.cos(self.rot - (math.pi / 2)) * self.arm_length
        cy += math.sin(self.rot - (math.pi / 2)) * self.arm_length
        return (cx, cy)

    def accelerate(self, force):
        self.vel[0] += force[0] / self.mass
        self.vel[1] += force[1] / self.mass
        return self.vel

    def draw(self, dest):
        x = int(self.pos[0])
        y = int(self.pos[1])
        lx, ly = self.l_thruster()
        rx, ry = self.r_thruster()
        lx, ly = int(lx), int(ly)
        rx, ry = int(rx), int(ry)

        rotated_image = pygame.transform.rotate(DRONE, math.degrees(self.rot))
        rotated_rect = rotated_image.get_rect(center=(x, y))
        dest.blit(rotated_image, rotated_rect.topleft)

        # Rotate the image when moving upwards
        if self.vel[1] < 0:
            rotated_image = pygame.transform.rotate(rotated_image, 180)
            dest.blit(rotated_image, rotated_rect.topleft)
        self.mask = pygame.mask.from_surface(rotated_image)
        
    def reset_drone(self):
        self.pos = [self.world.width / 2, self.world.height /2]
        self.vel = [0, 0]  # Reset velocity
        self.rot = -math.pi / 2  # Reset rotation
        self.l_thrust = 0
        self.r_thrust = 0
        self.health = DRONE_HEALTH  # Reset health
        self.direction = Direction.None_  # Reset direction to None
        self.max_thrust = 100
        self.min_thrust = 0
        self.mass = 1E3
        self.arm_length = 15
        self.sensors = Sensors(self, 0.01)

        self.controller.reset()

    def calculate_proximity_penalty_reward(
        self,
        distance_from_left, distance_from_right,
        distance_from_top, distance_from_bottom,
        safe_distance_x, safe_distance_y
    ):
        penalty_reward = 0
        
        # Check distances from all edges and penalize for being too close
        if distance_from_left < safe_distance_x:
            penalty_reward = (EDGE_PROXIMITY_PENALTY * (1 - (distance_from_left / safe_distance_x)))
        if distance_from_right < safe_distance_x:
            penalty_reward = (EDGE_PROXIMITY_PENALTY * (1 - (distance_from_right / safe_distance_x)))
        if distance_from_top < safe_distance_y:
            penalty_reward = (EDGE_PROXIMITY_PENALTY * (1 - (distance_from_top / safe_distance_y)))
        if distance_from_bottom < safe_distance_y:
            penalty_reward = (EDGE_PROXIMITY_PENALTY * (1 - (distance_from_bottom / safe_distance_y)))

        # Check if the drone is in the central safe zone
        central_zone_x = SCREEN_WIDTH * 0.2  # 20% of the screen width from each side
        central_zone_y = SCREEN_HEIGHT * 0.2  # 20% of the screen height from top and bottom
        in_safe_zone_x = central_zone_x < distance_from_left < (SCREEN_WIDTH - central_zone_x)
        in_safe_zone_y = central_zone_y < distance_from_top < (SCREEN_HEIGHT - central_zone_y)

        # Reward for staying within the safe central zone
        if in_safe_zone_x and in_safe_zone_y:
            penalty_reward += SAFE_ALTITUDE_REWARD   # Reward value for maintaining position in the safe zone

        return penalty_reward

       


class Ground(object):
    def __init__(self):
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

    def check(self, pos):
        return  (
            pos[0] < 5 or 
            pos[1] > (self.height + 5) or 
            pos[1] < 5 or 
            pos[0] > (self.width + 5)
        )

    def get_height(self, pos):
        return self.height - pos[1]


def create_drone():
    controller = AutoController()
    world = Ground()
    ship = Ship([world.width/2, world.height/2], world, controller, sensor_interface=Sensors, base_error=0.01)
    return ship, controller, world, [next_draw, next_think, think_period, desired_lps, draw_period]


def update_drone(ship, screen, reward, action, next_draw_val, next_think_val, think_period_val, desired_lps_val, draw_period_val):
    global new_reward
    new_reward = reward

    now = datetime.datetime.now()
    if now >= next_think_val:
        next_think_val += think_period_val
        ship.vel[1] += gravity / desired_lps_val
        new_reward += ship.update(new_reward,action)

    # if now >= next_draw_val:
    #     next_draw_val += draw_period_val

    #     ship.draw(screen)
        # pygame.display.flip()

    return new_reward