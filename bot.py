from ast import If
from symtable import Symbol
import time
from binance.client import Client
import config
import keyboard


user_key = config.API_KEY
secret_key = config.API_SECRET

binance_client = Client(user_key, secret_key)

#cuanto apalancamiento leverage
apalancamiento=50
binance_client.futures_change_leverage(symbol="1000SHIBUSDT", leverage=apalancamiento)





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
        cantidadshiba=int((saldo/precio)*0.98)*apalancamiento
        print(cantidadshiba)
        #orden de comprar
        binance_client.futures_create_order(
        symbol='1000SHIBUSDT',
        type='LIMIT',
        timeInForce='GTC',
        price=precio ,
        side='BUY',
        quantity=cantidadshiba
        )
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
                binance_client.futures_create_order(
                symbol='1000SHIBUSDT',
                type='LIMIT',
                timeInForce='GTC',
                price=precio+0.00002,
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
        cantidadshiba=int((saldo/precio)*0.98)*apalancamiento
        print(cantidadshiba)
        #orden de vender
        binance_client.futures_create_order(
        symbol='1000SHIBUSDT',
        type='LIMIT',
        timeInForce='GTC',
        price=precio ,
        side='SELL',
        quantity=cantidadshiba
        )
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
                binance_client.futures_create_order(
                symbol='1000SHIBUSDT',
                type='LIMIT',
                timeInForce='GTC',
                price=precio-0.00002,
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