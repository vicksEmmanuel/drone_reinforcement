import os
import random
import pygame
import math
from game_objects.constant import COLLISION_PENALTY, SCREEN_HEIGHT, SCREEN_WIDTH, DRONE_HEALTH, SURVIVAL_REWARD

ENEMY_BUG = pygame.image.load(os.path.join(os.path.dirname(__file__), "../assets", "Bug.png"))
ENEMY_BUG = pygame.transform.scale(ENEMY_BUG, (30, 30))

class Bug:
    def __init__(self, health=DRONE_HEALTH, ship_position=None, offset=0, level=1):
        self.health = health
        self.original_image = ENEMY_BUG
        self.mask = pygame.mask.from_surface(self.original_image)
        self.pos = self.get_random_start_position(offset)
        self.ship_position = ship_position
        self.constant_speed = 1.0 + (level/10)  # Constant speed for all bugs
        self.velocity = [self.constant_speed, 0]  # Start moving horizontally
        self.manoeuvre_started = False
        self.entry_side = self.determine_entry_side(offset)  # Determine the entry side
        self.offset = offset  # Horizontal offset for spacing in formation
        self.curve_factor = random.uniform(0.1, 0.3)  # Factor to determine the curvature of the path

    def get_random_start_position(self, offset):
        # Start position is now influenced by the horizontal offset
        y_pos = random.randint(0, SCREEN_HEIGHT * 0.3)
        x_pos = (-50 if random.choice([True, False]) else SCREEN_WIDTH + 50) + offset
        return [x_pos, y_pos]
    
    def determine_entry_side(self, offset):
        if offset < 0:
            return 'left'
        elif offset > 0:
            return 'right'
    
    def distance_to_ship(self, ship):
        dx = self.pos[0] - ship.pos[0]
        dy = self.pos[1] - ship.pos[1]
        return math.sqrt(dx**2 + dy**2)

    def calculate_angle_to_ship(self):
        dx = self.ship_position[0] - self.pos[0]
        dy = self.ship_position[1] - self.pos[1]
        return math.degrees(math.atan2(dy, dx))

    def move(self):
        # If not yet maneuvering, move horizontally until 30% across the screen
        if not self.manoeuvre_started and (self.pos[0] > SCREEN_WIDTH * 0.3 or self.pos[0] < SCREEN_WIDTH * 0.7):
            self.manoeuvre_started = True
            self.angle = self.calculate_angle_to_ship()
        
        # Update the velocity towards the drone's position
        self.velocity[0] = self.constant_speed * math.cos(math.radians(self.angle))
        self.velocity[1] = self.constant_speed * math.sin(math.radians(self.angle))

        # Update position with velocity
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        
        # Apply a sine wave function to create a curve
        if self.manoeuvre_started:
            self.pos[0] += math.sin(self.pos[1] * self.curve_factor) * self.constant_speed

    def rotate_image(self):
        # Calculate the direction of movement
        direction_angle = math.atan2(self.velocity[1], self.velocity[0])
        rotation_angle = math.degrees(direction_angle) - 270
        self.ship_image = pygame.transform.rotate(self.original_image, abs(rotation_angle) )
        self.mask = pygame.mask.from_surface(self.ship_image)

    def draw(self, screen):
        self.rotate_image()
        rotated_rect = self.ship_image.get_rect(center=self.pos)
        screen.blit(self.ship_image, rotated_rect.topleft)

def update_bugs(
        bugs, screen, ship, 
        level, reward, score, 
        wave_length=5, spacing=50,
    ):
    global spawn_side  # Keep track of the side they should spawn from
    global spawn_angle  # Keep track of the angle they should move towards
    new_reward = 0 

    # Check if we need to spawn a new wave
    if len(bugs) == 0:
        # Determine the side for the new wave to spawn
        spawn_side = -50 if random.choice([True, False]) else SCREEN_WIDTH + 50
        spawn_angle = 0
        offset = 0

        for i in range(max(70, wave_length)):
            # Increment the offset for each bug to space them out
            offset += spacing
            new_bug = Bug(ship_position=ship.pos, offset=offset, level=level)
            new_bug.pos[0] = spawn_side
            new_bug.angle = spawn_angle
            bugs.append(new_bug)

    for bug in list(bugs):
        # Remove the bug if it has moved past the bottom of the screen
        if ((bug.entry_side == 'left' and bug.pos[0] > SCREEN_WIDTH) or
            (bug.entry_side == 'right' and bug.pos[0] < 0) or
            (bug.entry_side == 'top' and bug.pos[1] > SCREEN_HEIGHT) or
            (bug.entry_side == 'bottom' and bug.pos[1] < 0)
        ):
            bugs.remove(bug)
            score += 0.1
            new_reward += SURVIVAL_REWARD
            continue
        
        if collide(bug, ship):
            ship.health -= 0.5
            new_reward  += COLLISION_PENALTY
            bugs.remove(bug)

        
        # Update the bug's position and draw it
        bug.move()
        bug.draw(screen)
    
    return  new_reward + reward, score


def collide(obj1, obj2):
    offset_x = obj2.pos[0] - obj1.pos[0]
    offset_y = obj2.pos[1] - obj1.pos[1]
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None