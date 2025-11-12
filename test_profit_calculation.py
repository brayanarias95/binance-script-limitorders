"""
Script de prueba manual para verificar el cálculo de take profit para 2 USDT

Este script verifica que la lógica de cálculo de precio de take profit
funcione correctamente para diferentes escenarios.
"""

import utils

def test_long_position():
    """Prueba para posición LONG"""
    print("\n" + "="*60)
    print("TEST: Posición LONG")
    print("="*60)
    
    entry_price = 0.08  # $0.08 USDT
    position_size_usdt = 10.0  # 10 USDT de margen
    target_profit_usd = 2.0  # Queremos ganar 2 USDT
    leverage = 10
    
    # Calcular precio de take profit
    take_profit_price = utils.calculate_take_profit_price_for_fixed_usd(
        entry_price=entry_price,
        position_size_usdt=position_size_usdt,
        target_profit_usd=target_profit_usd,
        leverage=leverage,
        position_side='LONG'
    )
    
    # Calcular cantidad comprada
    amount = position_size_usdt / entry_price
    
    # Verificar ganancia
    price_change = take_profit_price - entry_price
    profit = price_change * amount * leverage
    
    print(f"Precio de entrada: ${entry_price:.8f}")
    print(f"Precio de take profit: ${take_profit_price:.8f}")
    print(f"Margen usado: ${position_size_usdt:.2f} USDT")
    print(f"Apalancamiento: {leverage}x")
    print(f"Cantidad comprada: {amount:.2f} tokens")
    print(f"Cambio de precio: ${price_change:.8f}")
    print(f"Ganancia calculada: ${profit:.4f} USDT")
    print(f"Ganancia objetivo: ${target_profit_usd:.2f} USDT")
    print(f"Diferencia: ${abs(profit - target_profit_usd):.8f} USDT")
    
    # Verificar que la ganancia sea correcta (con tolerancia de 0.000001)
    assert abs(profit - target_profit_usd) < 0.000001, f"Ganancia incorrecta: {profit} != {target_profit_usd}"
    print("✅ Test LONG PASADO")


def test_short_position():
    """Prueba para posición SHORT"""
    print("\n" + "="*60)
    print("TEST: Posición SHORT")
    print("="*60)
    
    entry_price = 0.08  # $0.08 USDT
    position_size_usdt = 10.0  # 10 USDT de margen
    target_profit_usd = 2.0  # Queremos ganar 2 USDT
    leverage = 10
    
    # Calcular precio de take profit
    take_profit_price = utils.calculate_take_profit_price_for_fixed_usd(
        entry_price=entry_price,
        position_size_usdt=position_size_usdt,
        target_profit_usd=target_profit_usd,
        leverage=leverage,
        position_side='SHORT'
    )
    
    # Calcular cantidad vendida
    amount = position_size_usdt / entry_price
    
    # Verificar ganancia (en SHORT ganamos cuando el precio baja)
    price_change = entry_price - take_profit_price
    profit = price_change * amount * leverage
    
    print(f"Precio de entrada: ${entry_price:.8f}")
    print(f"Precio de take profit: ${take_profit_price:.8f}")
    print(f"Margen usado: ${position_size_usdt:.2f} USDT")
    print(f"Apalancamiento: {leverage}x")
    print(f"Cantidad vendida: {amount:.2f} tokens")
    print(f"Cambio de precio: ${price_change:.8f}")
    print(f"Ganancia calculada: ${profit:.4f} USDT")
    print(f"Ganancia objetivo: ${target_profit_usd:.2f} USDT")
    print(f"Diferencia: ${abs(profit - target_profit_usd):.8f} USDT")
    
    # Verificar que la ganancia sea correcta (con tolerancia de 0.000001)
    assert abs(profit - target_profit_usd) < 0.000001, f"Ganancia incorrecta: {profit} != {target_profit_usd}"
    print("✅ Test SHORT PASADO")


def test_different_scenarios():
    """Prueba con diferentes escenarios de precio y tamaño de posición"""
    print("\n" + "="*60)
    print("TEST: Diferentes escenarios")
    print("="*60)
    
    scenarios = [
        # (entry_price, position_size_usdt, target_profit, leverage, side)
        (0.00001, 5.0, 2.0, 50, 'LONG'),  # SHIB con 50x leverage
        (0.1, 20.0, 2.0, 5, 'LONG'),  # DOGE con 5x leverage
        (0.5, 10.0, 2.0, 10, 'SHORT'),  # Otro token con 10x leverage
        (1.5, 15.0, 2.0, 20, 'SHORT'),  # Token más caro con 20x leverage
    ]
    
    for i, (entry, size, target, lev, side) in enumerate(scenarios, 1):
        print(f"\n  Escenario {i}: {side} - Precio: ${entry:.8f}, Margen: ${size} USDT, Leverage: {lev}x")
        
        tp_price = utils.calculate_take_profit_price_for_fixed_usd(
            entry_price=entry,
            position_size_usdt=size,
            target_profit_usd=target,
            leverage=lev,
            position_side=side
        )
        
        amount = size / entry
        
        if side == 'LONG':
            price_change = tp_price - entry
        else:
            price_change = entry - tp_price
        
        profit = price_change * amount * lev
        
        print(f"     Take Profit: ${tp_price:.8f}")
        print(f"     Ganancia: ${profit:.4f} USDT (objetivo: ${target:.2f})")
        
        assert abs(profit - target) < 0.000001, f"Escenario {i} falló"
        print(f"     ✅ Escenario {i} PASADO")
    
    print("\n✅ Todos los escenarios PASARON")


if __name__ == "__main__":
    print("Ejecutando pruebas de cálculo de take profit para 2 USDT...")
    
    try:
        test_long_position()
        test_short_position()
        test_different_scenarios()
        
        print("\n" + "="*60)
        print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("="*60)
        print("\nLa lógica de cálculo de take profit para 2 USDT está funcionando correctamente.")
        print("El bot calculará automáticamente el precio de venta necesario para")
        print("obtener exactamente 2 USDT de ganancia en cada operación.")
        
    except AssertionError as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
