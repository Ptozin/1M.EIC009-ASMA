import json, pandas as pd
from misc.create_user import ProsodyClient

DATA_FOLDER : str = 'data/'
PROSODY_PASSWORD : str = ''

def create_agents(agents_uids : list[str]):
    """
    Creates users in prosody server if they don't exist already.
    WARNING: Only call it the first time you run the program.
    """
    global PROSODY_PASSWORD
    with open(DATA_FOLDER +'global_variables.json') as file:
        content : json = json.load(file)
        container_id : str = content['docker_container_id']
        prosody_password : str = content['prosody_password']
        PROSODY_PASSWORD = prosody_password

    with ProsodyClient(container_id) as prosody_client:
        for agent_uid in agents_uids:
            prosody_client.create_user(username=agent_uid, password=prosody_password)

def parse_delivery_drones(delivery_drones : pd.DataFrame) -> list[dict]:
    """
    Parse the delivery drones data.

    Args:
        delivery_drones (dict): A dictionary containing the delivery drones data.

    Returns:
        list[dict]: A list of dictionaries representing the parsed delivery drones data.
    """

    delivery_drones['id'] = delivery_drones['id'].astype(str)
    delivery_drones['jid'] = delivery_drones['id'] + '@localhost'
    delivery_drones['password'] = PROSODY_PASSWORD
    delivery_drones['capacity'] = delivery_drones['capacity'].str.strip('kg').astype(int)
    delivery_drones['autonomy'] = delivery_drones['autonomy'].str.strip('Km').astype(int) * 1_000
    delivery_drones['velocity'] = delivery_drones['velocity'].str.strip('m/s').astype(int)
    delivery_drones['initialPos'] = delivery_drones['initialPos'].astype(str)
    
    return delivery_drones.to_dict('records')

def parse_warehouses_and_orders(warehouse_and_orders : pd.DataFrame) -> list[dict]:
    """ 
    Parse the warehouses and orders data.
    
    Args:
        warehouses (pd.DataFrame): A pandas DataFrame containing the warehouses and orders data.
        
    Returns:
        list[dict]: A list of dictionaries representing the parsed warehouses and orders data.
    """

    # Set the first line (warehouse) id to be the prosody id
    warehouse_and_orders['id'] = warehouse_and_orders['id'].astype(str)
    warehouse_and_orders['latitude'] = warehouse_and_orders['latitude'].str.replace(',', '.').astype(float)
    warehouse_and_orders['longitude'] = warehouse_and_orders['longitude'].str.replace(',', '.').astype(float)
    
    warehouse = warehouse_and_orders.iloc[0:1, :]
    orders = warehouse_and_orders.iloc[1: , :]
    
    warehouse = warehouse.to_dict('records')[0]
    
    warehouse['jid'] = warehouse['id'] + '@localhost'
    warehouse['password'] = PROSODY_PASSWORD
    
    return warehouse, orders.to_dict('records')

def parse_data(isOriginalData : bool = True) -> tuple[list[dict], list[list]]:    

    if isOriginalData:
        folder = DATA_FOLDER + 'original/'
    else:
        folder = DATA_FOLDER + 'small/'
    
    # Read delivery drones agents
    delivery_drones_fields : pd.DataFrame = pd.read_csv(folder + 'delivery_drones.csv', delimiter=';')

    # Read warehouse agents
    warehouse_1_fields : pd.DataFrame = pd.read_csv(folder + 'delivery_center1.csv', delimiter=';')
    warehouse_2_fields : pd.DataFrame = pd.read_csv(folder + 'delivery_center2.csv', delimiter=';')
    
    # Retrieve agents uids for prosody
    agents_uids : list[str] = delivery_drones_fields['id'].to_list() \
        + [warehouse_1_fields['id'].head(1).values[0]] \
        + [warehouse_2_fields['id'].head(1).values[0]]
        
    # Create agents in prosody server
    create_agents(agents_uids)
    
    # Setup delivery drones
    delivery_drones : list[dict] = parse_delivery_drones(delivery_drones_fields)

    # Setup warehouses and orders
    warehouse_1 : list[dict] = parse_warehouses_and_orders(warehouse_1_fields)
    warehouse_2 : list[dict] = parse_warehouses_and_orders(warehouse_2_fields)
    
    warehouses : list[list] = [warehouse_1, warehouse_2]
    
    return delivery_drones, warehouses
    
    