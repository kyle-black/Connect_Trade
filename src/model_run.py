from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import time
import random
from datetime import datetime, timedelta
from oandapyV20 import API
from oandapyV20.endpoints.pricing import PricingInfo
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.positions import OpenPositions
from oandapyV20.endpoints.accounts import AccountDetails
import os
# OANDA API credentials

api_key = os.getenv('API_KEY')
account_id = os.getenv('ACCOUNT_ID')
API_KEY = api_key
ACCOUNT_ID = account_id
BASE_URL = "https://api-fxtrade.oanda.com"

# Initialize OANDA API client
client = API(access_token=API_KEY, environment="live")

# Trading parameters
SL_PIPS = 5.0
TP_PIPS = 25.0
PIP_VALUE = 0.0001  # For EUR/USD
SYMBOL = "EUR_USD"
RISK_PERCENT = 1.0  # Risk 1% of account balance per trade

# Function to calculate the next 15-minute bar time
def get_next_bar_time():
    now = datetime.utcnow()
    minute = now.minute
    next_minute = (minute // 15 + 1) * 15
    if next_minute >= 60:
        next_minute = 0
        now = now + timedelta(hours=1)
    next_bar = now.replace(minute=next_minute % 60, second=0, microsecond=0)
    return next_bar

# Function to get account balance
def get_account_balance():
    request = AccountDetails(accountID=ACCOUNT_ID)
    try:
        response = client.request(request)
        balance = float(response['account']['balance'])
        print(f"Current account balance: {balance}")
        return balance
    except Exception as e:
        print(f"Error fetching account balance: {e}")
        return None

# Function to get latest price
def get_latest_price():
    params = {"instruments": SYMBOL}
    request = PricingInfo(accountID=ACCOUNT_ID, params=params)
    try:
        response = client.request(request)
        price = float(response['prices'][0]['closeoutBid'])
        print(f"Latest price for {SYMBOL}: {price}")
        return price
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

# Function to place order with dynamic units
def place_order(direction, entry_price, units):
    sl_price = entry_price - SL_PIPS * PIP_VALUE if direction == "buy" else entry_price + SL_PIPS * PIP_VALUE
    tp_price = entry_price + TP_PIPS * PIP_VALUE if direction == "buy" else entry_price - TP_PIPS * PIP_VALUE
    
    order_body = {
        "order": {
            "units": str(units) if direction == "buy" else str(-units),
            "instrument": SYMBOL,
            "type": "MARKET",
            "stopLossOnFill": {"price": str(sl_price)},
            "takeProfitOnFill": {"price": str(tp_price)}
        }
    }
    request = OrderCreate(accountID=ACCOUNT_ID, data=order_body)
    try:
        response = client.request(request)
        print(f"{direction.capitalize()} order placed at {entry_price}, SL: {sl_price}, TP: {tp_price}, Units: {units}")
    except Exception as e:
        print(f"Order failed: {e}")

# Function to check open positions
def check_open_positions():
    request = OpenPositions(accountID=ACCOUNT_ID)
    try:
        response = client.request(request)
        positions = response.get("positions", [])
        print(f"Open positions: {len(positions)}")
        return len(positions) > 0
    except Exception as e:
        print(f"Error checking positions: {e}")
        return False

# Main trading loop
cool_down = 0
while True:
    now = datetime.utcnow()
    next_bar = get_next_bar_time()
    sleep_time = (next_bar - now).total_seconds()
    if sleep_time > 0:
        print(f"Sleeping for {sleep_time} seconds until next bar at {next_bar}")
        time.sleep(sleep_time)

    # Now at the start of a new 15-minute bar
    if cool_down > 0:
        cool_down -= 1
        print(f"Cool-down remaining: {cool_down}")
    else:
        if not check_open_positions():
            balance = get_account_balance()
            if balance:
                # Calculate units based on risk percentage
                units = int((RISK_PERCENT / 100 * balance) / (SL_PIPS * PIP_VALUE))
                print(f"Calculated units: {units} based on balance: {balance} and risk: {RISK_PERCENT}%")
                price = get_latest_price()
                if price:
                    action = random.randint(0, 2)
                    print(f"Random action chosen: {action}")
                    if action != 2:
                        direction = "buy" if action == 0 else "sell"
                        place_order(direction, price, units)
                        cool_down = 0  # 5-bar cool-down