import requests
import json
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Value
import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

execution_counter = Value('i', 0)

def get_json_from_url(symbol):
    api_key = os.getenv('FMG_API')
    url = f"https://financialmodelingprep.com/api/v3/historical-chart/15min/{symbol}?&apikey={api_key}"

    print(f'Retrieving {symbol}')
    response = requests.get(url)
    data_list = []

    # Check for successful response
    if response.status_code == 200:
        data = response.json()
        if data:  # Ensure the response contains data
            print(f"Data retrieved for {symbol}: {len(data)} entries")
            data_list.extend(data)
        else:
            print(f"No data returned for {symbol}")
    else:
        print(f"Failed to fetch data for {symbol}. HTTP status code: {response.status_code}")

    

    return data_list

def symbol_cycle(symbol_list):
    # List of symbols to fetch
    #symbol_list = ['EURUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD', 
    #               'EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY', 'USDHKD']

    # Dictionary to store raw data
    data_dict = {}

    # Fetch data for each symbol
    for symbol in symbol_list:
        print(f'Adding {symbol}')
        data = get_json_from_url(symbol)
        data_dict[symbol.lower()] = data

    # Prepare a dictionary to hold DataFrames for each symbol
    dfs = {}
    for symbol, data in data_dict.items():
        if data:  # Only process if data exists
            # Create a DataFrame from the list of dictionaries
            df = pd.DataFrame(data)
            # Rename columns to include symbol prefix
            df = df.rename(columns={
                'date': f'{symbol}_date',
                'open': f'{symbol}_open',
                'high': f'{symbol}_high',
                'low': f'{symbol}_low',
                'close': f'{symbol}_close',
                'volume': f'{symbol}_volume'
            })
            # Ensure 'date' is in datetime format for proper alignment
            df[f'{symbol}_date'] = pd.to_datetime(df[f'{symbol}_date'])
            # Set date as index for easier merging
            df = df.set_index(f'{symbol}_date')
            dfs[symbol] = df
        else:
            print(f"No data to process for {symbol}")

    # Merge all DataFrames on their date index
    combined_df = pd.DataFrame()
    for symbol, df in dfs.items():
        if combined_df.empty:
            combined_df = df
        else:
            combined_df = combined_df.join(df, how='outer')

    # Reset index to bring date columns back as regular columns
    #combined_df = combined_df.reset_index(drop=True)

    # Forward-fill missing numeric values
    numeric_cols = [col for col in combined_df.columns if col.endswith(('_date','_open', '_high', '_low', '_close', '_volume'))]
    combined_df[numeric_cols] = combined_df[numeric_cols].fillna(method='ffill')

    # Optionally, fill any remaining NaNs (e.g., at the start) with backward fill or zeros
    combined_df[numeric_cols] = combined_df[numeric_cols].fillna(method='ffill')  # or .fillna(0)

    # Print the resulting DataFrame
    print("Combined DataFrame with forward-filled values:")
    print(combined_df.head())
  #  unix_time = pd.to_datetime(combined_df.index).timestamp()
   # combined_df['timestamps'] =unix_time
    return combined_df

    # Optionally save to CSV for inspection
   # combined_df.to_csv('historical_data.csv', index=False)
    #print("Data saved to 'historical_data.csv'")