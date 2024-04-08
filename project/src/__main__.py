import json, pandas as pd
from misc.create_user import ProsodyClient
from logic import DeliveryLogic

def create_agents(agents_uids : list[str]):
    """
    Creates users in prosody server if they don't exist already.
    WARNING: Only call it the first time you run the program.
    """
    with open('data/global_variables.json') as file:
        content : json = json.load(file)
        container_id : str = content['docker_container_id']
        prosody_password : str = content['prosody_password']

    with ProsodyClient(container_id) as prosody_client:
        for agent_uid in agents_uids:
            prosody_client.create_user(username=agent_uid, password=prosody_password)

def parse_delivery_drones(delivery_drones) -> list[dict]:

    delivery_drones['capacity'] = delivery_drones['capacity'].str.strip('kg').astype(int)
    delivery_drones['autonomy'] = delivery_drones['autonomy'].str.strip('Km').astype(int) * 1_000
    delivery_drones['velocity'] = delivery_drones['velocity'].str.strip('m/s').astype(int)

    return delivery_drones.to_dict('records')

def parse_warehouses_and_orders(warehouses) -> list[dict]:

    warehouses['latitude'] = warehouses['latitude'].str.replace(',', '.').astype(float)
    warehouses['longitude'] = warehouses['longitude'].str.replace(',', '.').astype(float)

    return warehouses.head(1).to_dict('records')[0], warehouses.iloc[1: , :].to_dict('records')

def main() -> None:
    #try:
        # Read delivery drones agents
        delivery_drones_fields : pd = pd.read_csv('data/delivery_drones.csv', delimiter=';')

        # Read warehouse agents
        warehouse_1_fields : pd = pd.read_csv('data/delivery_center1.csv', delimiter=';')
        warehouse_2_fields : pd = pd.read_csv('data/delivery_center2.csv', delimiter=';')

        """
        Assuming that the agents' have unique ids - uids
        this will create the users in the prosody server in the format:
        ```plaintext
            drone_1, 
            drone_2,
            ..., 
            drone_x, 
            warehouse_1, 
            warehouse_2
        ```
        """
        agents_uids : list[str] = delivery_drones_fields['id'].to_list() \
                + [warehouse_1_fields['id'].head(1).values[0]] \
                + [warehouse_2_fields['id'].head(1).values[0]]
                
        # create_agents(agents_uids)

        # Setup delivery drones
        delivery_drones : list[dict] = parse_delivery_drones(delivery_drones_fields)

        # Setup warehouses and orders
        warehouse_1 = parse_warehouses_and_orders(warehouse_1_fields)
        warehouse_2 = parse_warehouses_and_orders(warehouse_2_fields)

        # Setup delivery logic
        delivery_logic : DeliveryLogic = DeliveryLogic(
            delivery_drones = delivery_drones,
            warehouses = [warehouse_1, warehouse_2],
        )
        
    #except Exception as e:
    #    print("Error:", e)

if __name__ == "__main__":
    main()