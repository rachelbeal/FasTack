# FasTack Documentation

FasTack was completed as a project for the Insight Data Science Fellowship program (NY 2020B). 

FasTack finds the best route between start and end coordinates for sailing races based on wind conditions from GFS data. The code is currently set up to optimize the route used by the Transpacific Yacht Race between the Pt. Fermin buoy (33.70˚N, 118.29˚W) in San Pedro, CA and the Diamond Head buoy (21.25˚N, 157.81˚W) off the coast of Oahu, but could be adujsted for other race coordinates.

## Data Sources

National Oceanic and Atmospheric Association Global Forecasting System weather data is obtained from the [GrADS Data Server] (https://nomads.ncep.noaa.gov:9090/dods/). Several data sources are available on GrADS, but FasTrak utilizes GFS because it has higher granularity.

