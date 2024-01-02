
import pygame;
import os;
import datetime
import pygame
import random
import math

from game_objects.constant import SCREEN_HEIGHT, SCREEN_WIDTH, Direction
from game_objects.drone.drone_controller import AutoController
from game_objects.drone.drone_sensors import Sensors

DRONE = pygame.image.load(os.path.join("assets", "Drone.png"))
DRONE = pygame.transform.scale(DRONE, (40, 40))

desired_lps = 100.0
desired_fps = 60.0

think_period = datetime.timedelta(seconds=1.0 / desired_lps)
next_think = datetime.datetime.now()
draw_period = datetime.timedelta(seconds=1.0 / desired_fps)
next_draw = datetime.datetime.now()

gravity = 19.81

class Ship(object):

    def __init__(self, pos, world, controller, sensor_interface=Sensors, base_error=0, health = 1000):
        self.controller = controller
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

    def update(self, action):
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

        self.sensors.update()
        self.controller.update(self, action)

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
        self.pos = [self.world.width/2, self.world.height - 50]
        self.rot = -math.pi / 2
        self.l_thrust = 0
        self.r_thrust = 0
        self.vel = [0, 0]
        self.max_thrust = 100
        self.min_thrust = 0
        self.health = 1000
        self.mass = 1E3
        self.arm_length = 15


class Ground(object):
    def __init__(self):
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

    def check(self, pos):
        return (
            pos[0] < 0 or 
            pos[1] > self.height or 
            pos[1] < 0 or 
            pos[0] > self.height
        )

    def get_height(self, pos):
        return max(self.width - pos[1], -1)


def create_drone():
    controller = AutoController()
    world = Ground()
    ship = Ship([world.width/2, world.height - 50], world, controller, base_error=0.01)
    return ship, controller, world, [next_draw, next_think, think_period, desired_lps, draw_period]


def update_drone(ship, screen, action, next_draw_val, next_think_val, think_period_val, desired_lps_val, draw_period_val):
    now = datetime.datetime.now()

    if now >= next_think_val:
        next_think_val += think_period_val

        ship.vel[1] += 9.91 / desired_lps_val
        ship.update(action)

    if now >= next_draw_val:
        next_draw_val += draw_period_val

        ship.draw(screen)
        # pygame.display.flip()