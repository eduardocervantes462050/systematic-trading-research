import os
import pandas as pd
from datetime import datetime


class CSVClientManager:
    def __init__(
        self, clients_csv="data/interim/clients.csv", history_folder="reports"
    ):
        self.clients_csv = clients_csv
        self.history_folder = history_folder
        os.makedirs(history_folder, exist_ok=True)
        os.makedirs(
            os.path.dirname(clients_csv), exist_ok=True
        )  # create folder if missing

        # Load existing clients or create empty DataFrame
        if os.path.exists(clients_csv) and os.path.getsize(clients_csv) > 0:
            self.clients = pd.read_csv(clients_csv, index_col="client_name")
        else:
            # File missing or empty → create empty DataFrame
            self.clients = pd.DataFrame(columns=["cash"])
            self.clients.to_csv(clients_csv)  # create the file

    # -----------------------------
    # Add / Update client
    # -----------------------------
    def add_client(self, name, cash=0, positions=None):
        positions = positions or {}

        # Ensure all columns exist in self.clients
        for ticker in positions.keys():
            if ticker not in self.clients.columns:
                self.clients[ticker] = 0  # initialize new column with 0

        # Add or update client
        row = {"cash": cash, **positions}
        self.clients.loc[name] = row

        # Fill missing values (if any tickers are missing for this client)
        self.clients = self.clients.fillna(0)

        # Save
        self.clients.to_csv(self.clients_csv)
        print(f"Added/Updated client {name}")

    # -----------------------------
    # Record portfolio snapshot
    # -----------------------------
    def record_history(self, name, total_value, date=None):
        date = date or datetime.today().strftime("%Y-%m-%d")

        if name not in self.clients.index:
            raise ValueError(f"Client {name} not found")

        client_row = self.clients.loc[name].to_dict()
        row = {"Date": date, "total_value": total_value, **client_row}

        history_file = os.path.join(self.history_folder, f"history_{name}.csv")

        if os.path.exists(history_file):
            df = pd.read_csv(history_file)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_csv(history_file, index=False)
        print(f"Recorded history for {name} on {date}")

    # -----------------------------
    # Get client positions
    # -----------------------------
    def get_client_positions(self, name):
        if name not in self.clients.index:
            raise ValueError(f"Client {name} not found")
        return self.clients.loc[name].to_dict()
