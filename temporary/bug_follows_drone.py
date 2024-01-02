import os
import random
import pygame
import math
from game_objects.constant import SCREEN_HEIGHT, SCREEN_WIDTH
from game_objects.drone import DRONE

ENEMY_BUG = pygame.image.load(os.path.join("assets", "Jet.png"))
ENEMY_BUG = pygame.transform.scale(ENEMY_BUG, (30, 30))

class Bug:
    def __init__(self, health=1000, ship_position=None, index=0, total_bugs=1):
        self.health = health
        self.original_image = ENEMY_BUG
        self.ship_image = self.original_image
        self.mask = pygame.mask.from_surface(self.ship_image)
        self.pos = self.get_arc_start_position(index, total_bugs)
        self.ship_position = ship_position
        self.constant_speed = 1.0  # Constant speed for all bugs
        self.velocity = [0, self.constant_speed]  # Start moving down
        self.index = index
        self.total_bugs = total_bugs

    def get_arc_start_position(self, index, total_bugs):
        # Position the bugs in an arc using their index and the total number of bugs
        arc_width = SCREEN_WIDTH * 0.5  # Width of the arc
        arc_height = SCREEN_HEIGHT * 0.1  # Height of the arc
        x_spacing = arc_width / max(1, total_bugs - 1)
        x_pos = (SCREEN_WIDTH - arc_width) / 2 + index * x_spacing
        y_pos = -30  # Start off-screen
        return [x_pos, y_pos]

    def calculate_angle_to_ship(self):
        # Calculate the angle towards the drone
        dx = self.ship_position[0] - self.pos[0]
        dy = self.ship_position[1] - self.pos[1]
        return math.degrees(math.atan2(dy, dx))

    def move(self):
        # Move towards the drone
        if self.ship_position:
            self.angle = self.calculate_angle_to_ship()
            self.velocity[0] = self.constant_speed * math.cos(math.radians(self.angle))
            self.velocity[1] = self.constant_speed * math.sin(math.radians(self.angle))

        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

    def rotate_image(self):
        # Rotate the bug's image based on the velocity direction
        rotation_angle = math.degrees(math.atan2(self.velocity[1], self.velocity[0])) - 90
        self.ship_image = pygame.transform.rotate(self.original_image, rotation_angle)
        self.mask = pygame.mask.from_surface(self.ship_image)

    def draw(self, screen):
        # Draw the rotated image of the bug
        self.rotate_image()
        rotated_rect = self.ship_image.get_rect(center=self.pos)
        screen.blit(self.ship_image, rotated_rect.topleft)

def update_bugs(bugs, screen, ship_position, wave_length=5):
    # Function to update and draw bugs
    if len(bugs) < wave_length:
        for i in range(wave_length - len(bugs)):
            index = len(bugs) + i
            new_bug = Bug(ship_position=ship_position, index=index, total_bugs=wave_length)
            bugs.append(new_bug)

    for bug in list(bugs):
        if bug.pos[1] > SCREEN_HEIGHT:
            bugs.remove(bug)
            continue
        bug.move()
        bug.draw(screen)