import pygame
import math
import os
import time
import random

from game import BACKGROUND_SCROLL_SPEED, SCREEN_HEIGHT, SCREEN_WIDTH
from game_objects.background import draw_background
from game_objects.bug import Bug, update_bugs
from game_objects.drone import create_drone, reset_drone, update_drone

pygame.init()


clock = pygame.time.Clock()
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Drone Shooter")
main_font = pygame.font.SysFont("comicsans", 20)

run  = True
scroll = 0

ship, controller, world, options = create_drone()

bugs = []
wave_length = 5
bug_vel = 1
level = 1
lost = False
lost_count = 0


while run:

    clock.tick(FPS)

    if ship.health <= 0:
        lost = True
        lost_count += 1

    if lost:
        if lost_count > FPS * 3:
            level = 1
            lost_count = 0
            lost = False
            wave_length = 5
            bugs = []
            bug_vel = 1
            reset_drone(ship)
        else:
            continue
         

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN:
                controller.desired_height = world.width - event.pos[1]
                controller.desired_x = event.pos[0] - (screen.get_size()[0] / 2)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                controller.estimated_x = ship.pos[0] - (screen.get_size()[0] / 2)
                controller.desired_x = world.width - ship.pos[1]


    scroll = draw_background(screen, scroll)

    update_drone(ship, screen, *options)

    
    level  = update_bugs(bugs, screen, ship, level, wave_length * level)
    lives_label = main_font.render(f"Lives: {ship.health}", 1, (0,0,0))
    level_label = main_font.render(f"Level: {level}", 1, (0,0,0))

    screen.blit(lives_label, (10, 10))
    screen.blit(level_label, (SCREEN_WIDTH - level_label.get_width() - 10, 10))

    pygame.display.update()


pygame.quit()