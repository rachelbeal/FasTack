import plotly.express as px
import pandas as pd
import numpy as np
import pygrib
import matplotlib.pyplot as plt
import netCDF4
import plotly.graph_objects as go

file = netCDF4.Dataset('https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25_1hr/gfs20200531/gfs_0p25_1hr_00z')
raw_lat  = np.array(file.variables['lat'][:])
raw_lon  = np.array(file.variables['lon'][:])
raw_wind = np.array(file.variables['gustsfc'][1,:,:])
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

wind = raw_wind[min_row:max_row+1, min_col:max_col+1]

BOARD_ROWS = len(wind)
BOARD_COLS = len(wind[0])

board = np.zeros([BOARD_ROWS, BOARD_COLS])

#racemap = np.zeros([BOARD_ROWS, BOARD_COLS])
visited = []
racemap = []

route_file = '/Users/rachelbeal/PycharmProjects/FasTack/route_lr0.9_er0.6_r200.csv'
route = pd.read_csv(route_file)

for i in range(0, len(route)-1):
    for j in range(0, len(route.values[0])-1):
        if route.values[i][j] > 0:
            lati = lat[i]
            lonj = lon[j]
            val = route.values[i][j]
            racemap.append((lati,lonj, val))

racemap_df = pd.DataFrame(racemap, columns = ["lat", "lon", "val"])

fig = go.Figure()

srd = racemap_df.sort_values(by = "val", ascending=True).reset_index(drop=True)

frames = list()
lon_data = [srd.lon[0]]
lat_data = [srd.lat[0]]

for i in range(len(srd.lon)):
    if i % 10 == 0:
        frames.append(
            go.Frame(data=[go.Scattergeo(lon=lon_data, lat=lat_data)])
        )
        lon_data.append(srd.lon[i])
        lat_data.append(srd.lat[i])

lon_data.append(srd.lon[i])
lat_data.append(srd.lat[i])
frames.append(go.Frame(data=[go.Scattergeo(lon=lon_data, lat=lat_data)]))

fig = go.Figure(
    data=[go.Scattergeo(
        locationmode= 'ISO-3', mode = "lines",
        lon=[racemap_df.lon[0], racemap_df.lon[0]],
        lat=[racemap_df.lat[0], racemap_df.lat[0]])],
    layout=go.Layout(
        xaxis=dict(range=[0, 5], autorange=False),
        yaxis=dict(range=[0, 5], autorange=False),
        title="FasTack Route Planner",
        updatemenus=[dict(
            type="buttons",
            buttons=[dict(label="Route",
                          method="animate",
                          args=[None])])]
    ),
    frames = frames
)

fig.show()
