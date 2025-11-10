"""
Utilidades para el bot de scalping
Funciones auxiliares para obtener precios, calcular indicadores técnicos, etc.
"""

import ccxt
import pandas as pd
import time
from typing import Optional, Dict, Any


def get_current_price(exchange: ccxt.Exchange, symbol: str) -> Optional[float]:
    """
    Obtiene el precio actual del símbolo especificado
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading (ej: 'BTC/USDT')
        
    Returns:
        Precio actual como float, o None si hay error
    """
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"Error obteniendo precio actual: {e}")
        return None


def get_ohlcv_data(exchange: ccxt.Exchange, symbol: str, timeframe: str, limit: int = 100) -> Optional[pd.DataFrame]:
    """
    Obtiene datos OHLCV (velas) del exchange
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading (ej: 'BTC/USDT')
        timeframe: Timeframe de las velas (ej: '1m', '5m', '1h')
        limit: Número de velas a obtener
        
    Returns:
        DataFrame con las velas o None si hay error
    """
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error obteniendo datos OHLCV: {e}")
        return None


def calculate_ema(data: pd.DataFrame, period: int, column: str = 'close') -> Optional[float]:
    """
    Calcula la Media Móvil Exponencial (EMA) para el periodo especificado
    
    Args:
        data: DataFrame con los datos de precio
        period: Periodo de la EMA
        column: Columna a usar para el cálculo (por defecto 'close')
        
    Returns:
        Valor actual de la EMA o None si hay error
    """
    try:
        if len(data) < period:
            print(f"No hay suficientes datos para calcular EMA de {period} periodos")
            return None
        
        ema = data[column].ewm(span=period, adjust=False).mean()
        return ema.iloc[-1]
    except Exception as e:
        print(f"Error calculando EMA: {e}")
        return None


def should_buy(current_price: float, ema: float) -> bool:
    """
    Determina si se debe comprar basado en la estrategia
    Compra cuando el precio cierra por encima de la EMA
    
    Args:
        current_price: Precio actual
        ema: Valor de la EMA
        
    Returns:
        True si se debe comprar, False en caso contrario
    """
    return current_price > ema


def calculate_profit_loss_percent(entry_price: float, current_price: float) -> float:
    """
    Calcula el porcentaje de ganancia o pérdida
    
    Args:
        entry_price: Precio de entrada
        current_price: Precio actual
        
    Returns:
        Porcentaje de ganancia/pérdida
    """
    if entry_price == 0:
        return 0.0
    return ((current_price - entry_price) / entry_price) * 100


def should_sell(entry_price: float, current_price: float, take_profit_percent: float, stop_loss_percent: float) -> tuple[bool, str]:
    """
    Determina si se debe vender basado en el take profit o stop loss
    
    Args:
        entry_price: Precio de entrada
        current_price: Precio actual
        take_profit_percent: Porcentaje de ganancia objetivo
        stop_loss_percent: Porcentaje de pérdida máxima
        
    Returns:
        Tupla (should_sell: bool, reason: str)
    """
    profit_loss_percent = calculate_profit_loss_percent(entry_price, current_price)
    
    if profit_loss_percent >= take_profit_percent:
        return True, f"TAKE PROFIT alcanzado: +{profit_loss_percent:.2f}%"
    elif profit_loss_percent <= -stop_loss_percent:
        return True, f"STOP LOSS alcanzado: {profit_loss_percent:.2f}%"
    
    return False, ""


def create_market_buy_order(exchange: ccxt.Exchange, symbol: str, amount_usdt: float, enable_real_trading: bool) -> Optional[Dict[str, Any]]:
    """
    Crea una orden de compra de mercado
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        amount_usdt: Cantidad en USDT a comprar
        enable_real_trading: Si está habilitado el trading real
        
    Returns:
        Información de la orden o None si hay error
    """
    try:
        if not enable_real_trading:
            print(f"[MODO SIMULACIÓN] Orden de compra: {amount_usdt} USDT de {symbol}")
            return {
                'id': 'sim_' + str(int(time.time())),
                'symbol': symbol,
                'type': 'market',
                'side': 'buy',
                'amount': amount_usdt,
                'status': 'closed',
                'simulated': True
            }
        
        # Obtener el precio actual para calcular la cantidad
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = amount_usdt / current_price
        
        order = exchange.create_market_buy_order(symbol, amount)
        return order
    except Exception as e:
        print(f"Error creando orden de compra: {e}")
        return None


def create_market_sell_order(exchange: ccxt.Exchange, symbol: str, amount: float, enable_real_trading: bool) -> Optional[Dict[str, Any]]:
    """
    Crea una orden de venta de mercado
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        amount: Cantidad de activo a vender
        enable_real_trading: Si está habilitado el trading real
        
    Returns:
        Información de la orden o None si hay error
    """
    try:
        if not enable_real_trading:
            print(f"[MODO SIMULACIÓN] Orden de venta: {amount} de {symbol}")
            return {
                'id': 'sim_' + str(int(time.time())),
                'symbol': symbol,
                'type': 'market',
                'side': 'sell',
                'amount': amount,
                'status': 'closed',
                'simulated': True
            }
        
        order = exchange.create_market_sell_order(symbol, amount)
        return order
    except Exception as e:
        print(f"Error creando orden de venta: {e}")
        return None


def get_balance(exchange: ccxt.Exchange, currency: str) -> Optional[float]:
    """
    Obtiene el balance disponible de una moneda
    
    Args:
        exchange: Instancia del exchange de CCXT
        currency: Moneda (ej: 'USDT', 'BTC')
        
    Returns:
        Balance disponible o None si hay error
    """
    try:
        balance = exchange.fetch_balance()
        return balance['free'].get(currency, 0.0)
    except Exception as e:
        print(f"Error obteniendo balance: {e}")
        return None
