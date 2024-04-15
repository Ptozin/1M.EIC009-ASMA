from flask_socketio import SocketIO
from typing import Dict, List
from flask import Flask, render_template
from random import uniform
import pandas as pd

def load_warehouse_data(file : str) -> pd.DataFrame:
    warehouse : pd = pd.read_csv('data/small/' + file, sep=';')
    warehouse['latitude'] = warehouse['latitude'].str.replace(',', '.').astype(float)
    warehouse['longitude'] = warehouse['longitude'].str.replace(',', '.').astype(float)

    return warehouse  

class WebApp:
    def __init__(self) -> None:
        pd.options.mode.chained_assignment = None 
        self.app : Flask = Flask(__name__, template_folder='./visualization/templates')
        self.socketio = SocketIO(self.app)
        
        self.debug = False
        self.use_reloader = False
        
        self.app.add_url_rule("/", "home", self.home)
        self.app.add_url_rule("/updated_data", "updated_data", self.randomizer)
        self.app.add_url_rule("/get_data", "new_data", self.get_data)
        
        self.data : List[Dict] = []
        
        self.plot_centers_and_orders()
        
        print('Setup Done...')
                
    def plot_centers_and_orders(self):
        files = ["delivery_center1.csv", "delivery_center2.csv"]
        
        for file in files:
            data = load_warehouse_data(file)
            center = pd.DataFrame([data.iloc[0]])
            orders = data.iloc[1:]

            center.loc[:, 'type'] = 'warehouse'
            orders.loc[:, 'status'] = False # AKA not delivered
            orders.loc[:, 'type'] = 'order'
            
            for order in orders.to_dict(orient='records'):
                self.data.append(order)
                
            for center in center.to_dict(orient='records'):
                self.data.append(center)
             
        
    def run(self) -> None:
        self.app.run(host="0.0.0.0", port=8050, debug=self.debug, use_reloader=self.use_reloader)
        
    def home(self) -> str:
        return(render_template('index.html'))
    
    def get_data(self) -> List[Dict]:
        return self.data
    
    def randomizer(self) -> List[Dict]:
        # creates random coordinates and publishes them to the map
        data = [
            {
                'id' : 1,
                'type' : 'drone',
                'latitude' : uniform(18.95, 19.0),
                'longitude' : uniform(72.5, 73.0)
            },
            {
                'id' : 2,
                'type' : 'drone',
                'latitude' : uniform(18.95, 19.0),
                'longitude' : uniform(72.5, 73.0)
            },
            {
                'id' : 3,
                'type' : 'drone',
                'status' : False,
                'latitude' : uniform(18.95, 19.0),
                'longitude' : uniform(72.5, 73.0)
            },
            {
                'id' : 4,
                'type' : 'order',
                'status' : True,
                'latitude' : 19,
                'longitude' : 73
            },
        ]
                
        return data
        
if __name__ == "__main__": 
    webApp = WebApp()
    webApp.debug = True
    webApp.use_reloader = True
    webApp.run()
