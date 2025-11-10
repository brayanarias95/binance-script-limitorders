"""
Bot de Scalping para Binance usando CCXT
Estrategia basada en EMA de 20 periodos con Take Profit y Stop Loss

El bot opera en modo sandbox por defecto (paper trading).
Para activar el trading real, cambiar ENABLE_REAL_TRADING a True en config.py
"""

import ccxt
import time
import sys
from datetime import datetime, timedelta
import config
import utils


class ScalpingBot:
    """
    Bot de trading tipo scalping para Binance (Futures)
    """
    
    def __init__(self):
        """
        Inicializa el bot con la configuración de config.py
        """
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.ema_period = config.EMA_PERIOD
        self.position_size = config.POSITION_SIZE_USDT
        self.take_profit = config.TAKE_PROFIT_PERCENT
        self.stop_loss = config.STOP_LOSS_PERCENT
        self.loop_interval = config.LOOP_INTERVAL
        self.enable_real_trading = config.ENABLE_REAL_TRADING
        self.cooldown_seconds = config.COOLDOWN_SECONDS
        self.enable_short_positions = config.ENABLE_SHORT_POSITIONS
        
        # Configuración de Futures
        self.use_futures = config.USE_FUTURES
        self.leverage = config.LEVERAGE
        self.margin_mode = config.MARGIN_MODE
        
        # Estado del bot
        self.in_position = False
        self.entry_price = 0.0
        self.position_amount = 0.0
        self.position_side = None  # 'LONG' o 'SHORT'
        self.last_close_time = None  # Timestamp de última posición cerrada
        
        # Estadísticas
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit_usd = 0.0
        
        # Configurar exchange
        self.exchange = self._setup_exchange()
        
        # Mostrar configuración
        self._print_configuration()
    
    def _setup_exchange(self) -> ccxt.Exchange:
        """
        Configura y retorna la instancia del exchange de Binance
        
        Returns:
            Instancia configurada de ccxt.binance
        """
        try:
            # Determinar tipo de mercado
            market_type = 'future' if self.use_futures else 'spot'
            
            exchange = ccxt.binance({
                'apiKey': config.API_KEY,
                'secret': config.API_SECRET,
                'enableRateLimit': True,
                'options': {
                    'defaultType': market_type,
                    'recvWindow': 60000,
                }
            })
            
            # Configurar para sandbox/testnet si está habilitado
            if config.USE_SANDBOX and not self.enable_real_trading:
                exchange.set_sandbox_mode(True)
                print("⚠️  MODO SANDBOX ACTIVADO - No se usará dinero real")
            
            # Sincronizar tiempo con el servidor de Binance
            print("🕐 Sincronizando tiempo con el servidor...")
            exchange.load_time_difference()
            
            # Verificar conexión
            exchange.load_markets()
            print(f"✅ Conectado a Binance exitosamente")
            
            # Configurar apalancamiento y margin mode si es Futures
            if self.use_futures:
                try:
                    # Establecer apalancamiento
                    exchange.fapiPrivate_post_leverage({
                        'symbol': self.symbol.replace('/', ''),
                        'leverage': self.leverage
                    })
                    print(f"✅ Apalancamiento configurado: {self.leverage}x")
                    
                    # Establecer modo de margen (isolated/cross)
                    margin_type = 'ISOLATED' if self.margin_mode == 'isolated' else 'CROSSED'
                    exchange.fapiPrivate_post_margintype({
                        'symbol': self.symbol.replace('/', ''),
                        'marginType': margin_type
                    })
                    print(f"✅ Modo de margen: {margin_type}")
                    
                except Exception as e:
                    print(f"⚠️  Advertencia al configurar Futures: {e}")
                    print(f"   (Es normal si ya estaba configurado)")
            
            return exchange
        except Exception as e:
            print(f"❌ Error configurando exchange: {e}")
            sys.exit(1)
    
    def _print_configuration(self):
        """
        Muestra la configuración actual del bot
        """
        print("\n" + "="*60)
        print("🤖 BOT DE SCALPING - CONFIGURACIÓN")
        print("="*60)
        print(f"Símbolo: {self.symbol}")
        print(f"Mercado: {'FUTURES' if self.use_futures else 'SPOT'}")
        
        if self.use_futures:
            print(f"Apalancamiento: {self.leverage}x")
            print(f"Modo de margen: {self.margin_mode.upper()}")
            print(f"Posiciones SHORT: {'HABILITADAS' if self.enable_short_positions else 'DESHABILITADAS'}")
        
        print(f"Timeframe: {self.timeframe}")
        print(f"Periodo EMA: {self.ema_period}")
        print(f"Tamaño de posición: {self.position_size} USDT")
        
        if self.use_futures:
            print(f"Control efectivo: {self.position_size * self.leverage} USDT (con {self.leverage}x)")
        
        print(f"Take Profit: +{self.take_profit}%")
        print(f"Stop Loss: -{self.stop_loss}%")
        print(f"Intervalo de loop: {self.loop_interval} segundos")
        print(f"Cooldown: {self.cooldown_seconds} segundos")
        
        if self.enable_real_trading:
            print("⚠️  TRADING REAL ACTIVADO ⚠️")
        else:
            print("📝 MODO SIMULACIÓN (Paper Trading)")
        
        print("="*60 + "\n")
    
    def run(self):
        """
        Loop principal del bot
        """
        print(f"🚀 Iniciando bot de scalping...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                # Ejecutar ciclo de trading
                self._trading_cycle()
                
                # Resetear contador de reintentos si el ciclo fue exitoso
                retry_count = 0
                
                # Esperar antes del próximo ciclo
                time.sleep(self.loop_interval)
                
            except ccxt.NetworkError as e:
                retry_count += 1
                print(f"\n⚠️  Error de red ({retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    print("❌ Máximo de reintentos alcanzado. Deteniendo bot...")
                    break
                
                print(f"🔄 Reintentando en {self.loop_interval * 2} segundos...")
                time.sleep(self.loop_interval * 2)
                
            except ccxt.ExchangeError as e:
                print(f"\n❌ Error del exchange: {e}")
                print(f"⏸️  Pausando por {self.loop_interval * 2} segundos...")
                time.sleep(self.loop_interval * 2)
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Bot detenido por el usuario")
                if self.in_position:
                    print(f"⚠️  ADVERTENCIA: Hay una posición abierta en {self.symbol}")
                    print(f"   Precio de entrada: ${self.entry_price:.2f}")
                break
                
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}")
                print(f"⏸️  Pausando por {self.loop_interval * 2} segundos...")
                time.sleep(self.loop_interval * 2)
    
    def _trading_cycle(self):
        """
        Ejecuta un ciclo completo de la estrategia de trading
        """
        # Obtener precio actual
        current_price = utils.get_current_price(self.exchange, self.symbol)
        if current_price is None:
            print("⚠️  No se pudo obtener el precio actual")
            return
        
        # Obtener datos históricos para calcular EMA
        ohlcv_data = utils.get_ohlcv_data(
            self.exchange, 
            self.symbol, 
            self.timeframe, 
            limit=self.ema_period + 10
        )
        
        if ohlcv_data is None or len(ohlcv_data) < self.ema_period:
            print("⚠️  No hay suficientes datos para calcular EMA")
            return
        
        # Calcular EMA
        ema = utils.calculate_ema(ohlcv_data, self.ema_period)
        if ema is None:
            print("⚠️  No se pudo calcular la EMA")
            return
        
        # Mostrar información actual
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] 📊 Estado del mercado:")
        print(f"  💰 Precio actual: ${current_price:.2f}")
        print(f"  📈 EMA({self.ema_period}): ${ema:.2f}")
        
        # Lógica de trading
        if not self.in_position:
            # Verificar cooldown antes de abrir nueva posición
            if self.last_close_time:
                time_since_close = (datetime.now() - self.last_close_time).total_seconds()
                if time_since_close < self.cooldown_seconds:
                    remaining = int(self.cooldown_seconds - time_since_close)
                    print(f"  ⏳ Cooldown activo: esperar {remaining}s antes de nueva posición")
                    return
            
            # No estamos en posición - buscar señal de compra o venta
            if utils.should_buy(current_price, ema):
                self._execute_buy(current_price, 'LONG')
            elif self.use_futures and self.enable_short_positions and utils.should_sell_short(current_price, ema):
                self._execute_buy(current_price, 'SHORT')
        else:
            # Estamos en posición - verificar si debemos cerrar
            if self.position_side == 'LONG':
                profit_loss_percent = utils.calculate_profit_loss_percent(
                    self.entry_price, 
                    current_price
                )
            else:  # SHORT
                profit_loss_percent = -utils.calculate_profit_loss_percent(
                    self.entry_price, 
                    current_price
                )
            
            position_emoji = "🟢" if self.position_side == 'LONG' else "🔴"
            print(f"  {position_emoji} En posición {self.position_side} desde: ${self.entry_price:.2f}")
            
            # Mostrar P/L con color
            if profit_loss_percent >= 0:
                print(f"  💹 P/L: +{profit_loss_percent:.2f}% (ganancia)")
            else:
                print(f"  📉 P/L: {profit_loss_percent:.2f}% (pérdida)")
            
            # Verificar condiciones de salida
            should_exit, reason = utils.should_sell(
                self.entry_price,
                current_price,
                self.take_profit,
                self.stop_loss,
                self.position_side
            )
            
            if should_exit:
                self._execute_sell(current_price, reason)
    
    def _execute_buy(self, current_price: float, position_side: str):
        """
        Ejecuta una orden de compra (LONG o SHORT)
        
        Args:
            current_price: Precio actual del activo
            position_side: 'LONG' o 'SHORT'
        """
        side_emoji = "🟢" if position_side == 'LONG' else "🔴"
        signal_text = "COMPRA (LONG)" if position_side == 'LONG' else "VENTA (SHORT)"
        
        print(f"\n{side_emoji} SEÑAL DE {signal_text} DETECTADA")
        print(f"   Precio: ${current_price:.2f}")
        
        if position_side == 'LONG':
            order = utils.create_market_buy_order(
                self.exchange,
                self.symbol,
                self.position_size,
                self.enable_real_trading,
                self.use_futures
            )
        else:  # SHORT
            order = utils.create_short_order(
                self.exchange,
                self.symbol,
                self.position_size,
                self.enable_real_trading
            )
        
        if order:
            self.in_position = True
            self.entry_price = current_price
            self.position_side = position_side
            
            # Calcular cantidad comprada (aproximada en modo simulación)
            base_currency = self.symbol.split('/')[0]
            self.position_amount = self.position_size / current_price
            
            print(f"✅ Orden {position_side} ejecutada")
            print(f"   Precio de entrada: ${self.entry_price:.2f}")
            print(f"   Cantidad: {self.position_amount:.6f} {base_currency}")
            print(f"   Margen: {self.position_size} USDT")
            
            if self.use_futures:
                effective_size = self.position_size * self.leverage
                print(f"   Control efectivo: {effective_size} USDT (apalancamiento {self.leverage}x)")
            
            if not self.enable_real_trading:
                print(f"   [SIMULACIÓN - No se ejecutó orden real]")
        else:
            print(f"❌ No se pudo ejecutar la orden {position_side}")
    
    def _execute_sell(self, current_price: float, reason: str):
        """
        Ejecuta una orden de cierre de posición
        
        Args:
            current_price: Precio actual del activo
            reason: Razón de la venta (TP o SL)
        """
        side_emoji = "🟢" if self.position_side == 'LONG' else "🔴"
        print(f"\n{side_emoji} SEÑAL DE CIERRE {self.position_side} DETECTADA")
        print(f"   Razón: {reason}")
        
        if self.position_side == 'LONG':
            order = utils.create_market_sell_order(
                self.exchange,
                self.symbol,
                self.position_amount,
                self.enable_real_trading,
                self.use_futures,
                self.position_side
            )
        else:  # SHORT
            order = utils.close_short_order(
                self.exchange,
                self.symbol,
                self.position_amount,
                self.enable_real_trading
            )
        
        if order:
            # Calcular P/L
            if self.position_side == 'LONG':
                profit_loss_percent = utils.calculate_profit_loss_percent(
                    self.entry_price,
                    current_price
                )
                profit_loss_usd = (current_price - self.entry_price) * self.position_amount
            else:  # SHORT
                profit_loss_percent = -utils.calculate_profit_loss_percent(
                    self.entry_price,
                    current_price
                )
                profit_loss_usd = (self.entry_price - current_price) * self.position_amount
            
            # Aplicar apalancamiento al cálculo de ganancias en Futures
            if self.use_futures:
                profit_loss_usd *= self.leverage
            
            print(f"✅ Posición {self.position_side} cerrada")
            print(f"   Precio de entrada: ${self.entry_price:.2f}")
            print(f"   Precio de salida: ${current_price:.2f}")
            print(f"   Cantidad: {self.position_amount:.6f}")
            
            if profit_loss_percent >= 0:
                print(f"   💰 Ganancia: +{profit_loss_percent:.2f}% (+${profit_loss_usd:.2f})")
                self.winning_trades += 1
            else:
                print(f"   💸 Pérdida: {profit_loss_percent:.2f}% (${profit_loss_usd:.2f})")
                self.losing_trades += 1
            
            # Actualizar estadísticas
            self.total_trades += 1
            self.total_profit_usd += profit_loss_usd
            
            # Mostrar estadísticas acumuladas
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            print(f"\n📊 ESTADÍSTICAS:")
            print(f"   Total trades: {self.total_trades}")
            print(f"   Ganadores: {self.winning_trades} | Perdedores: {self.losing_trades}")
            print(f"   Win rate: {win_rate:.1f}%")
            print(f"   P/L Total: ${self.total_profit_usd:.2f} USD")
            
            if not self.enable_real_trading:
                print(f"   [SIMULACIÓN - No se ejecutó orden real]")
            
            # Resetear estado y activar cooldown
            self.in_position = False
            self.entry_price = 0.0
            self.position_amount = 0.0
            self.position_side = None
            self.last_close_time = datetime.now()
            
            print(f"\n   ⏳ Cooldown activado: {self.cooldown_seconds}s antes de nueva posición")
        else:
            print(f"❌ No se pudo cerrar la posición {self.position_side}")


def main():
    """
    Función principal para iniciar el bot
    """
    # Verificar que las credenciales estén configuradas
    if config.API_KEY == 'your api key' or config.API_SECRET == 'your api secret':
        print("❌ ERROR: Configura tus credenciales de API en config.py")
        print("   Para obtener credenciales: https://www.binance.com/en/my/settings/api-management")
        
        if config.USE_SANDBOX:
            print("\n💡 NOTA: Estás en modo SANDBOX. Puedes usar credenciales de testnet:")
            print("   https://testnet.binance.vision/")
        
        return
    
    # Advertencia si el trading real está activado
    if config.ENABLE_REAL_TRADING:
        print("\n" + "="*60)
        print("⚠️  ADVERTENCIA: TRADING REAL ACTIVADO ⚠️")
        print("="*60)
        print("Este bot ejecutará órdenes REALES en Binance.")
        print("Asegúrate de entender los riesgos antes de continuar.")
        print("="*60)
        
        response = input("\n¿Estás seguro de continuar con trading real? (escribe 'SI' para confirmar): ")
        if response != 'SI':
            print("❌ Operación cancelada por el usuario")
            return
    
    # Crear e iniciar el bot
    bot = ScalpingBot()
    bot.run()


if __name__ == "__main__":
    main()
