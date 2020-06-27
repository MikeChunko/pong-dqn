# Implementation of Pong in pygame
import numpy as np
import pygame as pyg
import random
import math
import argparse
from pong_dqn import Agent
from random import randrange, randint
from keras.utils import to_categorical


def define_parameters():
    params = dict()
    params["epsilon_decay_linear"] = 1 / 100
    params["learning_rate"] = 0.0005
    params["first_layer_size"] = 25
    params["second_layer_size"] = 25
    params["third_layer_size"] = 25
    params["episodes"] = 200
    params["memory_size"] = 2500
    params["batch_size"] = 50
    params["weights_path"] = "weights.hdf5"
    params["train"] = True
    return params


class Pong:
    def __init__(self, draw=True, screen_x=300, screen_y=300):
        pyg.init()
        pyg.font.init()
        self.white = (255, 255, 255)
        self.size_x = self.size_y = 10  # "Pixel" size
        self.screen_x, self.screen_y = screen_x, screen_y

        if draw:
            self.screen = pyg.display.set_mode((self.screen_x, self.screen_y))
            pyg.display.update()
            pyg.display.set_caption("Pong")

        self.clock = pyg.time.Clock()
        self.sentinel = True
        self.font = pyg.font.SysFont("hack", 30)
        self.draw = draw
        self.hit = False

        # _1 is for the player 1, _2 is for player 2
        self.score_1 = self.score_2 = 0
        self.paddle_1 = self.paddle_2 = screen_y / 2 - (2 * self.size_y)
        self.delta_1 = self.delta_2 = 0
        self.paddle_length = 5
        self.ball_x, self.ball_y = screen_x / 2, screen_y / 2
        self.ball_delta_x, self.ball_delta_y = -.5, 0
        self.delta_factor = 1.8
        self.min_delta_factor = .8
        self.score_timer = 300
        self.volley = 0

    def display(self):
        """ Display the game. """
        self.screen.fill((0, 0, 0))  # Blank the screen

        pyg.draw.rect(self.screen, self.white, [self.ball_x, self.ball_y, self.size_x, self.size_y])  # Ball

        for i in range (0, self.paddle_length * self.size_y, self.size_y):  # Paddles
            pyg.draw.rect(self.screen, self.white, [0, self.paddle_1 + i, self.size_y, self.size_y])
            pyg.draw.rect(self.screen, self.white, [self.screen_x - self.size_x, self.paddle_2 + i, self.size_x, self.size_y])

        for i in range(0, self.screen_x, self.size_x):  # Border
            pyg.draw.rect(self.screen, self.white, [i, 0, self.size_x, self.size_y])
            pyg.draw.rect(self.screen, self.white, [i, self.screen_y - self.size_y, self.size_x, self.size_y])

        if self.score_timer > 0:
            textsurface = self.font.render("{} - {}".format(self.score_1, self.score_2), True, (255, 255, 255))
            self.screen.blit(textsurface, textsurface.get_rect(center=(self.screen_x // 2, self.size_y * 4)))
            self.score_timer -= 1

    def get_features(self):
        return [
            self.paddle_2 +  (self.paddle_length * self.size_y / 2),
            self.ball_y, self.ball_delta_x * self.delta_factor,
            self.ball_delta_y * self.delta_factor
        ]

    def process_input(self, input):
        """ Fetch and handle user input. """
        for event in pyg.event.get():  # Quit
            if event.type == pyg.QUIT:
                pyg.quit()
                quit()

            if event.type == pyg.KEYDOWN and event.key == pyg.K_r:  # Restart
                self.sentinel = False
                self.score_1 = self.score_2 = 0

        # Player 1
        if self.paddle_1 > self.ball_y:
            self.delta_1 = -.5
        else:
            self.delta_1 = .5

        # Player 2
        if input == 0:
            self.delta_2 = -.5
        elif input == 1:
            self.delta_2 = .5
        elif input == 2:
            self.delta_2 = 0

    def move_paddles(self):
        """ Move both paddles.
            Do bounds checking to ensure they do not move outside the screen. """
        # Player 1
        new_paddle_1 = self.paddle_1 + self.delta_1
        if (new_paddle_1 > self.size_y
            and new_paddle_1 + (self.paddle_length * self.size_y) < self.screen_y - self.size_y):
            self.paddle_1 += self.delta_1

        # Player 2
        new_paddle_2 = self.paddle_2 + self.delta_2
        if (new_paddle_2 > self.size_y
            and new_paddle_2 + (self.paddle_length * self.size_y) < self.screen_y - self.size_y):
            self.paddle_2 += self.delta_2

    def move_ball(self):
        """ Move the ball and do the relevant calculations for if it hit a wall, paddle, or goal. """
        def get_intersect_angle(paddle_num):
            """ Calculate the normalized angle to bounce the ball off of a paddle. """
            if paddle_num == 1:
                paddle = self.paddle_1
            else:
                paddle = self.paddle_2

            relative_intersect = (paddle + (self.paddle_length * self.size_y) / 2) - self.ball_y - (self.size_y / 2)
            return relative_intersect / (self.paddle_length * self.size_y / 2)  # Normalize

        def increase_delta_factor():
            """ Speed up the ball. """
            if self.delta_factor > self.min_delta_factor:
                self.delta_factor -= self.delta_factor / 12

        self.hit = False

        # Check paddle intersect
        self.ball_x += self.ball_delta_x
        self.ball_y += self.ball_delta_y

        # Player 1 side
        if self.ball_x <= self.size_x and self.ball_x >= 0:
            increase_delta_factor()
            intersect_angle = get_intersect_angle(1)
            if intersect_angle > -1.1 and intersect_angle < 1.1:  # Paddle miss
                self.ball_delta_x, self.ball_delta_y = math.cos(intersect_angle) / self.delta_factor, \
                                                      -math.sin(intersect_angle) / self.delta_factor
                self.volley += 1
        elif self.ball_x < -self.size_x:
            self.score_2 += 1
            self.sentinel = False
            self.clock.tick(3)

        # Player 2 side
        if self.ball_x >= self.screen_x -  2 * self.size_x and self.ball_x <= self.screen_x:
            increase_delta_factor()
            intersect_angle = get_intersect_angle(2)
            if intersect_angle > -1.1 and intersect_angle < 1.1:  # Paddle miss
                self.ball_delta_x, self.ball_delta_y = -math.cos(intersect_angle) / self.delta_factor, \
                                                       -math.sin(intersect_angle) / self.delta_factor
                self.hit = True
                self.volley += 1
        elif self.ball_x > self.screen_x + self.size_x:
            self.score_1 += 1
            self.sentinel = False
            self.clock.tick(3)

        # Borders
        if self.ball_y <= self.size_y or self.ball_y >= self.screen_y - 2 * self.size_y:
            self.ball_delta_y = -self.ball_delta_y

    def step(self, tick=200, input=0):
        """ Process one step of the game. """
        self.process_input(input)
        self.move_paddles()
        self.move_ball()

        if self.draw:
            self.display()
            pyg.display.update()

        self.clock.tick(tick)


def str_to_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


if __name__ == "__main__":
    pyg.init()
    pyg.font.init()
    tick = 2000
    params = define_parameters()
    num_games = 0

    parse = argparse.ArgumentParser()
    parse.add_argument("--draw", type=str_to_bool, default=True, help="whether or not to draw the game")
    parse.add_argument("--train", type=str_to_bool, default=True, help="whether or not to train")
    args = parse.parse_args()
    params["train"] = args.train

    agent = Agent(params)
    score_1 = score_2 = 0

    while num_games < params["episodes"]:
        game = Pong(draw=args.draw)
        game.score_1, game.score_2 = score_1, score_2
        timer = 0

        while game.sentinel:
            if timer == 0:
                if not params["train"]:
                    agent.epsilon = 0
                else:
                    # Epsilon determines randomness factor
                    agent.epsilon = 1 - (num_games * params["epsilon_decay_linear"])

                state_old = np.asarray(game.get_features())
                if randint(0, 1) < agent.epsilon:  # Random action
                    final_input = randint(0, 2)
                    final_move = to_categorical(final_input, num_classes=3)
                else:  # Predict action based on nn
                    prediction = agent.model.predict(state_old.reshape((1, 4)))
                    final_move = to_categorical(np.argmax(prediction[0]), num_classes=3)

                    if np.array_equal(final_move, [1, 0, 0]):
                        final_input = 0
                    elif np.array_equal(final_move, [0, 1, 0]):
                        final_input = 1
                    else:
                        final_input = 2

            game.step(tick=tick, input=final_input)

            if timer == 0:
                timer = 100
                state_new = np.asarray(game.get_features())
                reward = (score_1 - game.score_1) * 100
                if reward == 0:
                    reward += 1
                if game.hit:
                    reward += 500

                if params["train"]:
                    # Train short memory based on the new action and state
                    agent.train_short_memory(state_old, final_move, reward, state_new, not game.sentinel)
                    # Store into long term memory
                    agent.remember(state_old, final_move, reward, state_new, not game.sentinel)
            else:
                timer -= 1

            score_1, score_2 = game.score_1, game.score_2

        num_games += 1
        print("Round: {}, Score: {} - {}, Volley: {}".format(num_games, score_1, score_2, game.volley))

        if params["train"]:
            agent.replay_new(params["batch_size"])

    # Save the calculated weights for later use
    if params["train"]:
        agent.model.save_weights(params["weights_path"])

