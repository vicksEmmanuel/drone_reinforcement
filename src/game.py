import datetime
import math
import pygame

from game_objects.constant import NEXT_DRAW,COLLISION_PENALTY, DRAW_PERIOD, SCREEN_HEIGHT, SCREEN_WIDTH
from game_objects.background import draw_background
from game_objects.attackers.bug import  update_bugs
from game_objects.drone.drone import create_drone, update_drone

pygame.init()

class Game:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.FPS = 60

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Drone Shooter")
        self.main_font = pygame.font.SysFont("comicsans", 20)

        self.run  = True
        self.scroll = 0

        self.ship, self.controller, self.world, self.options = create_drone()

        self.bugs = []
        self.wave_length = 5
        self.bug_vel = 1
        self.level = 0
        self.lost = False
        self.lost_count = 0
        self.score  = 0

        self.reward = 0
        self.drone_reward = 0
        self.bug_reward = 0

    def play(self, action):
        self.clock.tick(self.FPS)
        
        reward = self.reward
        drone_reward = self.drone_reward
        bug_reward = self.bug_reward

        self.lost = False
        self.lost_count = 0

        if self.ship.health <= 0:
            self.lost = True
            self.lost_count += 1
            reward = COLLISION_PENALTY

            return reward, self.lost, self.score


        if len(self.bugs) == 0 :
            self.level += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False



        drone_reward += update_drone(self.ship, self.screen, drone_reward, action, *self.options)
  
        new_bug_reward, score  = update_bugs(
            self.bugs, self.screen, 
            self.ship, self.level, bug_reward, self.score,
            self.wave_length * self.level, 
        )

        bug_reward += new_bug_reward

        if (bug_reward < 0):
            reward = bug_reward
        else:
            reward += int(drone_reward + bug_reward)
        
        self.score = score
        
        return reward, self.lost, self.score


    def render(self):
        self.scroll = draw_background(self.screen, self.scroll)

        now = datetime.datetime.now()
        next_draw_val = self.ship.next_draw
        if now >= next_draw_val:
                next_draw_val += DRAW_PERIOD

                self.ship.draw(self.screen)
        

        for bug in self.bugs:
            bug.draw(self.screen)


        lives_label = self.main_font.render(f"Lives: {self.ship.health}", 1, (0,0,0))
        level_label = self.main_font.render(f"Level: {self.level}", 1, (0,0,0))
        reward_label = self.main_font.render(f"Reward: {self.reward}", 1, (0,0,0))
        score_label = self.main_font.render(f"Score: {int(self.score)}", 1, (0,0,0))

        self.screen.blit(lives_label, (10, 35))
        self.screen.blit(score_label, (10, 10))
        self.screen.blit(level_label, (SCREEN_WIDTH - level_label.get_width() - 10, 10))
        self.screen.blit(reward_label, (SCREEN_WIDTH - reward_label.get_width() - 10, 35))

        

        pygame.display.update()



    def update_closest_bug_data(self, bugs, ship):
        if not bugs:
            return SCREEN_HEIGHT, (SCREEN_WIDTH, SCREEN_HEIGHT), False  # or a large number to indicate no bugs

        # Update distances for all bugs
        bug_distances = [(bug, bug.distance_to_ship(ship)) for bug in bugs]
        # Sort bugs by distance
        bug_distances.sort(key=lambda x: x[1])

        # Get the closest bug's data
        closest_bug, closest_distance = bug_distances[0]

        # Check for potential collisions with the drone
        for next_bug, distance in bug_distances[1:]:
            if self.is_on_collision_course(next_bug, ship):
                # Take evasive action or update the reward system
                return closest_distance, closest_bug.pos, True

        return closest_distance, closest_bug.pos, False

    def is_on_collision_course(self, bug, ship):
        # Simple collision course logic based on the bug moving directly towards the ship's current position
        next_bug_pos = [bug.pos[0] + bug.velocity[0], bug.pos[1] + bug.velocity[1]]
        distance_to_next_pos = math.sqrt((next_bug_pos[0] - ship.pos[0])**2 + (next_bug_pos[1] - ship.pos[1])**2)
        # Assuming a buffer zone radius around the ship for collision
        buffer_zone_radius = 50  
        return distance_to_next_pos < buffer_zone_radius

    def reset(self):
        self.level = 0
        self.score = 0

        self.wave_length = 5
        self.bugs = []
        self.bug_vel = 1
        self.reward = 0
        self.drone_reward = 0
        self.bug_reward = 0
        self.main_font = pygame.font.SysFont("comicsans", 20)
        self.ship.reset_drone()