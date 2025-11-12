# Binance API credentials
API_KEY = ''
API_SECRET = ''

# Trading configuration
SYMBOL = 'DOGE/USDT'  # Trading pair
TIMEFRAME = '1m'  # 1 minute candles
EMA_PERIOD = 12  # ⚠️ Reducido para más sensibilidad

# Futures configuration
USE_FUTURES = True  # ⚠️ ACTIVAR FUTURES TRADING
LEVERAGE = 10  # ⚠️ Apalancamiento (2-5x recomendado para principiantes, máx 125x)
MARGIN_MODE = 'isolated'  # 'isolated' o 'cross' (isolated es más seguro)

# Position sizing
POSITION_SIZE_USDT = 5  # Amount in USDT to trade per position (sin apalancamiento) - DEPRECATED: se usa balance dinámico
USE_DYNAMIC_POSITION_SIZE = True  # Usar tamaño de posición dinámico basado en balance disponible
POSITION_SIZE_PERCENT = 10  # Porcentaje del balance disponible a usar por posición (1-100)

# Risk management
TAKE_PROFIT_PERCENT = 0.6  # ⚠️ Aumentado para compensar comisiones (DEPRECATED: se usa TARGET_PROFIT_USDT)
STOP_LOSS_PERCENT = 0.4   # ⚠️ Ajustado (mantener ratio 1.5:1)
TARGET_PROFIT_USDT = 2.0  # Ganancia objetivo por operación en USDT

# Execution settings
LOOP_INTERVAL = 3  # Seconds between each loop iteration (3-5 seconds)
COOLDOWN_SECONDS = 60  # ⚠️ Tiempo de espera después de cerrar posición (evita overtrading)
ENABLE_REAL_TRADING = True  # ⚠️ DESACTIVADO - Probar en testnet primero
ENABLE_SHORT_POSITIONS = True  # ⚠️ Permitir posiciones SHORT (venta en corto)

# Sandbox mode configuration
USE_SANDBOX = False  # ⚠️ ACTIVADO - Usar testnet para practicar