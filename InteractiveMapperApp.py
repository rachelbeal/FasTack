import plotly.graph_objects as go  # or plotly.express as px
from InteractiveMapper import fig
import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig, id='sail-routes')
])

app.run_server(host="0.0.0.0", port=8050, ssl_context=(
'/etc/letsencrypt/live/fastack.app/fullchain.pem', '/etc/letsencrypt/live/fastack.app/privkey.pem'))
