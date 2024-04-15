import argparse

from logic import DeliveryLogic
from parse_data import parse_data
import threading
from visualization import WebApp

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
    #web_app = WebApp()
    
    #stop_thread = False
    #
    #server_thread = threading.Thread(target=web_app.socketio.run, args=(web_app.app,), kwargs={'port': 8050})
    #server_thread.start()
    
    # Setup delivery logic
    DeliveryLogic(delivery_drones, warehouses)
    
    # Kill the server thread
    # server_thread.raise_exception()
    # server_thread.join()
        

if __name__ == "__main__":
    main()