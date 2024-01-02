import pygame

from game_objects.constant import SCREEN_HEIGHT, SCREEN_WIDTH
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

    def play(self, action):
        self.clock.tick(self.FPS)

        reward = 0

        if self.ship.health <= 0:
            self.lost = True
            self.lost_count += 1
            reward = -10

            return reward, self.lost, self.score

        if self.lost:
            if self.lost_count > self.FPS * 3:
                self.level = 0
                self.lost_count = 0
                self.lost = False
                self.wave_length = 5
                self.bugs = []
                self.bug_vel = 1
                self.ship.reset_drone()
            

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False


        self.scroll = draw_background(self.screen, self.scroll)

        update_drone(self.ship, self.screen, action, *self.options)

        
        self.level, reward, self.score  = update_bugs(
            self.bugs, self.screen, 
            self.ship, self.level, reward, self.score,
            self.wave_length * self.level, 
        )
        lives_label = self.main_font.render(f"Lives: {self.ship.health}", 1, (0,0,0))
        level_label = self.main_font.render(f"Level: {self.level}", 1, (0,0,0))
        score_label = self.main_font.render(f"Score: {self.score}", 1, (0,0,0))

        self.screen.blit(lives_label, (10, 10))
        self.screen.blit(score_label, ((SCREEN_WIDTH /2) - 10, 10))
        self.screen.blit(level_label, (SCREEN_WIDTH - level_label.get_width() - 10, 10))

        pygame.display.update()

        return reward, self.lost, self.score

        


# game = Game()

# while game.run:
#     game.play(None)
    


# pygame.quit()