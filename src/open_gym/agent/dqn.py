from collections import deque
from torch.utils.tensorboard import SummaryWriter
import torch
import random
import numpy as np
from conv_model import Conv_QNet, Conv_QTrainer
from game_objects.constant import CONV_INPUT_NUMBER, OUTPUT_NUMBER
from helper import plot

# Hyperparameters
MEMORY_SIZE = 100_000
BATCH_SIZE = 32
LR = 0.001
GAMMA = 0.9
EXPLORATION_MAX = 1.0
EXPLORATION_MIN = 0.01
EXPLORATION_DECAY = 0.995

class Agent:
    def __init__(self):
        self.exploration_rate = EXPLORATION_MAX
        self.action_space = OUTPUT_NUMBER
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.memory = deque(maxlen=MEMORY_SIZE)
        self.model = Conv_QNet(CONV_INPUT_NUMBER, OUTPUT_NUMBER)
        self.model.load()
        self.trainer = Conv_QTrainer(self.model, lr=LR, gamma=GAMMA)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() < self.exploration_rate:
            return random.randrange(self.action_space)
        
        state_tensor = torch.tensor(state, dtype=torch.float).to(self.device)
        q_values = self.model.forward(state_tensor)
        return np.argmax(q_values.cpu().detach().numpy()[0])

    def experience_replay(self):
        if len(self.memory) < BATCH_SIZE:
            return
        batch = random.sample(self.memory, BATCH_SIZE)
        states, actions, rewards, next_states, dones = zip(*batch)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

        self.exploration_rate *= EXPLORATION_DECAY
        self.exploration_rate = max(EXPLORATION_MIN, self.exploration_rate)

    