import argparse

from logic import DeliveryLogic
from parse_data import parse_data

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

    # Setup delivery logic
    DeliveryLogic(delivery_drones, warehouses)
        

if __name__ == "__main__":
    main()