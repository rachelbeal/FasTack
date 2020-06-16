import numpy as np
import netCDF4
import pandas as pd
import math

TIMEPENALTY = 2000

print("reading gribs")
file = netCDF4.Dataset('https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25_1hr/gfs20200614/gfs_0p25_1hr_00z')
raw_lat = np.array(file.variables['lat'][:])
raw_lon = np.array(file.variables['lon'][:])
print("still reading gribs")
raw_wind = np.array(file.variables['gustsfc'][1, :, :])
raw_wind_u = np.array(file.variables['ugrd10m'][1,:,:])
raw_wind_v = np.array(file.variables['vgrd10m'][1,:,:])
file.close()
print("done reading gribs!")

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
wind_u = raw_wind_u[min_row:max_row+1, min_col:max_col+1]
wind_v = raw_wind_v[min_row:max_row+1, min_col:max_col+1]

wind_angle = np.zeros([len(wind), len(wind[0])])

for i in range(0, len(wind_u)):
    for j in range (0, len(wind_v)):
        wind_angle[i][j] = 180 + math.degrees(math.atan2(raw_wind_u[i][j], raw_wind_v[i][j]))

lat_start = 33.75
lon_start = 241.75

start_i = int(np.argwhere(lat == lat_start))
start_j = int(np.argwhere(lon == lon_start))

lat_fin = 21.25
lon_fin = 360 - 157.75
fin_i = int(np.argwhere(lat == lat_fin))
fin_j = int(np.argwhere(lon == lon_fin))

# dead_wind = wind*1
#
# dead_min_row = 65
# dead_max_row = 90
# dead_min_col = 110
# dead_max_col = 115
#
# dead_wind[dead_min_row:dead_max_row, dead_min_col:dead_max_col] = 0.001
#
# dead_min_row = 85
# dead_max_row = 105
# dead_min_col = 125
# dead_max_col = 130
#
# dead_wind[dead_min_row:dead_max_row, dead_min_col:dead_max_col] = 0.1
#
# wind = dead_wind

# global variables
BOARD_ROWS = len(wind)
BOARD_COLS = len(wind[0])
WIN_LOC = (fin_i, fin_j)
# LOSE_STATE = (1, 3)
START = (start_i, start_j, wind[start_i][start_j])
DETERMINISTIC = True

tab_times = []
tab_lr = []
tab_exp_rate = []
tab_rounds = []
tab_decay_gamma = []
tab_steps = []


