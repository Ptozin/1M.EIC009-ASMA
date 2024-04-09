import json, pandas as pd
from misc.create_user import ProsodyClient
from logic import DeliveryLogic
from parse_data import parse_data

def main() -> None:
    # Parse data
    delivery_drones, warehouses = parse_data()

    # Setup delivery logic
    delivery_logic : DeliveryLogic = DeliveryLogic(delivery_drones, warehouses)
        

if __name__ == "__main__":
    main()