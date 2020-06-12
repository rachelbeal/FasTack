import numpy as np
import pygrib
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import netCDF4
import pandas as pd

file = netCDF4.Dataset('https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25_1hr/gfs20200611/gfs_0p25_1hr_00z')
raw_lat = np.array(file.variables['lat'][:])
raw_lon = np.array(file.variables['lon'][:])
raw_wind = np.array(file.variables['gustsfc'][1, :, :])
file.close()

min_lat = 0
max_lat = 50
min_lon = 180
max_lon = 242

lat_to_use = np.argwhere((raw_lat >= min_lat) & (raw_lat <= max_lat))
min_row = int(lat_to_use[0])
max_row = int(lat_to_use[-1])

lon_to_use = np.argwhere((raw_lon >= min_lon) & (raw_lon <= max_lon))
min_col = int(lon_to_use[0])
max_col = int(lon_to_use[-1])

lat = raw_lat[lat_to_use].reshape(len(lat_to_use))
lon = raw_lon[lon_to_use].reshape(len(lon_to_use))

wind = raw_wind[min_row:max_row + 1, min_col:max_col + 1]

lat_start = 33.75
lon_start = 241.75
start_i = int(np.argwhere(lat == lat_start))
start_j = int(np.argwhere(lon == lon_start))

lat_fin = 21.25
lon_fin = 360 - 157.75
fin_i = int(np.argwhere(lat == lat_fin))
fin_j = int(np.argwhere(lon == lon_fin))

#dead_min_row = 100
#dead_max_row = 190
#dead_min_col = 170
#dead_max_col = 190

#dead_wind = wind

#dead_wind[dead_min_row:dead_max_row, dead_min_col:dead_max_col] = 0.1

#wind = dead_wind

# global variables
BOARD_ROWS = len(wind)
BOARD_COLS = len(wind[0])
WIN_LOC = (fin_i, fin_j)
# LOSE_STATE = (1, 3)
START = (start_i, start_j, wind[start_i][start_j])
DETERMINISTIC = True


class State:
    def __init__(self, state=START):
        self.board = np.zeros([BOARD_ROWS, BOARD_COLS])
        self.state = state
        self.isEnd = False
        self.determine = DETERMINISTIC
        self.reward = 100000

    def giveReward(self):
        if (self.state[0], self.state[1]) == WIN_LOC:
            return self.reward
        else:
            return 0

    def isEndFunc(self):
        if (self.state[0], self.state[1]) == WIN_LOC:
            self.isEnd = True

    def nxtPosition(self, action):
        """
        action: up, down, left, right
        -------------
        0 | 1 | 2| 3|
        1 |
        2 |
        return next position
        """
        if self.determine:
            if action == "up":
                nxtPos = (self.state[0] - 1, self.state[1])
            elif action == "down":
                nxtPos = (self.state[0] + 1, self.state[1])
            elif action == "left":
                nxtPos = (self.state[0], self.state[1] - 1)
            else:
                nxtPos = (self.state[0], self.state[1] + 1)
            # if next state legal
            if (nxtPos[0] >= 0) and (nxtPos[0] <= (BOARD_ROWS - 1)):
                if (nxtPos[1] >= 0) and (nxtPos[1] <= (BOARD_COLS - 1)):
                    nxtState = (nxtPos[0], nxtPos[1], wind[nxtPos[0]][nxtPos[1]])
                    return nxtState
            return self.state

    def showBoard(self):
        self.board[self.state] = 1
        for i in range(0, BOARD_ROWS):
            print('-----------------')
            out = '| '
            for j in range(0, BOARD_COLS):
                if self.board[i, j] == 1:
                    token = '*'
                if self.board[i, j] == -1:
                    token = 'z'
                if self.board[i, j] == 0:
                    token = '0'
                out += token + ' | '
            print(out)
        print('-----------------')


# Agent of player

