from Tkinter import *
import numpy as np
import threading
import time

thing = {"EMPTY": 0, "ALFRED": 1, "OBSTACLE": 2, "CAT": 3, "CHEESE": 4}
movement = {"w": 0, "a": 1, "s": 2, "d": 3}
gamma = 0.5
walking_reward = -1


class Position:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class Map:
    def __init__(self, width, height, canvas):
        self.width = width
        self.height = height
        self.player = Position(0, 0)
        self.obstacles = []
        self.cats = []
        self.cheeses = []

        self.area = np.zeros((width, height))
        self.r_matrix = np.zeros((width + height * width, 4))
        self.q_matrix = np.zeros((width + height * width, 4))

        self.canvas = canvas
        self.area[self.player.x][self.player.y] = thing["ALFRED"]

    def draw_me(self, canvas):
        canvas.delete("all")
        canvas_width, canvas_height = canvas.winfo_reqwidth(), canvas.winfo_reqheight()
        dx, dy = (canvas_width / self.width), (canvas_height / self.height)

        canvas.create_rectangle(dx * self.player.x, dy * self.player.y, dx * self.player.x + dx, dy * self.player.y + dy, fill="red")

        for obstacle in self.obstacles:
            canvas.create_rectangle(dx * obstacle.x, dy * obstacle.y, dx * obstacle.x + dx, dy * obstacle.y + dy, fill="gray")

        for cat in self.cats:
            canvas.create_rectangle(dx * cat.x, dy * cat.y, dx * cat.x + dx, dy * cat.y + dy, fill="black")

        for cheese in self.cheeses:
            canvas.create_rectangle(dx * cheese.x, dy * cheese.y, dx * cheese.x + dx, dy * cheese.y + dy, fill="green")

    def add_obstacle(self, x, y):
        self.obstacles.append(Position(x, y))
        self.area[x][y] = thing["OBSTACLE"]
        self.set_reward_to_block(x, y, -10)

    def add_cat(self, x, y):
        self.cats.append(Position(x, y))
        self.area[x][y] = thing["CAT"]
        self.set_reward_to_block(x, y, -100)

    def add_cheese(self, x, y):
        self.cheeses.append(Position(x, y))
        self.area[x][y] = thing["CHEESE"]
        self.set_reward_to_block(x, y, 100)

    def can_move(self, action):
        new_position = [0, 0]
        if action == 0:
            new_position = [self.player.x, self.player.y - 1]
        elif action == 1:
            new_position = [self.player.x - 1, self.player.y]
        elif action == 2:
            new_position = [self.player.x, self.player.y + 1]
        elif action == 3:
            new_position = [self.player.x + 1, self.player.y]
        else:
            return False

        if new_position[0] < 0 or new_position[0] >= self.width or new_position[1] < 0 or new_position[1] >= self.height:
            return False
        if self.area[new_position[0]][new_position[1]] != thing["OBSTACLE"]:
            return True
        else:
            return False

    def move_to(self, action):
        state_now = self.player.x + self.width * self.player.y
        self.q_matrix[state_now][action] = self.calculate_q_new(state_now, action)

        if action == 0 and self.can_move(0):
            self.area[self.player.x][self.player.y] = thing["EMPTY"]
            self.player.y -= 1
        elif action == 1 and self.can_move(1):
            self.area[self.player.x][self.player.y] = thing["EMPTY"]
            self.player.x -= 1
        elif action == 2 and self.can_move(2):
            self.area[self.player.x][self.player.y] = thing["EMPTY"]
            self.player.y += 1
        elif action == 3 and self.can_move(3):
            self.area[self.player.x][self.player.y] = thing["EMPTY"]
            self.player.x += 1

        if self.area[self.player.x][self.player.y] == thing["CAT"]:
            self.player.x = 0
            self.player.y = 0
        elif self.area[self.player.x][self.player.y] == thing["CHEESE"]:
            self.player.x = 0
            self.player.y = 0

        self.area[self.player.x][self.player.y] = thing["ALFRED"]

    def calculate_q_new(self, state, action):
        next_state = self.get_next_state(state, action)
        return self.r_matrix[state][action] + gamma * self.max_q(next_state) + walking_reward

    def max_q(self, state):
        return max(self.q_matrix[state][0], self.q_matrix[state][1], self.q_matrix[state][2], self.q_matrix[state][3])

    def best_action(self, state):
        action_max = -1
        q_value = -1000
        for action in range(4):
            if q_value < self.q_matrix[state][action]:
                action_max = action
                q_value = self.q_matrix[state][action]

        return action_max

    def get_state_from_position(self, x, y):
        return x + y * self.width

    def get_next_state(self, state, action):
        if self.can_move(action):
            if action == 0:
                return state - self.width
            elif action == 1:
                return state - 1
            elif action == 2:
                return state + self.width
            elif action == 3:
                return state + 1
        else:
            return state

    def set_reward_to_block(self, x, y, r):
        if x > 0:
            self.r_matrix[x + y * self.width - 1][3] = r
        if x < self.width - 1:
            self.r_matrix[x + y * self.width + 1][1] = r
        if y > 0:
            self.r_matrix[x + (y - 1) * self.width][2] = r
        if y < self.height - 1:
            self.r_matrix[x + (y + 1) * self.width][0] = r


class World:
    def __init__(self, width, height):
        self.master = Tk()
        self.master.wm_title("Alfred the Rat")
        self.canvas = Canvas(self.master, width=480, height=480)
        self.canvas.grid(row=0, column=0)
        self.canvas.pack()

        self.map = Map(width, height, self.canvas)

    def start(self):
        self.master.mainloop()

    def run(self):
        while 1:
            self.map.move_to(self.map.best_action(self.map.get_state_from_position(self.map.player.x, self.map.player.y)))
            self.map.draw_me(self.canvas)
            time.sleep(0.1)


