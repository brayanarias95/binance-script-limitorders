from ast import If
from symtable import Symbol
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
import config
import keyboard


user_key = config.API_KEY
secret_key = config.API_SECRET

binance_client = Client(user_key, secret_key)

#cuanto apalancamiento leverage
apalancamiento=50
binance_client.futures_change_leverage(symbol="1000SHIBUSDT", leverage=apalancamiento)

# Target profit en USDT
TARGET_PROFIT_USDT = 2.0


def calculate_take_profit_price(entry_price, position_size_usdt, target_profit_usd, leverage, position_side='LONG'):
    """
    Calcula el precio de take profit necesario para obtener una ganancia fija en USD
    
    Args:
        entry_price: Precio de entrada de la posición
        position_size_usdt: Tamaño de la posición en USDT (sin apalancamiento)
        target_profit_usd: Ganancia objetivo en USD (ej: 2.0 para 2 USDT)
        leverage: Apalancamiento usado
        position_side: 'LONG' o 'SHORT'
        
    Returns:
        Precio objetivo para obtener el profit deseado
    """
    # Calcular cantidad de activo comprado/vendido
    amount = position_size_usdt / entry_price
    
    # Calcular el cambio de precio necesario para obtener el profit deseado
    # Profit = (price_change * amount) * leverage
    # price_change = profit / (amount * leverage)
    price_change_needed = target_profit_usd / (amount * leverage)
    
    if position_side == 'LONG':
        # Para LONG, necesitamos que el precio suba
        take_profit_price = entry_price + price_change_needed
    else:  # SHORT
        # Para SHORT, necesitamos que el precio baje
        take_profit_price = entry_price - price_change_needed
    
    return take_profit_price


def create_order_with_retry(symbol, side, precio, cantidad_inicial, apalancamiento):
    """
    Crea una orden de futuros con manejo de error -2019 (margen insuficiente).
    Si hay error -2019, recalcula la cantidad basada en el balance disponible.
    
    Args:
        symbol: Símbolo del par (ej: '1000SHIBUSDT')
        side: 'BUY' o 'SELL'
        precio: Precio límite de la orden
        cantidad_inicial: Cantidad inicial calculada
        apalancamiento: Apalancamiento configurado
        
    Returns:
        Orden ejecutada o None si falló
    """
    try:
        # Intentar crear la orden con la cantidad inicial
        orden = binance_client.futures_create_order(
            symbol=symbol,
            type='LIMIT',
            timeInForce='GTC',
            price=precio,
            side=side,
            quantity=cantidad_inicial
        )
        return orden
        
    except BinanceAPIException as e:
        # Verificar si es error -2019 (Margin insuficiente)
        if e.code == -2019:
            print(f"⚠️  Error -2019 (Margin insuficiente). Intentando reducir cantidad inicial: {cantidad_inicial}")
            
            # Obtener balance disponible actualizado
            balance = binance_client.futures_account_balance()
            saldo_disponible = 0.0
            for x in balance:
                if x['asset'] == 'USDT':
                    saldo_disponible = float(x['availableBalance'])
            
            # Calcular nueva cantidad basada en saldo disponible
            # Usar solo el 95% del disponible para dejar margen de seguridad
            cantidad_ajustada = int((saldo_disponible / precio) * 0.95) * apalancamiento
            notional = cantidad_ajustada * precio
            
            print(f"   ↘ Probando cantidad basada en balance disponible: {cantidad_ajustada} (notional={notional:.4f})")
            
            # Verificar que la nueva cantidad sea válida
            if cantidad_ajustada <= 0:
                print(f"❌ Balance insuficiente. Saldo disponible: {saldo_disponible} USDT")
                return None
            
            try:
                # Reintentar con la cantidad ajustada
                orden = binance_client.futures_create_order(
                    symbol=symbol,
                    type='LIMIT',
                    timeInForce='GTC',
                    price=precio,
                    side=side,
                    quantity=cantidad_ajustada
                )
                
                # Mostrar detalles de la posición resultante
                print(f"✅ Orden ejecutada con cantidad ajustada: {cantidad_ajustada}")
                time.sleep(0.2)
                
                # Obtener detalles de la posición
                position = binance_client.futures_position_information(symbol=symbol)
                for pos in position:
                    if pos['symbol'] == symbol:
                        print(f"📊 Detalles de la posición:")
                        print(f"   • Cantidad (posAmt): {pos['positionAmt']}")
                        print(f"   • Precio entrada (entryPrice): {pos['entryPrice']}")
                        print(f"   • Precio liquidación (liquidationPrice): {pos['liquidationPrice']}")
                        print(f"   • PnL no realizado: {pos['unRealizedProfit']} USDT")
                        print(f"   • Apalancamiento: {pos['leverage']}x")
                        break
                
                return orden
                
            except BinanceAPIException as e2:
                print(f"❌ Error al reintentar con cantidad ajustada: {e2}")
                return None
        else:
            # Otro tipo de error de API
            print(f"❌ Error de Binance API ({e.code}): {e.message}")
            return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None





time.sleep(0.2)
print('-----------------------------')
position=binance_client.futures_position_information()
#print(position)
for x in position:
    if(x['symbol']=='1000SHIBUSDT'):
        print(x)
        entrada=float(x['entryPrice'])
        cantidad=x['positionAmt']

