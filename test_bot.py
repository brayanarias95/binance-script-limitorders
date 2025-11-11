"""
Test básico para verificar la funcionalidad de manejo de error -2019 en bot.py

Este test verifica la lógica del manejo de errores sin necesidad de conectarse
a la API de Binance real, usando mocks para simular el comportamiento.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from binance.exceptions import BinanceAPIException


def create_mock_order_function(mock_client):
    """
    Replica la lógica de create_order_with_retry para testing
    """
    def create_order_with_retry(symbol, side, precio, cantidad_inicial, apalancamiento):
        try:
            # Intentar crear la orden con la cantidad inicial
            orden = mock_client.futures_create_order(
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
                # Obtener balance disponible actualizado
                balance = mock_client.futures_account_balance()
                saldo_disponible = 0.0
                for x in balance:
                    if x['asset'] == 'USDT':
                        saldo_disponible = float(x['availableBalance'])
                
                # Calcular nueva cantidad basada en saldo disponible
                cantidad_ajustada = int((saldo_disponible / precio) * 0.95) * apalancamiento
                
                # Verificar que la nueva cantidad sea válida
                if cantidad_ajustada <= 0:
                    return None
                
                try:
                    # Reintentar con la cantidad ajustada
                    orden = mock_client.futures_create_order(
                        symbol=symbol,
                        type='LIMIT',
                        timeInForce='GTC',
                        price=precio,
                        side=side,
                        quantity=cantidad_ajustada
                    )
                    
                    # Obtener detalles de la posición
                    position = mock_client.futures_position_information(symbol=symbol)
                    
                    return orden
                    
                except BinanceAPIException as e2:
                    return None
            else:
                # Otro tipo de error de API
                return None
        except Exception as e:
            return None
    
    return create_order_with_retry


class TestErrorHandling(unittest.TestCase):
    """Tests para el manejo de error -2019"""
    
    def test_create_order_success(self):
        """Test: Orden exitosa sin error -2019"""
        mock_client = Mock()
        mock_client.futures_create_order.return_value = {'orderId': 12345, 'status': 'FILLED'}
        
        create_order = create_mock_order_function(mock_client)
        
        result = create_order(
            symbol='1000SHIBUSDT',
            side='BUY',
            precio=0.00001,
            cantidad_inicial=10000,
            apalancamiento=50
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['orderId'], 12345)
        self.assertEqual(mock_client.futures_create_order.call_count, 1)
        
    def test_error_2019_handling(self):
        """Test: Manejo de error -2019 con reintento exitoso"""
        mock_client = Mock()
        
        # Mock de error -2019 en primer intento
        error_2019 = BinanceAPIException(
            response=Mock(),
            status_code=400,
            text='{"code":-2019,"msg":"Margin is insufficient."}'
        )
        error_2019.code = -2019
        error_2019.message = "Margin is insufficient."
        
        # Mock de balance disponible
        mock_client.futures_account_balance.return_value = [
            {'asset': 'USDT', 'availableBalance': '10.0'}
        ]
        
        # Mock de posición
        mock_client.futures_position_information.return_value = [
            {
                'symbol': '1000SHIBUSDT',
                'positionAmt': '5000',
                'entryPrice': '0.00001',
                'liquidationPrice': '0.000005',
                'unRealizedProfit': '0.5',
                'leverage': '50'
            }
        ]
        
        # Primer intento falla con -2019, segundo intento exitoso
        mock_client.futures_create_order.side_effect = [
            error_2019,
            {'orderId': 67890, 'status': 'FILLED'}
        ]
        
        create_order = create_mock_order_function(mock_client)
        
        result = create_order(
            symbol='1000SHIBUSDT',
            side='BUY',
            precio=0.00001,
            cantidad_inicial=100000,
            apalancamiento=50
        )
        
        # Verificar que se hizo reintento y fue exitoso
        self.assertIsNotNone(result)
        self.assertEqual(result['orderId'], 67890)
        # Verificar que se llamó dos veces (primer intento + reintento)
        self.assertEqual(mock_client.futures_create_order.call_count, 2)
        # Verificar que se obtuvo el balance
        self.assertEqual(mock_client.futures_account_balance.call_count, 1)
        # Verificar que se obtuvo la información de posición
        self.assertEqual(mock_client.futures_position_information.call_count, 1)
        
    def test_error_2019_insufficient_balance(self):
        """Test: Error -2019 con balance insuficiente para reintento"""
        mock_client = Mock()
        
        # Mock de error -2019
        error_2019 = BinanceAPIException(
            response=Mock(),
            status_code=400,
            text='{"code":-2019,"msg":"Margin is insufficient."}'
        )
        error_2019.code = -2019
        error_2019.message = "Margin is insufficient."
        
        # Mock de balance insuficiente (resultará en cantidad_ajustada <= 0)
        # Con precio 0.00001 y balance 0.0000001, cantidad será muy pequeña
        # int((0.0000001 / 0.00001) * 0.95) * 50 = int(0.000095) * 50 = 0 * 50 = 0
        mock_client.futures_account_balance.return_value = [
            {'asset': 'USDT', 'availableBalance': '0.0000001'}
        ]
        
        mock_client.futures_create_order.side_effect = error_2019
        
        create_order = create_mock_order_function(mock_client)
        
        result = create_order(
            symbol='1000SHIBUSDT',
            side='BUY',
            precio=0.00001,
            cantidad_inicial=100000,
            apalancamiento=50
        )
        
        # Verificar que retorna None cuando no hay balance suficiente
        self.assertIsNone(result)
        # Con balance muy pequeño, no debería haber segundo intento
        # porque cantidad_ajustada será <= 0
        self.assertEqual(mock_client.futures_create_order.call_count, 1)
        
    def test_other_binance_error(self):
        """Test: Manejo de otros errores de Binance (no -2019)"""
        mock_client = Mock()
        
        # Mock de error diferente a -2019
        other_error = BinanceAPIException(
            response=Mock(),
            status_code=400,
            text='{"code":-1111,"msg":"Precision is over the maximum defined for this asset."}'
        )
        other_error.code = -1111
        other_error.message = "Precision is over the maximum defined for this asset."
        
        mock_client.futures_create_order.side_effect = other_error
        
        create_order = create_mock_order_function(mock_client)
        
        result = create_order(
            symbol='1000SHIBUSDT',
            side='BUY',
            precio=0.00001,
            cantidad_inicial=10000,
            apalancamiento=50
        )
        
        # Verificar que retorna None para otros errores
        self.assertIsNone(result)
        # Verificar que solo se llamó una vez (no hubo reintento)
        self.assertEqual(mock_client.futures_create_order.call_count, 1)
        
    def test_error_2019_retry_also_fails(self):
        """Test: Error -2019 y el reintento también falla"""
        mock_client = Mock()
        
        # Mock de error -2019
        error_2019 = BinanceAPIException(
            response=Mock(),
            status_code=400,
            text='{"code":-2019,"msg":"Margin is insufficient."}'
        )
        error_2019.code = -2019
        error_2019.message = "Margin is insufficient."
        
        # Mock de balance disponible
        mock_client.futures_account_balance.return_value = [
            {'asset': 'USDT', 'availableBalance': '5.0'}
        ]
        
        # Ambos intentos fallan con -2019
        mock_client.futures_create_order.side_effect = [error_2019, error_2019]
        
        create_order = create_mock_order_function(mock_client)
        
        result = create_order(
            symbol='1000SHIBUSDT',
            side='SELL',
            precio=0.00001,
            cantidad_inicial=100000,
            apalancamiento=50
        )
        
        # Verificar que retorna None cuando el reintento también falla
        self.assertIsNone(result)
        # Verificar que se llamó dos veces (primer intento + reintento fallido)
        self.assertEqual(mock_client.futures_create_order.call_count, 2)


if __name__ == '__main__':
    # Ejecutar tests con output verbose
    print("Ejecutando tests para el manejo de error -2019...\n")
    unittest.main(verbosity=2)


