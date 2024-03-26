# app.py

from dash import Dash, html
from dash import dcc
import plotly.express as px
import pandas as pd

def get_coordinates() -> pd.DataFrame:
    warehouse_1 : pd = pd.read_csv('data/delivery_center1.csv', delimiter=';')
    # warehouse_2 : pd = pd.read_csv('data/delivery_center2.csv', delimiter=';')

    warehouse_1['latitude'] = warehouse_1['latitude'].str.replace(',', '.').astype(float)
    warehouse_1['longitude'] = warehouse_1['longitude'].str.replace(',', '.').astype(float)

    # warehouse_2['latitude'] = warehouse_1['latitude'].str.replace(',', '.').astype(float)
    # warehouse_2['longitude'] = warehouse_1['longitude'].str.replace(',', '.').astype(float)

    return warehouse_1[['latitude', 'longitude']]


app = Dash(__name__)

# This makes the actual map
fig = px.scatter_geo(get_coordinates(), lat='latitude', lon='longitude', projection="orthographic")
fig.update_layout(height=500, margin={"r":0,"t":0,"l":0,"b":0})


app.layout = html.Div([
    html.H1('Armazon Delivery Simulation'),
    html.Div(id='lat-long-text'),
    dcc.Graph(id='map', figure=fig)
]) 

if __name__ == '__main__':
    app.run_server(debug=True)