while True:


    if keyboard.is_pressed('2'):
        precioshib=binance_client.futures_symbol_ticker(symbol='1000SHIBUSDT')
        print(precioshib)

        balance=binance_client.futures_account_balance()
        for x in balance:
            if(x['asset']=='USDT'):
                saldo=float(x['balance'])
        print(saldo)
        precio=float(precioshib['price'])
        
        # Calcular position size en USDT (el margen usado, sin apalancamiento)
        position_size_usdt = saldo * 0.98  # Usar 98% del balance disponible
        
        cantidadshiba=int((position_size_usdt/precio))*apalancamiento
        print(f"Cantidad inicial calculada: {cantidadshiba}")
        print(f"Position size (margen): {position_size_usdt:.2f} USDT")
        
        # Calcular precio de take profit para obtener 2 USDT
        take_profit_price = calculate_take_profit_price(
            entry_price=precio,
            position_size_usdt=position_size_usdt,
            target_profit_usd=TARGET_PROFIT_USDT,
            leverage=apalancamiento,
            position_side='LONG'
        )
        
        print(f"Precio de entrada: {precio:.8f}")
        print(f"Precio de Take Profit: {take_profit_price:.8f} (para ${TARGET_PROFIT_USDT:.2f} USDT profit)")
        
        #orden de comprar
        orden_result = create_order_with_retry(
            symbol='1000SHIBUSDT',
            side='BUY',
            precio=precio,
            cantidad_inicial=cantidadshiba,
            apalancamiento=apalancamiento
        )
        
        if orden_result is None:
            print("❌ No se pudo ejecutar la orden de compra")
            continue
        time.sleep(0.2)
        espera=True
        while espera == True:

            position=binance_client.futures_position_information()
            #print(position)
            for x in position:
                if(x['symbol']=='1000SHIBUSDT'):
                    print(x)
                    entrada=float(x['entryPrice'])
                    cantidad=x['positionAmt']
                    
            
            if cantidad=='0':
                print('aun no estamos en pocision')
                time.sleep(0.1)
                if keyboard.is_pressed('5'):
                    espera=False
            if cantidad!='0':
                if int(cantidad)<0:
                        cantidad=int(cantidad)*(-1)
                else:
                    cantidad=int(cantidad)
                
                # Usar el precio de take profit calculado
                print(f"Colocando orden de venta LIMIT a {take_profit_price:.8f} para profit de ${TARGET_PROFIT_USDT:.2f} USDT")
                binance_client.futures_create_order(
                symbol='1000SHIBUSDT',
                type='LIMIT',
                timeInForce='GTC',
                price=take_profit_price,
                side='SELL',
                quantity=cantidad
                )
                espera=False



        
        
    if keyboard.is_pressed('3'):
        precioshib=binance_client.futures_symbol_ticker(symbol='1000SHIBUSDT')
        print(precioshib)

        balance=binance_client.futures_account_balance()
        for x in balance:
            if(x['asset']=='USDT'):
                saldo=float(x['balance'])
        print(saldo)
        precio=float(precioshib['price'])
        
        # Calcular position size en USDT (el margen usado, sin apalancamiento)
        position_size_usdt = saldo * 0.98  # Usar 98% del balance disponible
        
        cantidadshiba=int((position_size_usdt/precio))*apalancamiento
        print(f"Cantidad inicial calculada: {cantidadshiba}")
        print(f"Position size (margen): {position_size_usdt:.2f} USDT")
        
        # Calcular precio de take profit para obtener 2 USDT en SHORT
        take_profit_price = calculate_take_profit_price(
            entry_price=precio,
            position_size_usdt=position_size_usdt,
            target_profit_usd=TARGET_PROFIT_USDT,
            leverage=apalancamiento,
            position_side='SHORT'
        )
        
        print(f"Precio de entrada: {precio:.8f}")
        print(f"Precio de Take Profit: {take_profit_price:.8f} (para ${TARGET_PROFIT_USDT:.2f} USDT profit)")
        
        #orden de vender
        orden_result = create_order_with_retry(
            symbol='1000SHIBUSDT',
            side='SELL',
            precio=precio,
            cantidad_inicial=cantidadshiba,
            apalancamiento=apalancamiento
        )
        
        if orden_result is None:
            print("❌ No se pudo ejecutar la orden de venta")
            continue
        time.sleep(0.2)
        espera=True
        while espera == True:

            position=binance_client.futures_position_information()
            #print(position)
            for x in position:
                if(x['symbol']=='1000SHIBUSDT'):
                    print(x)
                    entrada=float(x['entryPrice'])
                    cantidad=x['positionAmt']
                    
            if cantidad=='0':
                print('aun no estamos en pocision')
                time.sleep(0.1)
                if keyboard.is_pressed('5'):
                    espera=False
            if cantidad!='0':
                if int(cantidad)<0:
                        cantidad=int(cantidad)*(-1)
                else:
                    cantidad=int(cantidad)
                
                # Usar el precio de take profit calculado para SHORT
                print(f"Colocando orden de compra LIMIT a {take_profit_price:.8f} para profit de ${TARGET_PROFIT_USDT:.2f} USDT")
                binance_client.futures_create_order(
                symbol='1000SHIBUSDT',
                type='LIMIT',
                timeInForce='GTC',
                price=take_profit_price,
                side='BUY',
                quantity=cantidad
                )
                espera=False

    position=binance_client.futures_position_information()
    #print(position)
    for x in position:
        if(x['symbol']=='1000SHIBUSDT'):
            print(x)
            entrada=float(x['entryPrice'])
            markprice=float(x['markPrice'])
            cantidad=x['positionAmt']
            pnl=float(x['unRealizedProfit'])
    if cantidad!='0' and pnl<-3:
        if int(cantidad)<0:
            cantidad=int(cantidad)*(-1)
        else:
            cantidad=int(cantidad)
        if entrada<markprice:
                binance_client.futures_create_order(
                symbol='1000SHIBUSDT',
                type='MARKET',
                side='BUY',
                quantity=cantidad
                )
        else:
                binance_client.futures_create_order(
                symbol='1000SHIBUSDT',
                type='MARKET',
                side='SELL',
                quantity=cantidad
                )
    time.sleep(0.2)