# Binance API credentials
API_KEY = 'your api key'
API_SECRET = 'your api secret'

# Trading configuration
SYMBOL = 'BTC/USDT'  # Trading pair
TIMEFRAME = '1m'  # 1 minute candles
EMA_PERIOD = 20  # EMA period for the strategy

# Position sizing
POSITION_SIZE_USDT = 100  # Amount in USDT to trade per position

# Risk management
TAKE_PROFIT_PERCENT = 0.4  # Take profit at +0.4%
STOP_LOSS_PERCENT = 0.3  # Stop loss at -0.3%

# Execution settings
LOOP_INTERVAL = 3  # Seconds between each loop iteration (3-5 seconds)
ENABLE_REAL_TRADING = False  # Set to True to enable real trading (USE WITH CAUTION)

# Sandbox mode configuration
USE_SANDBOX = True  # Use testnet/sandbox mode for paper trading