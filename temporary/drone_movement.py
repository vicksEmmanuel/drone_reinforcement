__author__ = 'Oliver Maskery'


import datetime
import os
import pygame
import random
import math


class Controller(object):

    def update(self, ship):
        pass


class Sensor(object):

    def __init__(self, value, error=0):
        self.value = value
        self.error = error

    def set(self, value):
        self.value = value + random.gauss(0, self.error)

    def update(self, latest_measurement):
        pass

    def get(self):
        return self.value


class DeltaSensor(Sensor):

    def __init__(self, value, error=0):
        Sensor.__init__(self, value, error)
        self.last = value

    def update(self, latest_measurement):
        self.set(latest_measurement - self.last)
        self.last = latest_measurement


image = pygame.image.load(os.path.join("src/assets", "Drone.png"))
image = pygame.transform.scale(image, (50, 50))  # Replace new_width and new_height with your desired values


class Sensors(object):

    def __init__(self, ship, base_error=0):
        self.ship = ship
        self.x_vel = DeltaSensor(ship.pos[0], base_error)
        self.y_vel = DeltaSensor(ship.pos[1], base_error)
        self.rot = DeltaSensor(ship.rot, base_error)

    def update(self):
        self.x_vel.update(self.ship.pos[0])
        self.y_vel.update(self.ship.pos[1])
        self.rot.update(self.ship.rot)


class Ship(object):

    def __init__(self, pos, world, controller, sensor_interface=Sensors, base_error=0):
        self.controller = controller
        self.world = world
        self.pos = pos
        self.rot = -math.pi / 2
        self.l_thrust = 0
        self.r_thrust = 0
        self.vel = [0, 0]
        self.max_thrust = 100
        self.min_thrust = 0
        self.mass = 1E3
        self.arm_length = 15
        self.sensors = sensor_interface(self, base_error)

    def set_thrust(self, left, right):
        self.l_thrust = max(min(left, self.max_thrust), self.min_thrust)
        self.r_thrust = max(min(right, self.max_thrust), self.min_thrust)

    def total_thrust(self):
        return [math.cos(self.rot) * (self.l_thrust + self.r_thrust),
                math.sin(self.rot) * (self.l_thrust + self.r_thrust)]

    def update(self):
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
        self.controller.update(self)

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

        rotated_image = pygame.transform.rotate(image, math.degrees(self.rot))
        rotated_rect = rotated_image.get_rect(center=(x, y))
        dest.blit(rotated_image, rotated_rect.topleft)

        # Rotate the image when moving upwards
        if self.vel[1] < 0:
            rotated_image = pygame.transform.rotate(rotated_image, 180)
            dest.blit(rotated_image, rotated_rect.topleft)
        self.mask = pygame.mask.from_surface(rotated_image)



class Ground(object):

    def __init__(self):
        self.width = 600
        self.height = 800

    def check(self, pos):
        print(pos)
        return pos[0] <= 0 or pos[1] >= self.width or pos[1] <= 0 or pos[0] >= self.height

    def get_height(self, pos):
        return max(self.width - pos[1], -1)


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

    def update(self, ship):
        self.ship = ship

        target_delta = 2
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.desired_x -= target_delta
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.desired_x += target_delta
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.desired_height += target_delta
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.desired_height -= target_delta

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

    def draw(self, dest):
        x, y = int(self.ship.pos[0]), int(self.ship.pos[1])
        tx = int(dest.get_size()[0] / 2 + self.desired_x)
        ty = int(self.ship.world.width - self.desired_height)
        r = 20
        colour = (200, 255, 200)

        pygame.draw.line(dest, colour, (tx-r, ty), (tx+r, ty))
        pygame.draw.line(dest, colour, (tx, ty-r), (tx, ty+r))


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    running = True

    desired_lps = 100.0
    desired_fps = 60.0

    think_period = datetime.timedelta(seconds=1.0 / desired_lps)
    next_think = datetime.datetime.now()
    draw_period = datetime.timedelta(seconds=1.0 / desired_fps)
    next_draw = datetime.datetime.now()

    gravity = 9.81

    controller = AutoController()
    world = Ground()
    ship = Ship([world.height, world.width], world, controller, base_error=0.01)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                controller.desired_height = world.width - event.pos[1]
                controller.desired_x = event.pos[0] - (screen.get_size()[0] / 2)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    controller.estimated_x = ship.pos[0] - (screen.get_size()[0] / 2)
                    controller.desired_x = world.width - ship.pos[1]
                    
        pygame.display.update()
            

        now = datetime.datetime.now()

        if now >= next_think:
            next_think += think_period

            ship.vel[1] += 9.91 / desired_lps
            ship.update()

        if now >= next_draw:
            next_draw += draw_period

            screen.fill((200,200,255))
            ship.draw(screen)
            pygame.display.flip()
        


    pygame.quit()


if __name__ == "__main__":
    main()