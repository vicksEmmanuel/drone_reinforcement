import math
import os
import pygame

from game_objects.constant import BACKGROUND_SCROLL_SPEED, SCREEN_HEIGHT, SCREEN_WIDTH


# background_image1 = pygame.image.load(os.path.join("assets/background", "background6.jpg"))

file_path = os.path.join(os.path.dirname(__file__), "assets/background", "background6.jpg")
print("Loading image from:", file_path)
background_image1 = pygame.image.load(file_path)

# background_image1 = pygame.transform.scale(background_image1, (SCREEN_WIDTH, SCREEN_HEIGHT/2))

BG_HEIGHT = background_image1.get_height()
BG_RECT = background_image1.get_rect()

BG_TILES = math.ceil(SCREEN_HEIGHT  / BG_HEIGHT)
GAME_BACKGROUND = background_image1

def draw_background(screen, scroll):
    #draw scrolling background
    for i in range(0, BG_TILES):
        screen.blit(GAME_BACKGROUND, (0, i * SCREEN_HEIGHT - scroll))
        BG_RECT.y = i * BG_HEIGHT + scroll
        screen.blit(GAME_BACKGROUND, BG_RECT)


    #scroll background
    scroll -= BACKGROUND_SCROLL_SPEED

    #reset scroll
    if abs(scroll) >= SCREEN_HEIGHT:
        scroll = 0

    return scroll
