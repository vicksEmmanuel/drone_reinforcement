import cv2
import pygame
import torch
import random
import numpy as np
from collections import deque
from conv_model import Conv_QNet, Conv_QTrainer
from game_objects.attackers.bug import collide
from game_objects.constant import  COLLISION_PENALTY, CONV_INPUT_NUMBER, LAYERS, OUTPUT_NUMBER, SCREEN_HEIGHT, SCREEN_WIDTH, Direction, DirectionValue
from game import Game
from helper import load_values, plot, save_values

MAX_MEMORY = 100_000_000_000
BATCH_SIZE = 1000000
LR = 0.001
FRAME_STACK_SIZE = CONV_INPUT_NUMBER

class Agent:

    def __init__(self):
        self.n_games = 0
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.epsilon = 0 # randomness

        self.explore_start = 1.0            # exploration probability at start
        self.explore_stop = 0.01            # minimum exploration probability 
        self.decay_rate = 0.00001

        
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()
        self.frame_stack = deque(maxlen=FRAME_STACK_SIZE) 

        self.model = Conv_QNet(CONV_INPUT_NUMBER, OUTPUT_NUMBER)
        self.model.load()
        self.trainer = Conv_QTrainer(self.model, lr=LR, gamma=self.gamma)

        self.direction_sequences = [
            [DirectionValue.RIGHT, DirectionValue.UP, DirectionValue.LEFT, DirectionValue.DOWN],
            [DirectionValue.DOWN, DirectionValue.UP, DirectionValue.RIGHT, DirectionValue.LEFT],
            [DirectionValue.LEFT, DirectionValue.UP, DirectionValue.DOWN, DirectionValue.RIGHT],
            [DirectionValue.RIGHT, DirectionValue.DOWN, DirectionValue.LEFT, DirectionValue.UP],
            [DirectionValue.LEFT, DirectionValue.DOWN, DirectionValue.RIGHT, DirectionValue.UP],
            [DirectionValue.UP, DirectionValue.RIGHT, DirectionValue.DOWN, DirectionValue.LEFT]
        ]
        self.current_sequence = random.choice(self.direction_sequences)
        self.current_direction_index = 0
        self.steps_in_current_direction = 0
        self.max_steps_in_current_direction = random.randint(1, 100)


    def stack_frames(self, new_frame, is_new_episode):
        if is_new_episode:
            # Clear the frame stack and populate with the same frame for a new episode
            self.frame_stack.clear()
            for _ in range(FRAME_STACK_SIZE):
                self.frame_stack.append(new_frame)
        else:
            # Add the new frame and remove the oldest frame
            self.frame_stack.append(new_frame)

        # Combine the frames into a single 3D array (shape: [4, 84, 84])
        stacked_frames = np.stack(list(self.frame_stack), axis=0)
        return stacked_frames

    def capture_screen(self, screen):
        # Convert the screen to a 3D array (width x height x 3)
        screen_data = pygame.surfarray.array3d(screen)
        # Transpose it to a format suitable for OpenCV (height x width x 3)
        screen_data = screen_data.transpose([1, 0, 2])
        return screen_data

    def preprocess_frame(self, frame, new_size=(84, 84)):
        # Convert frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        # Resize to reduce the complexity
        resized_frame = cv2.resize(gray_frame, new_size, interpolation=cv2.INTER_AREA)
        # Normalize pixel values to be between 0 and 1
        normalized_frame = resized_frame / 255.0
        return normalized_frame

    def get_state(self, stacked_frames):
        state = torch.tensor(stacked_frames, dtype=torch.float)
        return state

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        # Unzip the mini-batch of experiences
        states, actions, rewards, next_states, dones = zip(*mini_sample)

        # Unzip experiences and convert to tensors
        states, actions, rewards, next_states, dones = zip(*mini_sample)

        states_tensor = torch.stack([torch.Tensor(s) for s in states]).to(self.device)
        next_states_tensor = torch.stack([torch.Tensor(s) for s in next_states]).to(self.device)
        actions_tensor = torch.tensor(actions, dtype=torch.long).to(self.device)
        rewards_tensor = torch.tensor(rewards, dtype=torch.float).to(self.device)
        dones_tensor = torch.tensor(dones, dtype=torch.bool).to(self.device)

        # Call the trainer's train_step method
        self.trainer.train_step(states_tensor, actions_tensor, rewards_tensor, next_states_tensor, dones_tensor)

    def train_short_memory(self, state, action, reward, next_state, done):
        # Convert single experience to tensors with batch size of 1
        state_tensor = torch.tensor(state, dtype=torch.float).unsqueeze(0).to(self.device)
        next_state_tensor = torch.tensor(next_state, dtype=torch.float).unsqueeze(0).to(self.device)
        action_tensor = torch.tensor([action], dtype=torch.long).to(self.device)
        reward_tensor = torch.tensor([reward], dtype=torch.float).to(self.device)
        done_tensor = torch.tensor([done], dtype=torch.uint8).to(self.device)

        self.trainer.train_step(state_tensor, action_tensor, reward_tensor, next_state_tensor, done_tensor)

    def get_action(self, state):
        self.epsilon = 1000 - self.n_games
        final_move = [0] * OUTPUT_NUMBER

        if random.randint(0, 800) < self.epsilon:
            self.update_movement_sequence()
            current_direction = self.current_sequence[self.current_direction_index]
            print("Action: Random")
            return current_direction.value
        else:
            state_tensor = torch.tensor(state, dtype=torch.float).unsqueeze(0)  # Add batch dimension

            # Check if the model is on GPU
            if next(self.model.parameters()).is_cuda:
                state_tensor = state_tensor.cuda()

            self.model.eval()  # Set the model to evaluation mode
            with torch.no_grad():  # Turn off gradients for prediction
                prediction = self.model(state_tensor)

            move = torch.argmax(prediction).item()
            action_map = {
                0: DirectionValue.None_.value,  # NONE
                1: DirectionValue.LEFT.value,  # LEFT
                2: DirectionValue.RIGHT.value,  # RIGHT
                3: DirectionValue.UP.value,    # UP
                4: DirectionValue.DOWN.value   # DOWN
            }

            final_move = action_map.get(move, DirectionValue.None_.value)
            print("Action: Predicted")

            return final_move
            # move = torch.argmax(prediction).item()
            # final_move[move] = 1

    def update_movement_sequence(self):
        # Update steps and direction
        self.steps_in_current_direction += 1
        if self.steps_in_current_direction >= self.max_steps_in_current_direction:
            self.steps_in_current_direction = 0
            self.max_steps_in_current_direction = random.randint(1, 50)
            self.current_direction_index = (self.current_direction_index + 1) % len(self.current_sequence)

            # If the sequence is complete, pick a new sequence
            if self.current_direction_index == 0:
                self.current_sequence = random.choice(self.direction_sequences)


