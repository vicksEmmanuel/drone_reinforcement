from conv_agent import agent_train
import os, sys
import pygame

# set SDL to use the dummy NULL video driver, 
#   so it doesn't need a windowing system.
os.environ["SDL_VIDEODRIVER"] = "dummy"


if 1:
    agent_train()



def scaleit(fin, fout, w, h):
    i = pygame.image.load(fin)

    if hasattr(pygame.transform, "smoothscale"):
        scaled_image = pygame.transform.smoothscale(i, (w,h))
    else:
        scaled_image = pygame.transform.scale(i, (w,h))
    pygame.image.save(scaled_image, fout)


if __name__ == "__main__":
    if "-scale" in sys.argv:
        fin, fout, w, h = sys.argv[2:]
        w, h = map(int, [w,h])
        scaleit(fin, fout, w,h)
    else:
        print("usafe")