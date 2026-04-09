from portfolio.equity_curve import calculate_portfolio_equity_curve

    # Calculate equity curves and metrics
    for client_name in tracker.get_all_clients():
        client = tracker.get_client(client_name)
        client.history_df = calculate_portfolio_equity_curve(client, filtered_data)

        df = client.history_df
        start_value = df["total_value"].iloc[0]
        end_value = df["total_value"].iloc[-1]
        years = (
            pd.to_datetime(df["Date"].iloc[-1]) - pd.to_datetime(df["Date"].iloc[0])
        ).days / 365.25
        cagr = (end_value / start_value) ** (1 / years) - 1
        print(f"{client_name} CAGR: {cagr:.2%}")

    # Save all histories after rebalancing
    tracker.save_all_histories()
    print("Client portfolio histories saved.")