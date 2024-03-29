# app.py

from dash import Dash, html
from dash import dcc
import plotly.express as px
import pandas as pd

def read_data() -> pd.DataFrame:
    """
    data format:
    
    `id;latitude;longitude;weight`
    
    e.g.:
    
    `order_1;37,7749;-122,4194;100`
    """
    warehouse : pd = pd.read_csv('data/delivery_center1.csv', delimiter=';')
    warehouse['latitude'] = warehouse['latitude'].str.replace(',', '.').astype(float)
    warehouse['longitude'] = warehouse['longitude'].str.replace(',', '.').astype(float)

    return warehouse

app = Dash(__name__)

data = read_data()
center = data.iloc[0]
orders = data.iloc[1:]

# This makes the actual map
fig = px.scatter_geo(orders, lat='latitude', lon='longitude', projection="orthographic", size='weight', opacity=0.3, text='id')

# Create a DataFrame just for the center
center_df = pd.DataFrame([center])

# Add the center as a red dot with fixed size
center_dot = px.scatter_geo(center_df, lat='latitude', lon='longitude', color_discrete_sequence=['red'], size=[20], text='id')
fig.add_trace(center_dot.data[0])

fig.update_layout(height=500, margin={"r":0,"t":0,"l":0,"b":0})


app.layout = html.Div([
    html.H1('Armazon Delivery Simulation'),
    html.Div(id='lat-long-text'),
    dcc.Graph(id='map', figure=fig)
]) 

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
