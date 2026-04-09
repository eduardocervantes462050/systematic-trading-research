# src/portfolio/add_clients.py

from csv_client_manager import CSVClientManager


def main():
    # Initialize manager
    manager = CSVClientManager(
        clients_csv="data/interim/clients.csv", history_folder="reports"
    )

    # Add or update clients
    # Example: replace/add any client
    manager.add_client(
        "Eduardo", cash=1000, positions={"AAPL": 10, "MSFT": 5, "GOOGL": 0, "INTC": 0}
    )

    manager.add_client(
        "Client1",
        cash=50000,
        positions={"AAPL": 20, "MSFT": 0, "GOOGL": 20, "INTC": 100},
    )

    print("Clients added/updated successfully!")


if __name__ == "__main__":
    main()
