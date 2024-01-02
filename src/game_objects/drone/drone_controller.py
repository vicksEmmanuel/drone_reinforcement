import numpy as np
import pygame;
import math

from game_objects.constant import SCREEN_WIDTH, Direction, DirectionValue


class Controller(object):
    def update(self, ship):
        pass


class PID(object):

    def __init__(self, p, i, d):
        self.params = (p, i, d)
        self.last = 0
        self.integral = 0
        self.output = 0

    def update(self, error):
        p, i, d = self.params
        self.integral += error
        delta = error - self.last
        self.last = error
        self.output = error * p + self.integral * i + delta * d
        return self.output

    def update_auto(self, actual, desired=0):
        error = desired - actual
        return self.update(error)


class AutoController(Controller):

    def __init__(self):
        Controller.__init__(self)
        self.desired_height = 100
        self.desired_x = -100

        self.estimated_x = 0
        self.height_estimate = 0
        self.rotation_estimate = -math.pi / 2

        self.ship = None

        self.height_pid = PID(0.05, 0, 3.5)
        self.x_pid = PID(0.05, 0, 2)

        self.yvel_pid = PID(10000, 0, 0)
        self.xvel_pid = PID(0.2, 0, 0)
        self.rot_pid = PID(50, 0, 0)

    def update(self, ship, action):
        self.ship = ship

        # Put move here
        self.move(ship, action)
        

        sensors = ship.sensors
        self.height_estimate -= sensors.y_vel.get()
        self.rotation_estimate += sensors.rot.get()
        self.estimated_x += sensors.x_vel.get()

        x_error = self.estimated_x - self.desired_x
        desired_xvel = -self.x_pid.update(x_error)

        height_error = self.height_estimate - self.desired_height
        desired_yvel = self.height_pid.update(height_error)

        yvel_error = sensors.y_vel.get() - desired_yvel
        base_thrust = self.yvel_pid.update(yvel_error)
        thrust_min = ship.max_thrust * 0.1
        thrust_max = ship.max_thrust * 0.8
        base_thrust = min(max(base_thrust, thrust_min), thrust_max)

        xvel_error = sensors.x_vel.get() - desired_xvel
        desired_rot = (-math.pi / 2) - self.xvel_pid.update(xvel_error)
        rot_min = (-math.pi / 2) - (math.pi / 4)
        rot_max = (-math.pi / 2) + (math.pi / 4)
        desired_rot = min(max(desired_rot, rot_min), rot_max)

        rot_error = self.rotation_estimate - desired_rot
        left_thrust = -self.rot_pid.update(rot_error)
        right_thrust = -left_thrust

        #print "desired rot:", desired_rot, "actual:", ship.rot
        #print "rot error:", rot_error

        l = base_thrust + left_thrust
        r = base_thrust + right_thrust

        #print "estimated height:", self.height_estimate, "actual height:", ship.world.get_height(ship.pos)
        #print "height error:", height_error, "yvel error:", yvel_error, "setting thrust:", l, r#
        ship.set_thrust(l, r)

    def move(self, ship, action):
        target_delta = 2

        ship.direction  = self.get_direction(action)

        print(ship.direction)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_a] or keys[pygame.K_LEFT] or ship.direction == Direction.LEFT:
            self.desired_x -= target_delta
        if keys[pygame.K_d] or keys[pygame.K_RIGHT] or ship.direction == Direction.RIGHT:
            self.desired_x += target_delta
        if keys[pygame.K_w] or keys[pygame.K_UP] or ship.direction == Direction.UP:
            self.desired_height += target_delta
        if keys[pygame.K_s] or keys[pygame.K_DOWN] or ship.direction == Direction.DOWN:
            self.desired_height -= target_delta
        if keys[pygame.K_SPACE] or ship.direction == Direction.STEADY:
            self.estimated_x = ship.pos[0] - (SCREEN_WIDTH / 2)
            self.desired_x = ship.world.width - ship.pos[1]
        if ship.direction == Direction.SHARP_DOWN:
            self.desired_height = ship.world.width - event.pos[1]
            self.desired_x = event.pos[0] - (SCREEN_WIDTH / 2)

        
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                    self.desired_height = ship.world.width - event.pos[1]
                    self.desired_x = event.pos[0] - (SCREEN_WIDTH / 2)

    def get_direction(self, action):
        if np.array_equal(action, DirectionValue.RIGHT):
            return Direction.RIGHT
        elif np.array_equal(action, DirectionValue.DOWN):
            return Direction.DOWN
        elif np.array_equal(action, DirectionValue.LEFT):
            return Direction.LEFT
        elif np.array_equal(action, DirectionValue.UP):
            return Direction.UP
        # elif np.array_equal(action, DirectionValue.SHARP_DOWN):
        #     return Direction.SHARP_DOWN
        # elif np.array_equal(action, DirectionValue.STEADY):
        #     return Direction.STEADY

        

    def draw(self, dest):
        x, y = int(self.ship.pos[0]), int(self.ship.pos[1])
        tx = int(dest.get_size()[0] / 2 + self.desired_x)
        ty = int(self.ship.world.width - self.desired_height)
        r = 20
        colour = (200, 255, 200)

        pygame.draw.line(dest, colour, (tx-r, ty), (tx+r, ty))
        pygame.draw.line(dest, colour, (tx, ty-r), (tx, ty+r))
