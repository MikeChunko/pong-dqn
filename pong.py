# Implementation of Pong in pygame
import pygame as pyg
import random
import math


class Pong:
    def __init__(self, screen_x=300, screen_y=300):
        pyg.init()
        pyg.font.init()
        self.screen_x, self.screen_y = screen_x, screen_y
        self.screen = pyg.display.set_mode((self.screen_x, self.screen_y))
        self.white = (255, 255, 255)
        self.size_x = self.size_y = 10  # "Pixel" size
        pyg.display.update()
        pyg.display.set_caption("Pong")
        self.clock = pyg.time.Clock()
        self.sentinel = True
        self.font = pyg.font.SysFont("hack", 30)

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

    def process_input(self):
        """ Fetch and handle user input. """
        for event in pyg.event.get():  # Quit
            if event.type == pyg.QUIT:
                pyg.quit()
                quit()

            # Player 1
            if event.type == pyg.KEYUP:  # Move release
                if event.key == pyg.K_w and self.delta_1 < 0:
                    self.delta_1 = 0
                elif event.key == pyg.K_s and self.delta_1 > 0:
                    self.delta_1 = 0
            elif event.type == pyg.KEYDOWN:  # Move begin
                if event.key == pyg.K_w:
                    self.delta_1 = -.5
                elif event.key == pyg.K_s:
                    self.delta_1 = .5

            # Player 2
            if event.type == pyg.KEYUP:  # Move release
                if event.key == pyg.K_UP and self.delta_2 < 0:
                    self.delta_2 = 0
                elif event.key == pyg.K_DOWN and self.delta_2 > 0:
                    self.delta_2 = 0
            elif event.type == pyg.KEYDOWN:  # Move begin
                if event.key == pyg.K_UP:
                    self.delta_2 = -.5
                elif event.key == pyg.K_DOWN:
                    self.delta_2 = .5

            if event.type == pyg.KEYDOWN and event.key == pyg.K_r:  # Restart
                self.sentinel = False
                self.score_1 = self.score_2 = 0

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
            print(self.delta_factor)

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
        elif self.ball_x > self.screen_x + self.size_x:
            self.score_1 += 1
            self.sentinel = False
            self.clock.tick(3)

        # Borders
        if self.ball_y <= self.size_y or self.ball_y >= self.screen_y - 2 * self.size_y:
            self.ball_delta_y = -self.ball_delta_y

    def step(self, tick=200):
        """ Process one step of the game. """
        self.process_input()
        self.move_paddles()
        self.move_ball()
        self.display()
        pyg.display.update()
        self.clock.tick(tick)


if __name__ == "__main__":
    score_1 = score_2 = 0
    while True:
        game = Pong()
        game.score_1, game.score_2 = score_1, score_2
        while game.sentinel:
            game.step()
            score_1, score_2 = game.score_1, game.score_2
