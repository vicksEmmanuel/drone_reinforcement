import torch
import random
import numpy as np
from collections import deque
from game_objects.attackers.bug import collide
from game_objects.constant import  INPUT_NUMBER, LAYERS, OUTPUT_NUMBER, Direction
from game import Game
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 # randomness
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen=MAX_MEMORY) # popleft()
        self.model = Linear_QNet(INPUT_NUMBER, LAYERS, OUTPUT_NUMBER)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)


    def get_state(self, game):
        ship = game.ship
        bugs = game.bugs

        dir_l = ship.direction == Direction.LEFT
        dir_r = ship.direction == Direction.RIGHT
        dir_u = ship.direction == Direction.UP
        dir_d = ship.direction == Direction.DOWN
        dir_sharp_d = ship.direction == Direction.SHARP_DOWN
        dir_steady = ship.direction == Direction.STEADY


        bug_distances = [bug.distance_to_ship(ship) for bug in bugs]

        # Find the distance to the closest bug
        # If there are no bugs, you can set a default value (e.g., a large number)
        closest_bug_distance = min(bug_distances) if bug_distances else 0


        # Check if bugs are on the right or left of the ship
        bugs_on_right = any(bug.pos[0] > ship.pos[0] for bug in bugs)
        bugs_on_left = any(bug.pos[0] < ship.pos[0] for bug in bugs)
        bugs_above = any(bug.pos[1] < ship.pos[1] for bug in bugs)
        bugs_below = any(bug.pos[1] > ship.pos[1] for bug in bugs)


        total_x_offset = 0
        total_y_offset = 0
        num_bugs = len(bugs)

        for bug in bugs:
            total_x_offset += (bug.pos[0] - ship.pos[0])
            total_y_offset += (bug.pos[1] - ship.pos[1])

        # Averaging the offsets
        avg_x_offset = total_x_offset / num_bugs if num_bugs > 0 else 0
        avg_y_offset = total_y_offset / num_bugs if num_bugs > 0 else 0

        state = [

            game.level,
            game.wave_length,

            ship.pos[0], ship.pos[1], 
            ship.rot, ship.vel[0], 
            ship.vel[1], 
            ship.health,
            ship.r_thruster()[0],
            ship.r_thruster()[1],
            ship.l_thruster()[0],
            ship.l_thruster()[1],



            # Move direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,
            dir_sharp_d,
            dir_steady,
            

            # Bugs on the right or left or top or bottom
            avg_x_offset,
            avg_y_offset,
            bugs_on_right,
            bugs_on_left,
            bugs_above,
            bugs_below,

            closest_bug_distance,
            


            any((dir_r and collide(ship, bug)) for bug in bugs) or 
            any((dir_l and collide(ship, bug)) for bug in bugs) or 
            any((dir_u and collide(ship, bug)) for bug in bugs) or 
            any((dir_d and collide(ship, bug)) for bug in bugs)
        ]


        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)
        #for state, action, reward, nexrt_state, done in mini_sample:
        #    self.trainer.train_step(state, action, reward, next_state, done)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 80 - self.n_games
        final_move = [0] * OUTPUT_NUMBER
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, OUTPUT_NUMBER-1)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = Game()
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play(final_move)
        print("reward: ", reward, "done: ", done, "score: ", score)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()


            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()