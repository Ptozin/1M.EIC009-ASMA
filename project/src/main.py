import argparse

from logic import DeliveryLogic
from parse_data import parse_data
import threading
from visualization import WebApp
from time import sleep

def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Delivery Drone Simulation")
    parser.add_argument(
        "-d", "--data", type=str, default="original", choices=["original", "small"],
        help="Data to use for the simulation. Options: original, small. Default: original."
    )
    return parser.parse_args()

def main() -> None:
    # Parse arguments
    args = parse_args()
    
    print(f"Using data: {args.data}")
    
    # Parse data
    delivery_drones, warehouses = parse_data(args.data == "original")
    
    # Setup web app on a separate thread
    web_app = WebApp()
    
    server_thread = threading.Thread(target=web_app.socketio.run, args=(web_app.app,), kwargs={'port': 8050})
    server_thread.daemon = True
    server_thread.start()
    # Wait for the server to start
    # sleep(3)
    
    # Setup delivery logic
    DeliveryLogic(delivery_drones, warehouses, web_app.socketio)
    
    # Kill the server thread
    exit(0)
        

if __name__ == "__main__":
    main()