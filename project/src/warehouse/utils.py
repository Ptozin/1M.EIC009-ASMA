# ----------------------------------------------------------------------------------------------

import json

# ----------------------------------------------------------------------------------------------

def select_orders(inventory) -> str:        
    orders_to_deliver = []
    for _, order in inventory.items():
        orders_to_deliver.append(order.__repr__())
        if len(orders_to_deliver) == 5: # TODO: change so that it selects orders with some criteria (like proximity - matrix approach)
            break
    return json.dumps(orders_to_deliver)

# ----------------------------------------------------------------------------------------------