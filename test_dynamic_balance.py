"""
Test para verificar la funcionalidad de tamaño de posición dinámico basado en balance
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, '/home/runner/work/binance-script-limitorders/binance-script-limitorders')

import utils
import config
from main import ScalpingBot


class TestDynamicPositionSize(unittest.TestCase):
    """Tests para el tamaño de posición dinámico"""
    
    def test_get_futures_available_balance_success(self):
        """Test: Obtener balance de Futures exitosamente"""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            'free': {'USDT': 100.0},
            'used': {'USDT': 20.0},
            'total': {'USDT': 120.0}
        }
        
        balance = utils.get_futures_available_balance(mock_exchange, 'USDT')
        
        self.assertIsNotNone(balance)
        self.assertEqual(balance, 100.0)
        self.assertEqual(mock_exchange.fetch_balance.call_count, 1)
    
    def test_get_futures_available_balance_no_funds(self):
        """Test: Balance de Futures con 0 USDT"""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            'free': {'USDT': 0.0},
            'used': {'USDT': 0.0},
            'total': {'USDT': 0.0}
        }
        
        balance = utils.get_futures_available_balance(mock_exchange, 'USDT')
        
        self.assertIsNotNone(balance)
        self.assertEqual(balance, 0.0)
    
    def test_get_futures_available_balance_error(self):
        """Test: Error al obtener balance de Futures"""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.side_effect = Exception("Network error")
        
        balance = utils.get_futures_available_balance(mock_exchange, 'USDT')
        
        self.assertIsNone(balance)
    
    def test_get_futures_available_balance_currency_not_found(self):
        """Test: Moneda no encontrada en balance"""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            'free': {'BTC': 0.5},
            'used': {},
            'total': {'BTC': 0.5}
        }
        
        balance = utils.get_futures_available_balance(mock_exchange, 'USDT')
        
        self.assertIsNotNone(balance)
        self.assertEqual(balance, 0.0)
    
    @patch('config.USE_DYNAMIC_POSITION_SIZE', True)
    @patch('config.POSITION_SIZE_PERCENT', 10)
    @patch('config.POSITION_SIZE_USDT', 5)
    @patch('config.USE_FUTURES', True)
    def test_get_position_size_dynamic(self):
        """Test: Calcular tamaño de posición dinámico"""
        # Mock de exchange con balance de 100 USDT
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            'free': {'USDT': 100.0}
        }
        
        # Crear una instancia temporal con mocks
        with patch('main.config') as mock_config:
            mock_config.SYMBOL = 'DOGE/USDT'
            mock_config.TIMEFRAME = '1m'
            mock_config.EMA_PERIOD = 12
            mock_config.POSITION_SIZE_USDT = 5
            mock_config.USE_DYNAMIC_POSITION_SIZE = True
            mock_config.POSITION_SIZE_PERCENT = 10
            mock_config.TAKE_PROFIT_PERCENT = 0.6
            mock_config.STOP_LOSS_PERCENT = 0.4
            mock_config.LOOP_INTERVAL = 3
            mock_config.ENABLE_REAL_TRADING = False
            mock_config.COOLDOWN_SECONDS = 60
            mock_config.ENABLE_SHORT_POSITIONS = True
            mock_config.USE_STOP_LIMIT = False
            mock_config.STOP_LIMIT_OFFSET_PERCENT = 0.1
            mock_config.USE_FUTURES = True
            mock_config.LEVERAGE = 10
            mock_config.MARGIN_MODE = 'isolated'
            mock_config.API_KEY = 'test_key'
            mock_config.API_SECRET = 'test_secret'
            mock_config.USE_SANDBOX = False
            
            with patch('main.ccxt.binance') as mock_binance:
                mock_binance.return_value = mock_exchange
                mock_exchange.load_time_difference = Mock()
                mock_exchange.load_markets = Mock()
                mock_exchange.set_sandbox_mode = Mock()
                mock_exchange.fapiPrivate_post_leverage = Mock()
                mock_exchange.fapiPrivate_post_margintype = Mock()
                
                # Instanciar el bot
                bot = ScalpingBot()
                bot.exchange = mock_exchange
                
                # Obtener tamaño de posición
                position_size = bot._get_position_size()
                
                # Con 100 USDT y 10%, debería ser 10 USDT
                self.assertEqual(position_size, 10.0)
    
    @patch('config.USE_DYNAMIC_POSITION_SIZE', False)
    @patch('config.POSITION_SIZE_USDT', 5)
    def test_get_position_size_static(self):
        """Test: Usar tamaño de posición estático"""
        mock_exchange = Mock()
        
        # Crear una instancia temporal con mocks
        with patch('main.config') as mock_config:
            mock_config.SYMBOL = 'DOGE/USDT'
            mock_config.TIMEFRAME = '1m'
            mock_config.EMA_PERIOD = 12
            mock_config.POSITION_SIZE_USDT = 5
            mock_config.USE_DYNAMIC_POSITION_SIZE = False
            mock_config.POSITION_SIZE_PERCENT = 10
            mock_config.TAKE_PROFIT_PERCENT = 0.6
            mock_config.STOP_LOSS_PERCENT = 0.4
            mock_config.LOOP_INTERVAL = 3
            mock_config.ENABLE_REAL_TRADING = False
            mock_config.COOLDOWN_SECONDS = 60
            mock_config.ENABLE_SHORT_POSITIONS = True
            mock_config.USE_STOP_LIMIT = False
            mock_config.STOP_LIMIT_OFFSET_PERCENT = 0.1
            mock_config.USE_FUTURES = True
            mock_config.LEVERAGE = 10
            mock_config.MARGIN_MODE = 'isolated'
            mock_config.API_KEY = 'test_key'
            mock_config.API_SECRET = 'test_secret'
            mock_config.USE_SANDBOX = False
            
            with patch('main.ccxt.binance') as mock_binance:
                mock_binance.return_value = mock_exchange
                mock_exchange.load_time_difference = Mock()
                mock_exchange.load_markets = Mock()
                mock_exchange.set_sandbox_mode = Mock()
                mock_exchange.fapiPrivate_post_leverage = Mock()
                mock_exchange.fapiPrivate_post_margintype = Mock()
                
                # Instanciar el bot
                bot = ScalpingBot()
                bot.exchange = mock_exchange
                
                # Obtener tamaño de posición
                position_size = bot._get_position_size()
                
                # Debería ser el valor estático configurado
                self.assertEqual(position_size, 5)
    
    @patch('config.USE_DYNAMIC_POSITION_SIZE', True)
    @patch('config.POSITION_SIZE_PERCENT', 50)
    @patch('config.POSITION_SIZE_USDT', 5)
    @patch('config.USE_FUTURES', True)
    def test_get_position_size_dynamic_small_balance(self):
        """Test: Tamaño de posición dinámico con balance pequeño debe usar mínimo"""
        # Mock de exchange con balance muy pequeño (2 USDT)
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            'free': {'USDT': 2.0}
        }
        
        # Crear una instancia temporal con mocks
        with patch('main.config') as mock_config:
            mock_config.SYMBOL = 'DOGE/USDT'
            mock_config.TIMEFRAME = '1m'
            mock_config.EMA_PERIOD = 12
            mock_config.POSITION_SIZE_USDT = 5
            mock_config.USE_DYNAMIC_POSITION_SIZE = True
            mock_config.POSITION_SIZE_PERCENT = 50
            mock_config.TAKE_PROFIT_PERCENT = 0.6
            mock_config.STOP_LOSS_PERCENT = 0.4
            mock_config.LOOP_INTERVAL = 3
            mock_config.ENABLE_REAL_TRADING = False
            mock_config.COOLDOWN_SECONDS = 60
            mock_config.ENABLE_SHORT_POSITIONS = True
            mock_config.USE_STOP_LIMIT = False
            mock_config.STOP_LIMIT_OFFSET_PERCENT = 0.1
            mock_config.USE_FUTURES = True
            mock_config.LEVERAGE = 10
            mock_config.MARGIN_MODE = 'isolated'
            mock_config.API_KEY = 'test_key'
            mock_config.API_SECRET = 'test_secret'
            mock_config.USE_SANDBOX = False
            
            with patch('main.ccxt.binance') as mock_binance:
                mock_binance.return_value = mock_exchange
                mock_exchange.load_time_difference = Mock()
                mock_exchange.load_markets = Mock()
                mock_exchange.set_sandbox_mode = Mock()
                mock_exchange.fapiPrivate_post_leverage = Mock()
                mock_exchange.fapiPrivate_post_margintype = Mock()
                
                # Instanciar el bot
                bot = ScalpingBot()
                bot.exchange = mock_exchange
                
                # Obtener tamaño de posición
                position_size = bot._get_position_size()
                
                # Con 2 USDT y 50% sería 1 USDT, pero debe usar mínimo de 5.5 USDT
                self.assertEqual(position_size, 5.5)


if __name__ == '__main__':
    # Ejecutar tests con output verbose
    print("Ejecutando tests para tamaño de posición dinámico...\n")
    unittest.main(verbosity=2)