class State:
    def __init__(self, state=START):
        self.board = np.zeros([BOARD_ROWS, BOARD_COLS])
        self.state = state
        self.isEnd = False
        self.determine = DETERMINISTIC
        self.reward = 1000000
        self.boat_dir = 0
        self.angle_off_wind = 0
        self.boat_speed = 0

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
        action: north, south, east, west, northeast, northwest, southeast, southwest
        -------------
        0 | 1 | 2| 3|
        1 |
        2 |
        return next position on board
        """

        if action == "north":
            nxtPos = (self.state[0] - 1, self.state[1])
        elif action == "northeast":
            nxtPos = (self.state[0] - 1, self.state[1] + 1)
        elif action == "northwest":
            nxtPos = (self.state[0] - 1, self.state[1] - 1)
        elif action == "south":
            nxtPos = (self.state[0] + 1, self.state[1])
        elif action == "southeast":
            nxtPos = (self.state[0] + 1, self.state[1] + 1)
        elif action == "southwest":
            nxtPos = (self.state[0] + 1, self.state[1] - 1)
        elif action == "west":
            nxtPos = (self.state[0], self.state[1] - 1)
        else:
            nxtPos = (self.state[0], self.state[1] + 1)

        if (nxtPos[0] >= 0) and (nxtPos[0] <= (BOARD_ROWS - 1)):
            if (nxtPos[1] >= 0) and (nxtPos[1] <= (BOARD_COLS - 1)):
                if action == "north":
                    self.boat_dir = 90
                elif action == "northeast":
                    self.boat_dir = 45
                elif action == "northwest":
                    self.boat_dir = 135
                elif action == "south":
                    self.boat_dir = 270
                elif action == "southeast":
                    self.boat_dir = 315
                elif action == "southwest":
                    self.boat_dir = 225
                elif action == "west":
                    self.boat_dir = 180
                else:
                    self.boat_dir = 0

                boati = nxtPos[0]
                boatj = nxtPos[1]
                # wind_speed = nxtPos[2]

                self.angle_off_wind = self.boat_dir - wind_angle[boati][boatj]

                if self.angle_off_wind <= -180:
                    self.angle_off_wind = self.angle_off_wind + 360

                if -180 < self.angle_off_wind < 0:
                    self.angle_off_wind = self.angle_off_wind + 180

                if self.angle_off_wind > 180:
                    self.angle_off_wind = self.angle_off_wind - 180

                # if self.angle_off_wind < 45:
                    # self.boat_speed = 0.001
                # else:
                    # self.boat_speed = wind_speed

                # self.time = self.time + (1 / self.boat_speed) * 0.25
                if self.angle_off_wind >= 45:
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


class Agent:

    def __init__(self, lr, exp_rate):
        self.states = []  # record position and action taken at the position
        self.actions = ["north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"]
        self.State = State()
        self.isEnd = self.State.isEnd
        self.reward = 0
        # self.lr = 0.7
        # self.exp_rate = 0.6
        # self.decay_gamma = 0.9

        self.lr = lr
        self.trainlr = lr
        self.exp_rate = exp_rate
        self.trainexp_rate = exp_rate
        self.decay_gamma = decay_gamma
        self.rounds = None
        self.trainingrounds = None
        self.windPenalty = 0
        self.route = []
        self.record = False
        self.steps = 0
        self.time = 0
        self.best_time = float("inf")

        # initial Q values
        self.Q_values = {}
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                self.Q_values[(i, j, wind[i][j])] = {}
                for a in self.actions:
                    self.Q_values[(i, j, wind[i][j])][a] = 0  # Q value is a dict of dict

    def chooseAction(self):
        # choose action with most expected value
        mx_nxt_reward = 0
        action = ""

        if np.random.uniform(0, 1) <= self.exp_rate:
            # print("Random")
            action = np.random.choice(self.actions)
        else:
            # greedy action
            for a in self.actions:
                current_position = self.State.state
                nxt_reward = self.Q_values[current_position][a]
                if nxt_reward >= mx_nxt_reward:
                    action = a
                    mx_nxt_reward = nxt_reward
            if mx_nxt_reward == 0:
                action = np.random.choice(self.actions)
            # print("current pos: {}, greedy action: {}".format(self.State.state, action))
        if self.record:
            self.route.append(self.State.state)

        return action

    def takeAction(self, action):
        old_position =  self.State.state
        position = self.State.nxtPosition(action)
        self.boat_speed = position[2]
        if old_position != position:
            self.time = self.time + (1 / self.boat_speed) * 0.25
            self.steps = self.steps + 1
        # update State
        return State(state=position)

    def reset(self):
        self.states = []
        self.State = State()
        self.isEnd = self.State.isEnd
        self.windPenalty = 0
        self.steps = 0
        self.time = 0
        self.reward = 0

    def play(self, rounds=10, verbose=False):
        self.rounds = rounds
        if rounds > 1:
            self.trainingrounds = rounds
        i = 0
        while i < rounds:
            # to the end of game back propagate reward
            if self.State.isEnd:
                # back propagate
                # reward = self.State.giveReward()
                reward = self.State.giveReward() - min(self.time * TIMEPENALTY, self.State.reward - 10)
                #  = self.State.giveReward() -  self.time * TIMEPENALTY
                reward = max(0, reward)
                for a in self.actions:
                    self.Q_values[self.State.state][a] = reward
                print(' ')
                print('----------------------------------')
                print('ROUND: {}'.format(i))
                print('----------------------------------\n')
                print("Game End Reward", reward)
                print("Total Reward", self.reward)
                for s in reversed(self.states):
                    current_q_value = self.Q_values[s[0]][s[1]]
                    reward = current_q_value + self.trainlr * (self.decay_gamma * reward - current_q_value)
                    self.Q_values[s[0]][s[1]] = reward
                self.best_time = min(self.best_time, self.time)
                print("Best Time: ", self.best_time / 24)
                print("Steps: ", self.steps)
                print("Time: ", self.time / 24)
                if self.record:
                    tab_times.append(self.time / 24)
                    tab_lr.append(self.trainlr)
                    tab_exp_rate.append(self.trainexp_rate)
                    tab_rounds.append(self.trainingrounds)
                    tab_decay_gamma.append(self.decay_gamma)
                    tab_steps.append(self.steps)
                self.reset()
                i += 1
            else:
                action = self.chooseAction()
                # append trace
                self.states.append([self.State.state, action])
                if verbose:
                    print("current position {} action {}".format(self.State.state, action))
                # by taking the action, it reaches the next state
                self.State = self.takeAction(action)
                # mark is end
                self.State.isEndFunc()

                # Give reward during training
                # s = self.State.state
                # current_q_value = self.Q_values[s][action]
                # reward_time = (250 - (1/self.boat_speed) * 0.25) * 0.001
                # reward = current_q_value + self.trainlr * (self.decay_gamma * reward_time - current_q_value)
                # self.reward += reward
                # self.Q_values[s][action] = reward

                if self.steps >= 500000 and self.best_time != float("inf"):
                    self.State.isEnd = True
                if verbose:
                    print("nxt state", self.State.state)
                    print("---------------------")
                self.isEnd = self.State.isEnd

    def showRoute(self):
        print("Showing Route")
        self.lr = 0
        self.exp_rate = 0.05
        self.record = True
        self.play(1)
        grid = np.zeros([BOARD_ROWS, BOARD_COLS])
        for s, route_tuple in enumerate(self.route):
            i = route_tuple[0]
            j = route_tuple[1]
            grid[i][j] = s
        df = pd.DataFrame(grid)
        df.to_csv("./output/wwinvec_parmtest/route_lr{}_er{}_r{}_gamma{}.csv".format(self.trainlr, self.trainexp_rate, self.trainingrounds, self.decay_gamma),
                  index=False)
        # tab_times.append(self.time / 24)
        # tab_lr.append(self.trainlr)
        # tab_exp_rate.append(self.trainexp_rate)
        # tab_rounds.append(self.trainingrounds)
        # tab_decay_gamma.append(self.decay_gamma)>



    def showValues(self):
        for i in range(0, BOARD_ROWS):
            print('----------------------------------')
            out = '| '
            for j in range(0, BOARD_COLS):
                out += str(self.Q_values[(i, j)]).ljust(6) + ' | '
            print(out)
        print('----------------------------------')

    def saveValues(self):
        df = pd.Series(ag.Q_values).reset_index()
        df.columns = ['i', 'j', 'wind', 'value']
        df.to_csv("./output/wwinvec_parmtest/Q_values_lr{}_er{}_r{}_gamma{}.csv".format(self.trainlr, self.trainexp_rate, self.rounds, self.decay_gamma),
                  index=False)
        return

    def saveTimes(self):
        dict = {'lr': tab_lr, 'exp_rate': tab_exp_rate, 'rounds': tab_rounds, 'gamma_decay': tab_decay_gamma, 'time': tab_times, 'steps': tab_steps}
        df = pd.DataFrame(dict)
        df.to_csv("./output/wwinvec_parmtest/times_r{}.csv".format(self.trainingrounds),
            index=False)
        return

if __name__ == "__main__":
    lr_list = [0.6]
    exp_rate_list = [0.9, 0.8, 0.7, 0.6]
    decay_gamma_list = [0.95]
    for lr in lr_list:
        for exp_rate in exp_rate_list:
            for decay_gamma in decay_gamma_list:
                ag = Agent(lr, exp_rate)
                print(start_i)
                print(start_j)
                # print("initial Q-values ... \n")
                # print(ag.Q_values)
                ag.play(1000, verbose=False)
                # print("latest Q-values ... \n")
                # print(ag.Q_values)
                ag.saveValues()
                print("Values are saved")
                ag.showRoute()
                print("Showing route")
    ag.saveTimes()



