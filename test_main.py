"""
Test para verificar la funcionalidad de los nuevos modos de operación
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import utils
import main


class TestLimitOrders(unittest.TestCase):
    """Tests para las órdenes limit"""
    
    def test_create_limit_buy_order_simulated(self):
        """Test: Crear orden limit de compra en modo simulación"""
        mock_exchange = Mock()
        
        order = utils.create_limit_buy_order(
            exchange=mock_exchange,
            symbol='DOGE/USDT',
            amount_usdt=10,
            limit_price=0.08,
            enable_real_trading=False
        )
        
        self.assertIsNotNone(order)
        self.assertEqual(order['type'], 'limit')
        self.assertEqual(order['side'], 'buy')
        self.assertEqual(order['price'], 0.08)
        self.assertTrue(order['simulated'])
    
    def test_create_limit_sell_order_simulated(self):
        """Test: Crear orden limit de venta en modo simulación"""
        mock_exchange = Mock()
        
        order = utils.create_limit_sell_order(
            exchange=mock_exchange,
            symbol='DOGE/USDT',
            amount=125.0,
            limit_price=0.08,
            enable_real_trading=False,
            position_side='LONG'
        )
        
        self.assertIsNotNone(order)
        self.assertEqual(order['type'], 'limit')
        self.assertEqual(order['side'], 'sell')
        self.assertEqual(order['price'], 0.08)
        self.assertTrue(order['simulated'])
    
    def test_create_limit_short_order_simulated(self):
        """Test: Crear orden limit SHORT en modo simulación"""
        mock_exchange = Mock()
        
        order = utils.create_limit_short_order(
            exchange=mock_exchange,
            symbol='DOGE/USDT',
            amount_usdt=10,
            limit_price=0.08,
            enable_real_trading=False
        )
        
        self.assertIsNotNone(order)
        self.assertEqual(order['type'], 'limit')
        self.assertEqual(order['side'], 'sell')
        self.assertEqual(order['price'], 0.08)
        self.assertTrue(order['simulated'])
        self.assertEqual(order['positionSide'], 'SHORT')
    
    def test_get_open_positions_no_position(self):
        """Test: Verificar cuando no hay posiciones abiertas"""
        mock_exchange = Mock()
        
        # Simular respuesta sin posiciones abiertas
        mock_exchange.fetch_positions.return_value = [
            {
                'symbol': 'DOGE/USDT',
                'contracts': 0,
                'entryPrice': 0,
                'markPrice': 0.08,
                'unrealizedPnl': 0,
                'leverage': 10
            }
        ]
        
        position = utils.get_open_positions(mock_exchange, 'DOGE/USDT')
        
        self.assertIsNone(position)
    
    def test_get_open_positions_with_long(self):
        """Test: Verificar cuando hay posición LONG abierta"""
        mock_exchange = Mock()
        
        # Simular respuesta con posición LONG abierta
        mock_exchange.fetch_positions.return_value = [
            {
                'symbol': 'DOGE/USDT',
                'contracts': 125.5,  # Positivo = LONG
                'entryPrice': 0.08,
                'markPrice': 0.082,
                'unrealizedPnl': 2.5,
                'leverage': 10
            }
        ]
        
        position = utils.get_open_positions(mock_exchange, 'DOGE/USDT')
        
        self.assertIsNotNone(position)
        self.assertEqual(position['side'], 'LONG')
        self.assertEqual(position['contracts'], 125.5)
        self.assertEqual(position['entryPrice'], 0.08)
        self.assertEqual(position['unrealizedPnl'], 2.5)
    
    def test_get_open_positions_with_short(self):
        """Test: Verificar cuando hay posición SHORT abierta"""
        mock_exchange = Mock()
        
        # Simular respuesta con posición SHORT abierta
        mock_exchange.fetch_positions.return_value = [
            {
                'symbol': 'DOGE/USDT',
                'contracts': -125.5,  # Negativo = SHORT
                'entryPrice': 0.08,
                'markPrice': 0.078,
                'unrealizedPnl': 2.5,
                'leverage': 10
            }
        ]
        
        position = utils.get_open_positions(mock_exchange, 'DOGE/USDT')
        
        self.assertIsNotNone(position)
        self.assertEqual(position['side'], 'SHORT')
        self.assertEqual(position['contracts'], 125.5)  # Debe ser valor absoluto
        self.assertEqual(position['entryPrice'], 0.08)


class TestBotModes(unittest.TestCase):
    """Tests para los modos de operación del bot"""
    
    @patch('main.config')
    @patch('main.utils')
    @patch('main.ccxt.binance')
    def test_bot_initialization_automatic(self, mock_binance, mock_utils, mock_config):
        """Test: Inicializar bot en modo automático"""
        # Configurar mocks
        mock_config.API_KEY = 'test_key'
        mock_config.API_SECRET = 'test_secret'
        mock_config.SYMBOL = 'DOGE/USDT'
        mock_config.TIMEFRAME = '1m'
        mock_config.EMA_PERIOD = 12
        mock_config.POSITION_SIZE_USDT = 5
        mock_config.TAKE_PROFIT_PERCENT = 0.6
        mock_config.STOP_LOSS_PERCENT = 0.4
        mock_config.LOOP_INTERVAL = 3
        mock_config.ENABLE_REAL_TRADING = False
        mock_config.COOLDOWN_SECONDS = 60
        mock_config.ENABLE_SHORT_POSITIONS = True
        mock_config.USE_STOP_LIMIT = True
        mock_config.STOP_LIMIT_OFFSET_PERCENT = 0.1
        mock_config.USE_FUTURES = True
        mock_config.LEVERAGE = 10
        mock_config.MARGIN_MODE = 'isolated'
        mock_config.USE_SANDBOX = False
        
        # Mock exchange
        mock_exchange = Mock()
        mock_exchange.load_markets.return_value = {}
        mock_binance.return_value = mock_exchange
        
        # Crear bot
        bot = main.ScalpingBot(operation_mode='automatic')
        
        self.assertEqual(bot.operation_mode, 'automatic')
        self.assertEqual(bot.symbol, 'DOGE/USDT')
        self.assertFalse(bot.in_position)
    
    @patch('main.config')
    @patch('main.utils')
    @patch('main.ccxt.binance')
    def test_bot_initialization_manual(self, mock_binance, mock_utils, mock_config):
        """Test: Inicializar bot en modo manual"""
        # Configurar mocks
        mock_config.API_KEY = 'test_key'
        mock_config.API_SECRET = 'test_secret'
        mock_config.SYMBOL = 'DOGE/USDT'
        mock_config.TIMEFRAME = '1m'
        mock_config.EMA_PERIOD = 12
        mock_config.POSITION_SIZE_USDT = 5
        mock_config.TAKE_PROFIT_PERCENT = 0.6
        mock_config.STOP_LOSS_PERCENT = 0.4
        mock_config.LOOP_INTERVAL = 3
        mock_config.ENABLE_REAL_TRADING = False
        mock_config.COOLDOWN_SECONDS = 60
        mock_config.ENABLE_SHORT_POSITIONS = True
        mock_config.USE_STOP_LIMIT = True
        mock_config.STOP_LIMIT_OFFSET_PERCENT = 0.1
        mock_config.USE_FUTURES = True
        mock_config.LEVERAGE = 10
        mock_config.MARGIN_MODE = 'isolated'
        mock_config.USE_SANDBOX = False
        
        # Mock exchange
        mock_exchange = Mock()
        mock_exchange.load_markets.return_value = {}
        mock_binance.return_value = mock_exchange
        
        # Crear bot
        bot = main.ScalpingBot(operation_mode='manual')
        
        self.assertEqual(bot.operation_mode, 'manual')
        self.assertEqual(bot.symbol, 'DOGE/USDT')
        self.assertFalse(bot.in_position)


if __name__ == '__main__':
    # Ejecutar tests con output verbose
    print("Ejecutando tests para los nuevos modos de operación...\n")
    unittest.main(verbosity=2)
