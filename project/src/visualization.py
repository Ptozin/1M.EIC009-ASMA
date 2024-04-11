# app.py

from dash import Dash, html
from dash import dcc
import plotly.express as px
import pandas as pd

def read_data_from_file(file : str) -> pd.DataFrame:
    warehouse : pd = pd.read_csv('data/small/' + file, sep=';')
    warehouse['latitude'] = warehouse['latitude'].str.replace(',', '.').astype(float)
    warehouse['longitude'] = warehouse['longitude'].str.replace(',', '.').astype(float)

    return warehouse

def plot_centers_and_orders(files = ["delivery_center1.csv", "delivery_center2.csv"]):
    fig = px.scatter_geo()
    for file in files:
        data = read_data_from_file(file)
        center = data.iloc[0]
        orders = data.iloc[1:]
        
        # Create a DataFrame just for the center
        center_df = pd.DataFrame([center])
        
        # Add the center as a red dot with fixed size
        center_dot = px.scatter_geo(center_df, lat='latitude', lon='longitude', color_discrete_sequence=['red'], size=[20], text='id')
        fig.add_trace(center_dot.data[0])

        # Add the orders as dots with size proportional to the weight
        order_dots = px.scatter_geo(orders, lat='latitude', lon='longitude', projection="orthographic", size='weight', opacity=0.3, text='id')
        for dot in order_dots.data:
            fig.add_trace(dot)


        
    fig.update_layout(height=500, margin={"r":0,"t":0,"l":0,"b":0})
    return fig

app = Dash(__name__)

fig = plot_centers_and_orders()

app.layout = html.Div([
    html.H1('Armazon Delivery Simulation'),
    html.Div(id='lat-long-text'),
    dcc.Graph(id='map', figure=fig)
]) 

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
