import requests
import os
from datetime import datetime
from database import save_price, get_latest_price

NAVASAN_API_KEY = os.getenv('NAVASAN_API_KEY', 'freeFGpzjUacmoTt3fn9ZgAeigqwAWmW')

def get_instant_price() -> float:
    url = f'https://api.navasan.tech/latest?api_key={NAVASAN_API_KEY}&item=usd'
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        price = data['usd']['value']
        return float(price)
    except Exception as e:
        print(f"Error fetching price: {e}")
        return 0.0

def fetch_and_store_daily():
    price = get_instant_price()
    today = datetime.now().strftime('%Y-%m-%d')
    save_price(today, price, 0.0)
    return price