class Agent:

    def __init__(self, lr, exp_rate, exp_decay=False):
        self.states = []
        self.actions = ["down", "up", "right", "left"]
        self.State = State()
        self.lr = lr
        self.trainlr = lr
        self.exp_rate = exp_rate
        self.trainexp_rate = exp_rate
        self.rounds = None
        self.trainingrounds = None
        self.windPenalty = 0
        self.route = []
        self.record = False
        self.steps = 0
        self.time = 0
        self.best_time = float("inf")
        self.exp_decay = exp_decay

        # initial state reward
        self.state_values = {}
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                self.state_values[(i, j, wind[i][j])] = 0  # set initial value to 0

    def chooseAction(self):
        # choose action with most expected value
        mx_nxt_reward = 0
        action = ""
        self.steps = self.steps + 1
        self.windPenalty = self.windPenalty + (self.State.state[2] - wind.max())
        self.time = self.time + (1 / self.State.state[2]) * 0.25

        if np.random.uniform(0, 1) <= self.exp_rate:
            action = np.random.choice(self.actions)
        else:
            # greedy action
            for a in self.actions:
                # if the action is deterministic
                nxt_reward = self.state_values[self.State.nxtPosition(a)]
                if nxt_reward >= mx_nxt_reward:
                    action = a
                    mx_nxt_reward = nxt_reward
            if mx_nxt_reward == 0:
                action = np.random.choice(self.actions)
        if self.record == True:
            self.route.append(self.State.state)
        return action

    def takeAction(self, action):
        position = self.State.nxtPosition(action)
        return State(state=position)

    def reset(self):
        self.states = []
        self.State = State()
        self.windPenalty = 0
        self.steps = 0
        self.time = 0

    def play(self, rounds=10, verbose=False):
        self.rounds = rounds
        if rounds > 1:
            self.trainingrounds = rounds
        i = 0
        while i < rounds:
            # to the end of game back propagate reward
            if self.State.isEnd:
                # back propagate
                # reward = self.State.giveReward() + self.windPenalty / 100
                reward = self.State.giveReward() - min(self.time * 10, self.State.reward - 10)
                reward = max(0, reward)
                # reward = self.State.giveReward()
                # explicitly assign end state to reward values
                self.state_values[self.State.state] = reward  # this is optional
                print(' ')
                print('----------------------------------')
                print('ROUND: {}'.format(i))
                print('----------------------------------\n')
                print("Game End Reward", reward)
                for s in reversed(self.states):
                    reward = self.state_values[s] + self.lr * (reward - self.state_values[s])
                    self.state_values[s] = reward
                self.best_time = min(self.best_time, self.time)
                print("Best Time: ", self.best_time / 24)
                print("Steps: ", self.steps)
                print("Time: ", self.time / 24)
                self.reset()
                i += 1
                if self.exp_decay:
                    self.exp_rate = self.exp_rate / (i/100.0)
            else:
                action = self.chooseAction()
                # append trace
                # if self.State.nxtPosition(action) not in self.states:
                self.states.append(self.State.nxtPosition(action))
                if verbose:
                    print("current position {} action {}".format(self.State.state, action))
                # by taking the action, it reaches the next state
                self.State = self.takeAction(action)
                # mark is end
                self.State.isEndFunc()
                if self.steps >= 500000 and self.best_time != float("inf"):
                    self.State.isEnd = True
                if verbose:
                    print("nxt state", self.State.state)
                    print("---------------------")

    def showRoute(self):
        print("Showing Route")
        self.lr = 0
        self.exp_rate = 0.2
        self.record = True
        self.play(1)
        grid = np.zeros([BOARD_ROWS, BOARD_COLS])
        for s, route_tuple in enumerate(self.route):
            i = route_tuple[0]
            j = route_tuple[1]
            grid[i][j] = s
        df = pd.DataFrame(grid)
        df.to_csv("./output/route_lr{}_er{}_r{}.csv".format(self.trainlr, self.trainexp_rate, self.trainingrounds),
                  index=False)

    def showValues(self):
        for i in range(0, BOARD_ROWS):
            print('----------------------------------')
            out = '| '
            for j in range(0, BOARD_COLS):
                out += str(self.state_values[(i, j)]).ljust(6) + ' | '
            print(out)
        print('----------------------------------')

    def saveValues(self):
        df = pd.Series(ag.state_values).reset_index()
        df.columns = ['i', 'j', 'wind', 'value']
        df.to_csv("./output/state_values_lr{}_er{}_r{}_te05.csv".format(self.lr, self.exp_rate, self.rounds),
                  index=False)
        return


if __name__ == "__main__":
    lr_list = [0.7]
    exp_rate_list = [0.6]
    for lr in lr_list:
        for exp_rate in exp_rate_list:
            ag = Agent(lr, exp_rate)
            print(start_i)
            print(start_j)
            ag.play(500)
            # print(ag.showValues())
            ag.saveValues()
            print("Values are saved")
            ag.showRoute()
            print("Showing route")
