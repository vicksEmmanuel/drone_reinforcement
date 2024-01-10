from torch.utils.tensorboard import SummaryWriter
import torch
import random
import numpy as np
from collections import deque
from agent.dqn import Agent
from conv_model import Conv_QNet, Conv_QTrainer
from drone_gym import DroneShooterEnv
from game_objects.constant import CONV_INPUT_NUMBER, OUTPUT_NUMBER  # Import your custom Gym environment
from helper import plot

env = DroneShooterEnv()
agent = Agent()
writer = SummaryWriter('runs/drone_shooter_experiment_1')


def train(n_episodes=10000, save_interval=100, filename="model.pth"):
    run = 0
    best_score = -float("inf")  # Initialize best score to a very low number

    for i_episode in range(1, n_episodes + 1):
        state = env.reset()
        score = 0


        while True:
            action = agent.act(state)
            env.render()
            state_next, reward, done, _ = env.step(action)
            score += reward
            agent.remember(state, action, reward, state_next, done)
            state = state_next

            if done:
                try:
                    writer.add_scalar('Score', score, i_episode)
                    print(f"Episode: {i_episode}, Exploration: {agent.exploration_rate}, Score: {score}")
                except Exception as e:
                    print(f"Episode: {i_episode}, Score: {score}")
                
                if score > best_score:
                    best_score = score
                    agent.model.save()

                break
            agent.experience_replay()
            
    writer.close()

train()