def agent_train():
    plot_scores, plot_mean_scores, plot_reward, plot_mean_reward, n_games, record = load_values()

    total_score = sum(plot_scores)
    total_reward = sum(plot_reward)
    agent = Agent()
    game = Game()
    agent.n_games = n_games
    is_new_episode = True

    reward_per_episode = []

    while True:

        screen_data = agent.capture_screen(game.screen)
        processed_frame = agent.preprocess_frame(screen_data)
        stacked_frames = agent.stack_frames(processed_frame, is_new_episode)
        state_old = agent.get_state(stacked_frames)

        # Update the is_new_episode flag accordingly
        is_new_episode = False

        # get move
        final_move = agent.get_action(state_old)

        # Perform the action and get the new state
        reward, done, score = game.play(final_move)
        _, __, is_collision = game.update_closest_bug_data(game.bugs, game.ship)

        if is_collision:
            reward -= COLLISION_PENALTY

        reward_per_episode.append(reward)

        new_screen_data = agent.capture_screen(game.screen)
        processed_new_frame = agent.preprocess_frame(new_screen_data)
        new_stacked_frames = agent.stack_frames(processed_new_frame, done)
        state_new = agent.get_state(new_stacked_frames)


        # Train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # Remember for long term memory
        agent.remember(state_old, final_move, reward, state_new, done)

        # Update the is_new_episode flag accordingly
        is_new_episode = done


        if done:
            # train long memory, plot result

            if (agent.n_games % 10 == 0):
                print(f"Game: {agent.n_games}, Score: {score}, Record: {record}")
                agent.train_long_memory()

            agent.n_games += 1
            game.reset()

            if score > record:
                record = score
                agent.model.save()
            else:
                agent.model.save()


            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)


            plot_reward.append(sum(reward_per_episode))
            total_reward += sum(reward_per_episode)
            mean_reward = total_reward / agent.n_games
            plot_mean_reward.append(mean_reward)



            save_values(
                plot_scores, 
                plot_mean_scores, 
                plot_reward, 
                plot_mean_reward, 
                agent.n_games, 
                record
            )

            reward_per_episode = []


