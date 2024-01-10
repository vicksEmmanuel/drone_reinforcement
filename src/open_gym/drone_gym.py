import cv2
from gym import Env
import pygame
from gym.spaces import Discrete, Box
import numpy as np
from collections import deque
from conv_agent import FRAME_STACK_SIZE

from game import Game
from game_objects.constant import CONV_INPUT_NUMBER, OUTPUT_NUMBER

class DroneShooterEnv(Env):
    def __init__(self):
       self.action_space = Discrete(OUTPUT_NUMBER)
       self.observation_space = Box(low=0, high=1, shape=(CONV_INPUT_NUMBER, 84, 84), dtype=np.float32)
       self.game = Game()
       self.frame_stack = deque(maxlen=FRAME_STACK_SIZE)  # Assuming FRAME_STACK_SIZE is 4

        # Initialize the game and capture the initial frame
       self.game.reset()
       self.game.render()
       initial_frame = self.capture_screen()
       processed_initial_frame = self.preprocess_frame(initial_frame)

        # Fill the frame stack with the initial processed frame
       for _ in range(FRAME_STACK_SIZE):
            self.frame_stack.append(processed_initial_frame)

    def step(self, action):
        action_vector = [0] * self.action_space.n
        action_vector[action] = 1
        
        # Take the step using the one-hot encoded action
        reward, done, score = self.game.play(action_vector)
        
        # Get the new observation
        observation = self._get_observation()
        
        info = {'score': score, 'level': self.game.level}

        return observation, reward, done, info
        
    def reset(self):
        self.game.reset()
        self.game.render()
        
        initial_screen = self.capture_screen()
        processed_initial_frame = self.preprocess_frame(initial_screen)

        self.frame_stack.clear()
        for _ in range(4):
            self.frame_stack.append(processed_initial_frame)

        observation = self._get_observation()

        return observation

    def render(self, mode='human'):
        self.game.render()
        
        if mode == 'rgb_array':
            # Return the RGB array of the screen for video recording and model analysis
            return self._get_screen_as_array()

    def _get_observation(self):
        # Capture the current game screen, preprocess it, and stack with the previous frames
        screen_data = self.capture_screen()
        processed_frame = self.preprocess_frame(screen_data)
        self.frame_stack.append(processed_frame)
        
        # Convert the deque of frames to a numpy array
        return np.array(self.frame_stack)
    
    def _get_screen_as_array(self):
        screen_data = self.capture_screen()
        screen_data = screen_data.astype(np.float32) / 255.0

    def capture_screen(self):
       screen_data = pygame.surfarray.array3d(self.game.screen)
       screen_data = np.transpose(screen_data, (1, 0, 2))
       return screen_data

    
    def preprocess_frame(self, frame, new_size=(84, 84)):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        resized_frame = cv2.resize(gray_frame, new_size, interpolation=cv2.INTER_AREA)
        normalized_frame = resized_frame / 255.0 
        return normalized_frame
    
    def stack_frames(self, new_frame, is_new_episode):
        if is_new_episode:
            self.frame_stack.clear()
            for _ in range(FRAME_STACK_SIZE):
                self.frame_stack.append(new_frame)
        else:
            self.frame_stack.append(new_frame)

        # Combine the frames into a single 3D array (shape: [4, 84, 84])
        stacked_frames = np.stack(list(self.frame_stack), axis=0)
        return stacked_frames
