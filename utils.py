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
    Determina si se debe comprar (LONG) basado en la estrategia
    Compra cuando el precio cierra por encima de la EMA
    
    Args:
        current_price: Precio actual
        ema: Valor de la EMA
        
    Returns:
        True si se debe comprar, False en caso contrario
    """
    return current_price > ema


def should_sell_short(current_price: float, ema: float) -> bool:
    """
    Determina si se debe vender en corto (SHORT) basado en la estrategia
    Vende en corto cuando el precio cierra por debajo de la EMA
    
    Args:
        current_price: Precio actual
        ema: Valor de la EMA
        
    Returns:
        True si se debe vender en corto, False en caso contrario
    """
    return current_price < ema


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


def should_sell(entry_price: float, current_price: float, take_profit_percent: float, 
                stop_loss_percent: float, position_side: str = 'LONG') -> tuple[bool, str]:
    """
    Determina si se debe cerrar la posición basado en el take profit o stop loss
    
    Args:
        entry_price: Precio de entrada
        current_price: Precio actual
        take_profit_percent: Porcentaje de ganancia objetivo
        stop_loss_percent: Porcentaje de pérdida máxima
        position_side: 'LONG' o 'SHORT'
        
    Returns:
        Tupla (should_sell: bool, reason: str)
    """
    if position_side == 'LONG':
        profit_loss_percent = calculate_profit_loss_percent(entry_price, current_price)
    else:  # SHORT
        # Para SHORT, ganamos cuando el precio baja
        profit_loss_percent = -calculate_profit_loss_percent(entry_price, current_price)
    
    if profit_loss_percent >= take_profit_percent:
        return True, f"TAKE PROFIT alcanzado: +{profit_loss_percent:.2f}%"
    elif profit_loss_percent <= -stop_loss_percent:
        return True, f"STOP LOSS alcanzado: {profit_loss_percent:.2f}%"
    
    return False, ""


def create_market_buy_order(exchange: ccxt.Exchange, symbol: str, amount_usdt: float, 
                           enable_real_trading: bool, use_futures: bool = False) -> Optional[Dict[str, Any]]:
    """
    Crea una orden de compra de mercado (LONG en Futures)
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        amount_usdt: Cantidad en USDT a comprar
        enable_real_trading: Si está habilitado el trading real
        use_futures: Si se está usando Futures
        
    Returns:
        Información de la orden o None si hay error
    """
    try:
        if not enable_real_trading:
            print(f"[MODO SIMULACIÓN] Orden de compra LONG: {amount_usdt} USDT de {symbol}")
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
        
        # Usar $5.50 para estar bien por encima del mínimo de $5
        # Esto evita problemas con redondeo y fluctuaciones de precio
        amount_usdt_safe = max(amount_usdt, 5.5)
        amount = amount_usdt_safe / current_price
        
        # Redondear hacia ARRIBA para asegurar que el notional sea suficiente
        import math
        amount = math.ceil(amount * 10) / 10  # Redondear hacia arriba a 1 decimal
        
        # Verificar que el notional sea suficiente
        notional = amount * current_price
        
        if use_futures:
            print(f"   DEBUG: Creando LONG - Precio: ${current_price:.4f}, Cantidad: {amount} DOGE, Notional: ${notional:.2f} USDT")
            
            # Verificación adicional
            if notional < 5.2:
                print(f"   ⚠️ Notional ${notional:.2f} muy cerca del mínimo. Ajustando más...")
                amount = math.ceil((6.0 / current_price) * 10) / 10
                notional = amount * current_price
                print(f"   ✅ Cantidad ajustada: {amount} DOGE, Notional: ${notional:.2f} USDT")
            
            # En Futures, usar create_market_buy_order directamente
            order = exchange.create_market_buy_order(symbol, amount)
        else:
            order = exchange.create_market_buy_order(symbol, amount)
        
        return order
    except Exception as e:
        print(f"Error creando orden de compra: {e}")
        return None


def create_market_sell_order(exchange: ccxt.Exchange, symbol: str, amount: float, 
                             enable_real_trading: bool, use_futures: bool = False,
                             position_side: str = 'LONG') -> Optional[Dict[str, Any]]:
    """
    Crea una orden de venta de mercado (cierra LONG en Futures)
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        amount: Cantidad de activo a vender
        enable_real_trading: Si está habilitado el trading real
        use_futures: Si se está usando Futures
        position_side: 'LONG' o 'SHORT'
        
    Returns:
        Información de la orden o None si hay error
    """
    try:
        if not enable_real_trading:
            print(f"[MODO SIMULACIÓN] Orden de venta (cerrar {position_side}): {amount} de {symbol}")
            return {
                'id': 'sim_' + str(int(time.time())),
                'symbol': symbol,
                'type': 'market',
                'side': 'sell',
                'amount': amount,
                'status': 'closed',
                'simulated': True
            }
        
        # Redondear cantidad
        amount = round(amount, 1)
        
        if use_futures:
            print(f"   DEBUG: Cerrando LONG - Cantidad: {amount} DOGE")
            # En Futures, cerrar LONG con sell
            order = exchange.create_market_sell_order(symbol, amount)
        else:
            order = exchange.create_market_sell_order(symbol, amount)
        
        return order
    except Exception as e:
        print(f"Error creando orden de venta: {e}")
        return None


def create_short_order(exchange: ccxt.Exchange, symbol: str, amount_usdt: float, 
                      enable_real_trading: bool) -> Optional[Dict[str, Any]]:
    """
    Crea una orden SHORT (venta en corto) en Futures
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        amount_usdt: Cantidad en USDT para la posición
        enable_real_trading: Si está habilitado el trading real
        
    Returns:
        Información de la orden o None si hay error
    """
    try:
        if not enable_real_trading:
            print(f"[MODO SIMULACIÓN] Orden SHORT: {amount_usdt} USDT de {symbol}")
            return {
                'id': 'sim_' + str(int(time.time())),
                'symbol': symbol,
                'type': 'market',
                'side': 'sell',
                'amount': amount_usdt,
                'status': 'closed',
                'simulated': True,
                'positionSide': 'SHORT'
            }
        
        # Obtener el precio actual para calcular la cantidad
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Usar $5.50 para estar bien por encima del mínimo de $5
        amount_usdt_safe = max(amount_usdt, 5.5)
        amount = amount_usdt_safe / current_price
        
        # Redondear hacia ARRIBA para asegurar que el notional sea suficiente
        import math
        amount = math.ceil(amount * 10) / 10
        
        # Verificar que el notional sea suficiente
        notional = amount * current_price
        
        print(f"   DEBUG: Creando SHORT - Precio: ${current_price:.4f}, Cantidad: {amount} DOGE, Notional: ${notional:.2f} USDT")
        
        # Verificación adicional
        if notional < 5.2:
            print(f"   ⚠️ Notional ${notional:.2f} muy cerca del mínimo. Ajustando más...")
            amount = math.ceil((6.0 / current_price) * 10) / 10
            notional = amount * current_price
            print(f"   ✅ Cantidad ajustada: {amount} DOGE, Notional: ${notional:.2f} USDT")
        
        # Abrir posición SHORT con sell
        order = exchange.create_market_sell_order(
            symbol=symbol,
            amount=amount
        )
        
        return order
    except Exception as e:
        print(f"Error creando orden SHORT: {e}")
        return None


def close_short_order(exchange: ccxt.Exchange, symbol: str, amount: float, 
                     enable_real_trading: bool) -> Optional[Dict[str, Any]]:
    """
    Cierra una posición SHORT en Futures
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        amount: Cantidad a cerrar
        enable_real_trading: Si está habilitado el trading real
        
    Returns:
        Información de la orden o None si hay error
    """
    try:
        if not enable_real_trading:
            print(f"[MODO SIMULACIÓN] Cerrar SHORT: {amount} de {symbol}")
            return {
                'id': 'sim_' + str(int(time.time())),
                'symbol': symbol,
                'type': 'market',
                'side': 'buy',
                'amount': amount,
                'status': 'closed',
                'simulated': True
            }
        
        # Redondear cantidad
        amount = round(amount, 1)
        
        print(f"   DEBUG: Cerrando SHORT - Cantidad: {amount} DOGE")
        
        # Cerrar posición SHORT con buy (comprar de vuelta)
        order = exchange.create_market_buy_order(
            symbol=symbol,
            amount=amount
        )
        
        return order
    except Exception as e:
        print(f"Error cerrando orden SHORT: {e}")
        return None


def create_stop_limit_order(exchange: ccxt.Exchange, symbol: str, side: str, 
                           amount: float, trigger_price: float, limit_price: float,
                           reduce_only: bool = True) -> Optional[Dict[str, Any]]:
    """
    Crea una orden stop-limit en Futures
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        side: 'buy' o 'sell' (buy para cerrar SHORT, sell para cerrar LONG)
        amount: Cantidad del activo
        trigger_price: Precio de activación del stop
        limit_price: Precio límite de la orden
        reduce_only: Si True, solo reduce la posición (no abre nueva)
        
    Returns:
        Información de la orden o None si hay error
    """
    try:
        # Redondear precios a 4 decimales y cantidad a 1 decimal
        trigger_price = round(trigger_price, 4)
        limit_price = round(limit_price, 4)
        amount = round(amount, 1)
        
        # Crear orden stop-limit usando la API de Futures
        params = {
            'stopPrice': trigger_price,
            'reduceOnly': reduce_only
        }
        
        order = exchange.create_order(
            symbol=symbol,
            type='STOP',
            side=side,
            amount=amount,
            price=limit_price,
            params=params
        )
        
        return order
    except Exception as e:
        print(f"Error creando orden stop-limit: {e}")
        return None


def cancel_all_stop_orders(exchange: ccxt.Exchange, symbol: str) -> bool:
    """
    Cancela todas las órdenes stop pendientes para un símbolo
    
    Args:
        exchange: Instancia del exchange de CCXT
        symbol: Par de trading
        
    Returns:
        True si se cancelaron correctamente, False si hubo error
    """
    try:
        # Obtener órdenes abiertas
        open_orders = exchange.fetch_open_orders(symbol)
        
        # Filtrar solo órdenes de tipo STOP o STOP_MARKET
        stop_orders = [
            order for order in open_orders 
            if order.get('type') in ['STOP', 'STOP_MARKET', 'STOP_LIMIT']
        ]
        
        # Cancelar cada orden stop
        for order in stop_orders:
            try:
                exchange.cancel_order(order['id'], symbol)
                print(f"   ✅ Stop-limit cancelado: ID {order['id']}")
            except Exception as e:
                print(f"   ⚠️ Error cancelando orden {order['id']}: {e}")
        
        return True
    except Exception as e:
        print(f"Error cancelando órdenes stop: {e}")
        return False


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


def get_futures_available_balance(exchange: ccxt.Exchange, currency: str = 'USDT') -> Optional[float]:
    """
    Obtiene el balance disponible en la cuenta de Futures
    
    Args:
        exchange: Instancia del exchange de CCXT configurado para Futures
        currency: Moneda (por defecto 'USDT')
        
    Returns:
        Balance disponible en Futures o None si hay error
    """
    try:
        balance = exchange.fetch_balance()
        # En Futures, el balance disponible está en 'free'
        available = balance['free'].get(currency, 0.0)
        return available
    except Exception as e:
        print(f"Error obteniendo balance de Futures: {e}")
        return None
