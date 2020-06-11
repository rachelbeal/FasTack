import plotly.express as px
import pandas as pd
import numpy as np
import pygrib
import matplotlib.pyplot as plt
import netCDF4
import plotly
import chart_studio.plotly as py
import plotly.offline as py_off
import plotly.graph_objs as go

file = netCDF4.Dataset('https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25_1hr/gfs20200609/gfs_0p25_1hr_00z')
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

wind = raw_wind[min_row:max_row+1, min_col:max_col+1]

dead_min_row = 10
dead_max_row = 120
dead_min_col = 140
dead_max_col = 200

dead_wind = wind

dead_wind[dead_min_row:dead_max_row, dead_min_col:dead_max_col] = 0

wind = dead_wind

wlat = []
wlon = []
wwind = []

for i in range(0, len(wind)):
    for j in range(0, len(wind[0])):
        wlat.append(lat[i])
        wlon.append(lon[j])
        wwind.append(wind[i][j])

weather_data = {"lat": wlat, "lon": wlon, "wind": wwind}
weather_df = pd.DataFrame(data=weather_data)

BOARD_ROWS = len(wind)
BOARD_COLS = len(wind[0])

board = np.zeros([BOARD_ROWS, BOARD_COLS])

#racemap = np.zeros([BOARD_ROWS, BOARD_COLS])
visited = []
racemap = []

route_file = './output/route_lr0.9_er0.9_r1000.csv'
route = pd.read_csv(route_file)

for i in range(0, len(route)-1):
    for j in range(0, len(route.values[0])-1):
        if route.values[i][j] > 0:
            lati = lat[i]
            lonj = lon[j]
            val = route.values[i][j]
            racemap.append((lati,lonj, val))

racemap_df = pd.DataFrame(racemap, columns = ["lat", "lon", "val"])

mapbox_access_token = open("mapbox_key.txt").read()

fig = go.Figure()

fig.add_trace(go.Scattermapbox(
    lon=weather_df.lon,
    lat=weather_df.lat,
    mode='markers',
    text=weather_df.wind,
    marker=dict(
        size = 5,
        cmax = 20,
        cmin =0,
        opacity = 0.1,
        color = weather_df.wind)))


fig.add_trace(go.Scattermapbox(
    lon=racemap_df.lon,
    lat=racemap_df.lat))

fig.update_layout(
    autosize=True,
    margin=dict(t=0, b=0, l=0, r=0),
    mapbox={
        'center': {'lon': 200, 'lat': 25},
        'style': "open-street-map",
        'center': {'lon': 200, 'lat': 25},
        'zoom': 1,
        'accesstoken': mapbox_access_token
    })

fig.update_layout(geo=dict(lonaxis=dict(
    showgrid=True,
    gridwidth=1,
    range=[min_lon + 10, max_lon + 30],
    dtick=1
),
    lataxis=dict(
        showgrid=True,
        gridwidth=1,
        range=[min_lat, max_lat],
        dtick=1
    )))

# To be able to see the plot while using pycharm
# fig.write_image('C:/Users/user/Desktop/test.png')
#fig.show()