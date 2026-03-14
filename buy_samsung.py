import warnings
warnings.filterwarnings('ignore')
from kis_api_client import KisApiClient
import sys

client = KisApiClient()
if not client.is_ready:
    print('API Client is not ready.')
    sys.exit(1)
df = client.fetch_ohlcv('005930')
if df is not None and not df.empty:
    target_price = int(df.iloc[-1]['Close'])
    print(f'Fetching last price: {target_price}')
    res = client.execute_buy('005930', 1, target_price)
    print(res)
else:
    print('Failed to fetch stock prices.')
