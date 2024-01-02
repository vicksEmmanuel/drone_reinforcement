import os
import random
import pygame
from game_objects.constant import SCREEN_HEIGHT, SCREEN_WIDTH

ENEMY_BUG = pygame.image.load(os.path.join("assets", "Bug.png"))
ENEMY_BUG = pygame.transform.scale(ENEMY_BUG, (50, 50))

class Bug:
    def __init__(self, health=1000):
        self.health = health
        self.original_image = ENEMY_BUG
        self.ship_image = self.original_image
        self.mask = pygame.mask.from_surface(self.ship_image)
        self.pos, self.initial_direction = self.get_random_start_position()
        self.direction = self.initial_direction
        self.turning = False
        self.turn_counter = 0
        self.has_entered_screen = False

    def get_random_start_position(self):
        # Decide the starting edge
        edge = random.choice(["horizontal", "vertical"])

        if edge == "horizontal":
            x_pos = random.choice([-50, SCREEN_WIDTH + 50])
            y_pos = random.randint(0, SCREEN_HEIGHT)
            direction = "right" if x_pos < 0 else "left"
        else:
            x_pos = random.randint(0, SCREEN_WIDTH)
            y_pos = random.choice([-50, SCREEN_HEIGHT + 50])
            direction = "bottom" if y_pos < 0 else "top"

        return [x_pos, y_pos], direction

    def check_screen_entry(self):
        if not self.has_entered_screen:
            if 0 <= self.pos[0] <= SCREEN_WIDTH and 0 <= self.pos[1] <= SCREEN_HEIGHT:
                self.has_entered_screen = True
                self.direction = random.choice(["top", "bottom", "left", "right"])  # Random new direction

    def move(self, vel):
        if not self.has_entered_screen:
            # Move in the initial direction until the bug enters the screen
            if self.initial_direction == "top":
                self.pos[1] -= vel
                self.rotate_image(0)
            elif self.initial_direction == "bottom":
                self.pos[1] += vel
                self.rotate_image(180)
            elif self.initial_direction == "left":
                self.pos[0] -= vel
                self.rotate_image(90)
            elif self.initial_direction == "right":
                self.pos[0] += vel
                self.rotate_image(-90)
            
            self.check_screen_entry()
        else:
            if self.turning:
                self.turn_counter -= 1
                if self.turn_counter <= 0:
                    self.turning = False
                    self.direction = random.choice(["top", "bottom", "left", "right"])

            if self.direction == "top":
                self.pos[1] -= vel
                self.rotate_image(0)
            elif self.direction == "bottom":
                self.pos[1] += vel
                self.rotate_image(180)
            elif self.direction == "left":
                self.pos[0] -= vel
                self.rotate_image(90)
            elif self.direction == "right":
                self.pos[0] += vel
                self.rotate_image(-90)

            if self.has_entered_screen and not self.turning and random.random() < 0.05:  # 5% chance to start turning
                self.turning = True
                self.turn_counter = random.randint(30, 60)

    def rotate_image(self, angle):
        self.ship_image = pygame.transform.rotate(self.original_image, angle)
        self.mask = pygame.mask.from_surface(self.ship_image)

    def draw(self, screen):
        rotated_rect = self.ship_image.get_rect(center=self.pos)
        screen.blit(self.ship_image, rotated_rect.topleft)

def update_bugs(bugs, screen, wave_length=5):
    for bug in bugs:
        bug.move(1)
        bug.draw(screen)
        if bug.health <= 0 or bug.pos[1] > SCREEN_HEIGHT or bug.pos[0] > SCREEN_WIDTH or bug.pos[0] < 0 or bug.pos[1] < 0:
            bugs.remove(bug)

    if len(bugs) == 0:
        for i in range(wave_length):
            new_bug = Bug()
            bugs.append(new_bug)
