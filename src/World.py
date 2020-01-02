from Tkinter import *
from PIL import ImageTk
from PIL import Image
import numpy as np
import time

thing = {"EMPTY": 0, "ALFRED": 1, "OBSTACLE": 2, "CAT": 3, "CHEESE": 4}
movement = {"w": 0, "a": 1, "s": 2, "d": 3}
gamma = 0.2
walking_reward = -0.1

OBSTACLE_REWARD = -1
CAT_REWARD = -100
CHEESE_REWARD = 100


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

        self.alfred = None

        square_width = canvas.winfo_reqwidth() / width
        square_height = canvas.winfo_reqheight() / height

        img = Image.open("../resource/rat.png")
        self.alfred_image = ImageTk.PhotoImage(img.resize((square_width, square_height), Image.ANTIALIAS))
        img = Image.open("../resource/cat.png")
        self.cat_image = ImageTk.PhotoImage(img.resize((square_width, square_height), Image.ANTIALIAS))
        img = Image.open("../resource/cheese.png")
        self.cheese_image = ImageTk.PhotoImage(img.resize((square_width, square_height), Image.ANTIALIAS))

        self.area = np.zeros((width, height))
        self.r_matrix = np.zeros((width + height * width, 4))
        self.q_matrix = np.zeros((width + height * width, 4))

        self.canvas = canvas
        self.area[self.player.x][self.player.y] = thing["ALFRED"]

    def draw(self, canvas):
        canvas_width, canvas_height = canvas.winfo_reqwidth(), canvas.winfo_reqheight()
        dx, dy = (canvas_width / self.width), (canvas_height / self.height)

        self.alfred = canvas.create_image(dx * self.player.x, dy * self.player.y, image=self.alfred_image, anchor="nw")

        for obstacle in self.obstacles:
            x = dx * obstacle.x
            y = dy * obstacle.y
            canvas.create_rectangle(x, y, x + dx, y + dy, fill="gray")

        for cat in self.cats:
            x = dx * cat.x
            y = dy * cat.y
            canvas.create_image(x, y, image=self.cat_image, anchor="nw")

        for cheese in self.cheeses:
            x = dx * cheese.x
            y = dy * cheese.y
            canvas.create_image(x, y, image=self.cheese_image, anchor="nw")

    def add_obstacle(self, x, y):
        self.obstacles.append(Position(x, y))
        self.area[x][y] = thing["OBSTACLE"]
        self.set_reward_to_block(x, y, OBSTACLE_REWARD)

    def add_cat(self, x, y):
        self.cats.append(Position(x, y))
        self.area[x][y] = thing["CAT"]
        self.set_reward_to_block(x, y, CAT_REWARD)

    def add_cheese(self, x, y):
        self.cheeses.append(Position(x, y))
        self.area[x][y] = thing["CHEESE"]
        self.set_reward_to_block(x, y, CHEESE_REWARD)

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

    def move_to(self, action, canvas):
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

        square_width = canvas.winfo_reqwidth() / self.width
        square_height = canvas.winfo_reqheight() / self.height

        canvas.coords(self.alfred, self.player.x * square_width, self.player.y * square_height)

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

        self.canvas = Canvas(self.master, width=480, height=480, bg="white")
        self.canvas.grid(row=0, column=0)
        self.canvas.pack()

        self.map = Map(width, height, self.canvas)

    def start(self):
        self.master.mainloop()

    def run(self):
        self.map.draw(self.canvas)
        while 1:
            state_now = self.map.get_state_from_position(self.map.player.x, self.map.player.y)
            best_state_action = self.map.best_action(state_now)
            self.map.move_to(best_state_action, self.canvas)
            time.sleep(1)


