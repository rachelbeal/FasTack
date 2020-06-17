import pandas as pd
import numpy as np
import pygrib
import matplotlib.pyplot as plt
import netCDF4
import math
import plotly
import plotly.express as px
import plotly.figure_factory as ff
import chart_studio.plotly as py
import plotly.offline as py_off
import plotly.graph_objs as go

file = netCDF4.Dataset('https://nomads.ncep.noaa.gov:9090/dods/gfs_0p25_1hr/gfs20200614/gfs_0p25_1hr_00z')
raw_lat  = np.array(file.variables['lat'][:])
raw_lon  = np.array(file.variables['lon'][:])
raw_wind = np.array(file.variables['gustsfc'][1,:,:])
file.close()

# set boundaries for race course
min_lat = 0
max_lat = 50
min_lon = 180
max_lon = 242

# apply boundaries
lat_to_use = np.argwhere((raw_lat >= min_lat) & (raw_lat <= max_lat))
min_row = int(lat_to_use[0])
max_row = int(lat_to_use[-1])

lon_to_use = np.argwhere((raw_lon >= min_lon) & (raw_lon <= max_lon))
min_col = int(lon_to_use[0])
max_col = int(lon_to_use[-1])

lat = raw_lat[lat_to_use].reshape(len(lat_to_use))
lon = raw_lon[lon_to_use].reshape(len(lon_to_use))

# filter weather data
wind = raw_wind[min_row:max_row+1, min_col:max_col+1]

def racemap(routefile):
    racemap = []
    route = pd.read_csv(routefile)
    for i in range(0, len(route)-1):
        for j in range(0, len(route.values[0])-1):
            if route.values[i][j] > 0:
                lati = lat[i]
                lonj = lon[j]
                val = route.values[i][j]
                racemap.append((lati,lonj, val))
    racemap_df = pd.DataFrame(racemap, columns = ["lat", "lon", "val"])
    return racemap_df

legs = ['/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0607.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0608.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0609.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0610.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0611.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0612.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0613.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0614.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0615.csv',
       '/Users/rachelbeal/PycharmProjects/FasTack/output/Timelapse/route_lr0.5_er0.8_r10000_gamma0.95_0616.csv']

legs_df = []

for i, filename in enumerate(legs):
    racemap_df = racemap(filename).sort_values(by = "val").reset_index(drop=True)
    leg = racemap_df[:15]
    leg["leg"] = i
    legs_df.append(leg)

all_legs = pd.concat(legs_df).reset_index(drop = True)

route_df = []

for i, filename in enumerate(legs):
    racemap_df = racemap(filename).sort_values(by = "val").reset_index(drop=True)
    leg = racemap_df
    leg["leg"] = i
    route_df.append(leg)

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

fig = go.Figure()

srd = all_legs

frames = list()
lon_data = [all_legs.lon[0]]
lat_data = [all_legs.lat[0]]

all_legs["leg"] = all_legs["leg"].astype(float)

for i in range(len(all_legs.lon)):
    if i % 5 == 0:
        frames.append(
            go.Frame(data=[go.Scattergeo(lon=lon_data,
                                         lat=lat_data,
                                         mode="markers",
                                         marker=dict(color=all_legs["leg"][::5],
                                                     cmin=0,
                                                     cmax=10,
                                                     colorscale="rainbow"
                                                     ))

                           ])
        )
        lon_data.append(all_legs.lon[i])
        lat_data.append(all_legs.lat[i])

lon_data.append(all_legs.lon[i])
lat_data.append(all_legs.lat[i])

frames.append(go.Frame(data=[go.Scattergeo(lon=lon_data, lat=lat_data)]))

fig = go.Figure(
    data=[go.Scattergeo(
        locationmode='ISO-3', mode="lines",
        lon=[all_legs.lon[0], all_legs.lon[0]],
        lat=[all_legs.lat[0], all_legs.lat[0]])],
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
    frames=frames
)

fig.update_layout(geo=dict(lonaxis=dict(
    showgrid=True,
    gridwidth=0.5,
    range=[min_lon + 10, max_lon + 30],
    dtick=1
),
    lataxis=dict(
        showgrid=True,
        gridwidth=0.5,
        range=[min_lat, max_lat],
        dtick=1
    )))

fig.show()
