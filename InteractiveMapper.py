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
import plotly.figure_factory as ff

print("reading gribs")
file = netCDF4.Dataset('http://nomads.ncep.noaa.gov:80/dods/gfs_0p25/gfs20200914/gfs_0p25_00z')
raw_lat = np.array(file.variables['lat'][:])
raw_lon = np.array(file.variables['lon'][:])
raw_wind = np.array(file.variables['gustsfc'][1, :, :])
raw_wind_u = np.array(file.variables['ugrd10m'][1,:,:])
raw_wind_v = np.array(file.variables['vgrd10m'][1,:,:])
file.close()
print("done reading gribs")

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
wind_u = raw_wind_u[min_row:max_row+1, min_col:max_col+1]
wind_v = raw_wind_v[min_row:max_row+1, min_col:max_col+1]

# wind_angle = np.zeros([len(wind), len(wind[0])])

# for i in range(0, len(wind_u)):
#     for j in range (0, len(wind_v)):
#         wind_angle[i][j] = 180 + math.degrees(math.atan2(raw_wind_u[i][j], raw_wind_v[i][j]))

# dead_wind = wind*1
#
# dead_min_row = 65
# dead_max_row = 90
# dead_min_col = 110
# dead_max_col = 115
#
# dead_wind[dead_min_row:dead_max_row, dead_min_col:dead_max_col] = 0.1
#
# dead_min_row = 85
# dead_max_row = 105
# dead_min_col = 125
# dead_max_col = 130
#
# dead_wind[dead_min_row:dead_max_row, dead_min_col:dead_max_col] = 0.1
#
# wind = dead_wind

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

route_file = './output/FinalRoutes/route_lr0.5_er0.8_r10000_gamma0.95_0914.csv'
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

print("plotting!!")

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
        color = weather_df.wind,
        showscale = True)))


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

# x, y = np.meshgrid(lon,lat)
#
# f = ff.create_quiver(x, y, wind_u, wind_v)
# f.show()

# To be able to see the plot while using pycharm
# fig.write_image('C:/Users/user/Desktop/test.png')
fig.show()