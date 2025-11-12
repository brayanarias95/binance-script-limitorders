"""
Bot de Scalping para Binance usando CCXT
Estrategia basada en EMA de 20 periodos con Take Profit y Stop Loss

El bot opera en modo sandbox por defecto (paper trading).
Para activar el trading real, cambiar ENABLE_REAL_TRADING a True en config.py

Modos de operación:
- Manual: Espera entrada del usuario para ejecutar órdenes
- Automático: Ejecuta órdenes automáticamente basado en señales
"""

import ccxt
import time
import sys
from datetime import datetime, timedelta
import config
import utils

try:
    import keyboard
except ImportError:
    keyboard = None
    print("⚠️  Advertencia: Módulo 'keyboard' no disponible. Modo manual deshabilitado.")


class ScalpingBot:
    """
    Bot de trading tipo scalping para Binance (Futures)
    Soporta modo manual y automático
    """
    
    def __init__(self, operation_mode='automatic'):
        """
        Inicializa el bot con la configuración de config.py
        
        Args:
            operation_mode: 'manual' o 'automatic'
        """
        self.symbol = config.SYMBOL
        self.timeframe = config.TIMEFRAME
        self.ema_period = config.EMA_PERIOD
        self.position_size = config.POSITION_SIZE_USDT
        self.use_dynamic_position_size = config.USE_DYNAMIC_POSITION_SIZE
        self.position_size_percent = config.POSITION_SIZE_PERCENT
        self.take_profit = config.TAKE_PROFIT_PERCENT
        self.stop_loss = config.STOP_LOSS_PERCENT
        self.loop_interval = config.LOOP_INTERVAL
        self.enable_real_trading = config.ENABLE_REAL_TRADING
        self.cooldown_seconds = config.COOLDOWN_SECONDS
        self.enable_short_positions = config.ENABLE_SHORT_POSITIONS
        
        # Stop-Limit configuration
        self.use_stop_limit = config.USE_STOP_LIMIT
        self.stop_limit_offset_percent = config.STOP_LIMIT_OFFSET_PERCENT
        
        # Configuración de Futures
        self.use_futures = config.USE_FUTURES
        self.leverage = config.LEVERAGE
        self.margin_mode = config.MARGIN_MODE
        
        # Modo de operación
        self.operation_mode = operation_mode
        
        # Estado del bot
        self.in_position = False
        self.entry_price = 0.0
        self.position_amount = 0.0
        self.position_side = None  # 'LONG' o 'SHORT'
        self.last_close_time = None  # Timestamp de última posición cerrada
        self.active_order_id = None  # ID de la orden activa
        
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
        print(f"Modo de operación: {self.operation_mode.upper()}")
        print(f"Símbolo: {self.symbol}")
        print(f"Mercado: {'FUTURES' if self.use_futures else 'SPOT'}")
        
        if self.use_futures:
            print(f"Apalancamiento: {self.leverage}x")
            print(f"Modo de margen: {self.margin_mode.upper()}")
            print(f"Posiciones SHORT: {'HABILITADAS' if self.enable_short_positions else 'DESHABILITADAS'}")
        
        print(f"Timeframe: {self.timeframe}")
        print(f"Periodo EMA: {self.ema_period}")
        
        if self.use_dynamic_position_size:
            print(f"Tamaño de posición: DINÁMICO ({self.position_size_percent}% del balance disponible)")
        else:
            print(f"Tamaño de posición: {self.position_size} USDT (estático)")
        
        if self.use_futures and not self.use_dynamic_position_size:
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
    
    def _check_existing_positions(self):
        """
        Verifica si hay posiciones abiertas al iniciar el bot
        """
        if not self.use_futures:
            return
        
        print("🔍 Verificando posiciones abiertas...")
        position = utils.get_open_positions(self.exchange, self.symbol)
        
        if position:
            self.in_position = True
            self.entry_price = position['entryPrice']
            self.position_amount = position['contracts']
            self.position_side = position['side']
            
            print(f"⚠️  POSICIÓN ABIERTA DETECTADA:")
            print(f"   Lado: {self.position_side}")
            print(f"   Precio de entrada: ${self.entry_price:.4f}")
            print(f"   Cantidad: {self.position_amount}")
            print(f"   PnL no realizado: ${position['unrealizedPnl']:.2f}")
            print(f"\n   ℹ️  El bot esperará hasta que esta posición se cierre antes de operar.")
        else:
            print("✅ No hay posiciones abiertas. Listo para operar.\n")
    
    def run(self):
        """
        Loop principal del bot
        """
        print(f"🚀 Iniciando bot de scalping en modo {self.operation_mode.upper()}...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Verificar posiciones abiertas
        self._check_existing_positions()
        
        if self.operation_mode == 'manual':
            if keyboard is None:
                print("❌ Error: Módulo 'keyboard' no disponible. No se puede usar modo manual.")
                print("   Instala con: pip install keyboard")
                return
            self._run_manual_mode()
        else:
            self._run_automatic_mode()
    
    def _run_manual_mode(self):
        """
        Ejecuta el bot en modo manual (espera entrada del usuario)
        """
        print("\n" + "="*60)
        print("📋 MODO MANUAL - CONTROLES")
        print("="*60)
        print("Presiona '2' para abrir posición LONG (compra)")
        print("Presiona '3' para abrir posición SHORT (venta)")
        print("Presiona Ctrl+C para salir")
        print("="*60 + "\n")
        
        try:
            while True:
                # Mostrar precio actual
                current_price = utils.get_current_price(self.exchange, self.symbol)
                if current_price:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] 💰 Precio actual {self.symbol}: ${current_price:.4f}", end='\r')
                
                # Verificar si hay posición abierta
                if self.in_position:
                    # Monitorear posición y verificar órdenes de cierre
                    self._monitor_position_manual()
                else:
                    # Esperar entrada del usuario para abrir posición
                    if keyboard.is_pressed('2'):
                        self._execute_manual_buy('LONG')
                        time.sleep(0.5)  # Evitar múltiples detecciones
                    elif keyboard.is_pressed('3') and self.enable_short_positions:
                        self._execute_manual_buy('SHORT')
                        time.sleep(0.5)  # Evitar múltiples detecciones
                
                time.sleep(0.2)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Bot detenido por el usuario")
            if self.in_position:
                print(f"⚠️  ADVERTENCIA: Hay una posición abierta en {self.symbol}")
                print(f"   Precio de entrada: ${self.entry_price:.4f}")
    
    def _run_automatic_mode(self):
        """
        Ejecuta el bot en modo automático (órdenes automáticas basadas en señales)
        """
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                # Ejecutar ciclo de trading
                self._trading_cycle_automatic()
                
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
    
    def _execute_manual_buy(self, position_side: str):
        """
        Ejecuta una orden manual de compra (LONG o SHORT) con orden LIMIT
        
        Args:
            position_side: 'LONG' o 'SHORT'
        """
        current_price = utils.get_current_price(self.exchange, self.symbol)
        if current_price is None:
            print("\n⚠️  No se pudo obtener el precio actual")
            return
        
        side_emoji = "🟢" if position_side == 'LONG' else "🔴"
        signal_text = "COMPRA (LONG)" if position_side == 'LONG' else "VENTA (SHORT)"
        
        print(f"\n{side_emoji} ORDEN MANUAL DE {signal_text}")
        print(f"   Precio actual: ${current_price:.4f}")
        
        # Usar precio actual como límite
        limit_price = current_price
        
        if position_side == 'LONG':
            order = utils.create_limit_buy_order(
                self.exchange,
                self.symbol,
                self.position_size,
                limit_price,
                self.enable_real_trading
            )
        else:  # SHORT
            order = utils.create_limit_short_order(
                self.exchange,
                self.symbol,
                self.position_size,
                limit_price,
                self.enable_real_trading
            )
        
        if order:
            self.in_position = True
            self.entry_price = limit_price
            self.position_side = position_side
            self.active_order_id = order.get('id')
            
            # Calcular cantidad comprada
            base_currency = self.symbol.split('/')[0]
            self.position_amount = self.position_size / limit_price
            
            print(f"✅ Orden LIMIT {position_side} creada")
            print(f"   ID de orden: {self.active_order_id}")
            print(f"   Precio límite: ${self.entry_price:.4f}")
            print(f"   Cantidad: {self.position_amount:.2f} {base_currency}")
            print(f"   Margen: {self.position_size} USDT")
            
            if self.use_futures:
                effective_size = self.position_size * self.leverage
                print(f"   Control efectivo: {effective_size} USDT (apalancamiento {self.leverage}x)")
            
            if not self.enable_real_trading:
                print(f"   [SIMULACIÓN - No se ejecutó orden real]")
            
            print(f"\n   ℹ️  Esperando que la orden se complete...")
        else:
            print(f"❌ No se pudo crear la orden {position_side}")
    
    def _monitor_position_manual(self):
        """
        Monitorea la posición abierta en modo manual y coloca orden de cierre automática
        """
        # Obtener precio actual
        current_price = utils.get_current_price(self.exchange, self.symbol)
        if current_price is None:
            return
        
        # Verificar si la posición ya está abierta (orden de entrada ejecutada)
        position = utils.get_open_positions(self.exchange, self.symbol)
        
        if position and not self.enable_real_trading:
            # En modo simulación, simular que la posición se abrió
            position = {
                'contracts': self.position_amount,
                'entryPrice': self.entry_price,
                'unrealizedPnl': (current_price - self.entry_price) * self.position_amount if self.position_side == 'LONG'
                                  else (self.entry_price - current_price) * self.position_amount
            }
        
        if position or not self.enable_real_trading:
            # Posición abierta - colocar orden de cierre con pequeño profit
            if self.position_side == 'LONG':
                # Para LONG: vender un poco más arriba
                close_price = current_price + (current_price * 0.00002)  # +0.002% como en bot.py
                profit_loss_percent = utils.calculate_profit_loss_percent(self.entry_price, current_price)
            else:  # SHORT
                # Para SHORT: comprar un poco más abajo
                close_price = current_price - (current_price * 0.00002)  # -0.002%
                profit_loss_percent = -utils.calculate_profit_loss_percent(self.entry_price, current_price)
            
            # Mostrar estado
            position_emoji = "🟢" if self.position_side == 'LONG' else "🔴"
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Estimar profit
            if self.use_futures:
                profit_usd = profit_loss_percent / 100 * self.position_size * self.leverage
            else:
                profit_usd = profit_loss_percent / 100 * self.position_size
            
            print(f"\n[{timestamp}] {position_emoji} Posición {self.position_side} activa")
            print(f"   Precio entrada: ${self.entry_price:.4f}")
            print(f"   Precio actual: ${current_price:.4f}")
            print(f"   P/L estimado: {profit_loss_percent:+.2f}% (${profit_usd:+.2f} USD)")
            
            # Colocar orden de cierre si aún no existe
            print(f"   Colocando orden de cierre a ${close_price:.4f}...")
            
            if self.position_side == 'LONG':
                close_order = utils.create_limit_sell_order(
                    self.exchange,
                    self.symbol,
                    self.position_amount,
                    close_price,
                    self.enable_real_trading,
                    self.position_side
                )
            else:  # SHORT
                close_order = utils.create_limit_short_order(
                    self.exchange,
                    self.symbol,
                    self.position_amount,
                    close_price,
                    self.enable_real_trading
                )
            
            if close_order:
                print(f"   ✅ Orden de cierre colocada (ID: {close_order.get('id')})")
                
                # Esperar a que se complete
                print(f"   ⏳ Esperando ejecución de cierre...")
                self._wait_for_close(close_price)
    
    def _wait_for_close(self, close_price: float):
        """
        Espera a que la orden de cierre se ejecute
        
        Args:
            close_price: Precio de cierre de la orden
        """
        # Simular cierre en modo simulación
        if not self.enable_real_trading:
            print(f"\n   [SIMULACIÓN] Posición cerrada a ${close_price:.4f}")
            self._finalize_trade(close_price)
            return
        
        # En modo real, verificar el estado de la posición
        max_wait = 60  # segundos
        waited = 0
        
        while waited < max_wait:
            position = utils.get_open_positions(self.exchange, self.symbol)
            
            if not position:
                # Posición cerrada
                print(f"\n   ✅ Posición cerrada exitosamente")
                self._finalize_trade(close_price)
                return
            
            time.sleep(1)
            waited += 1
        
        print(f"\n   ⚠️  Tiempo de espera agotado. Verifica manualmente.")
    
    def _finalize_trade(self, close_price: float):
        """
        Finaliza el trade y actualiza estadísticas
        
        Args:
            close_price: Precio de cierre
        """
        # Calcular P/L
        if self.position_side == 'LONG':
            profit_loss_percent = utils.calculate_profit_loss_percent(self.entry_price, close_price)
            profit_loss_usd = (close_price - self.entry_price) * self.position_amount
        else:  # SHORT
            profit_loss_percent = -utils.calculate_profit_loss_percent(self.entry_price, close_price)
            profit_loss_usd = (self.entry_price - close_price) * self.position_amount
        
        # Aplicar apalancamiento
        if self.use_futures:
            profit_loss_usd *= self.leverage
        
        print(f"\n📊 RESUMEN DEL TRADE:")
        print(f"   Lado: {self.position_side}")
        print(f"   Precio de entrada: ${self.entry_price:.4f}")
        print(f"   Precio de salida: ${close_price:.4f}")
        print(f"   Cantidad: {self.position_amount:.2f}")
        
        if profit_loss_percent >= 0:
            print(f"   💰 Profit realizado: +{profit_loss_percent:.2f}% (+${profit_loss_usd:.2f} USD)")
            self.winning_trades += 1
        else:
            print(f"   💸 Pérdida: {profit_loss_percent:.2f}% (${profit_loss_usd:.2f} USD)")
            self.losing_trades += 1
        
        # Actualizar estadísticas
        self.total_trades += 1
        self.total_profit_usd += profit_loss_usd
        
        # Mostrar estadísticas acumuladas
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        print(f"\n📈 ESTADÍSTICAS ACUMULADAS:")
        print(f"   Total trades: {self.total_trades}")
        print(f"   Ganadores: {self.winning_trades} | Perdedores: {self.losing_trades}")
        print(f"   Win rate: {win_rate:.1f}%")
        print(f"   P/L Total: ${self.total_profit_usd:.2f} USD\n")
        
        # Resetear estado
        self.in_position = False
        self.entry_price = 0.0
        self.position_amount = 0.0
        self.position_side = None
        self.active_order_id = None
        self.last_close_time = datetime.now()
    
    def _trading_cycle_automatic(self):
        """
        Ejecuta un ciclo completo de la estrategia de trading en modo automático
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
    
    def _place_stop_limit_order(self):
        """
        Coloca una orden stop-limit para proteger la posición actual
        """
        if not self.in_position or self.position_side is None:
            return
        
        # Calcular precio de stop (trigger) basado en el stop loss configurado
        if self.position_side == 'LONG':
            # Para LONG: stop loss es cuando el precio cae
            trigger_price = self.entry_price * (1 - self.stop_loss / 100)
            # Limit price es ligeramente por debajo del trigger
            limit_price = trigger_price * (1 - self.stop_limit_offset_percent / 100)
            # Para cerrar LONG, necesitamos SELL
            order_side = 'sell'
        else:  # SHORT
            # Para SHORT: stop loss es cuando el precio sube
            trigger_price = self.entry_price * (1 + self.stop_loss / 100)
            # Limit price es ligeramente por encima del trigger
            limit_price = trigger_price * (1 + self.stop_limit_offset_percent / 100)
            # Para cerrar SHORT, necesitamos BUY
            order_side = 'buy'
        
        # Crear la orden stop-limit
        stop_order = utils.create_stop_limit_order(
            self.exchange,
            self.symbol,
            order_side,
            self.position_amount,
            trigger_price,
            limit_price,
            reduce_only=True
        )
        
        if stop_order:
            print(f"   🛡 Stop-Limit colocado:")
            print(f"      Trigger: ${trigger_price:.4f}")
            print(f"      Limit: ${limit_price:.4f}")
            print(f"      Lado: {order_side.upper()}")
        else:
            print(f"   ⚠️ No se pudo colocar el stop-limit")
    
    def _execute_buy(self, current_price: float, position_side: str):
        """
        Ejecuta una orden de compra (LONG o SHORT) con orden LIMIT en modo automático
        
        Args:
            current_price: Precio actual del activo
            position_side: 'LONG' o 'SHORT'
        """
        side_emoji = "🟢" if position_side == 'LONG' else "🔴"
        signal_text = "COMPRA (LONG)" if position_side == 'LONG' else "VENTA (SHORT)"
        
        # Obtener tamaño de posición dinámico
        position_size_usdt = self._get_position_size()
        
        print(f"\n{side_emoji} SEÑAL DE {signal_text} DETECTADA")
        print(f"   Precio actual: ${current_price:.4f}")
        
        if self.use_dynamic_position_size:
            available_balance = utils.get_futures_available_balance(self.exchange, 'USDT') if self.use_futures else utils.get_balance(self.exchange, 'USDT')
            if available_balance:
                print(f"   💰 Balance disponible: ${available_balance:.2f} USDT")
                print(f"   📊 Tamaño de posición: ${position_size_usdt:.2f} USDT ({self.position_size_percent}% del balance)")
        
        # Usar precio actual como límite
        limit_price = current_price
        
        if position_side == 'LONG':
            order = utils.create_limit_buy_order(
                self.exchange,
                self.symbol,
                position_size_usdt,
                self.position_size,
                limit_price,
                self.enable_real_trading
            )
        else:  # SHORT
            order = utils.create_limit_short_order(
                self.exchange,
                self.symbol,
                position_size_usdt,
                self.position_size,
                limit_price,
                self.enable_real_trading
            )
        
        if order:
            self.in_position = True
            self.entry_price = limit_price
            self.position_side = position_side
            self.active_order_id = order.get('id')
            
            # Calcular cantidad comprada
            base_currency = self.symbol.split('/')[0]
            self.position_amount = position_size_usdt / limit_price
            self.position_amount = self.position_size / limit_price
            
            print(f"✅ Orden LIMIT {position_side} creada")
            print(f"   Estado: Pendiente de ejecución")
            print(f"   ID de orden: {self.active_order_id}")
            print(f"   Precio límite: ${self.entry_price:.4f}")
            print(f"   Cantidad: {self.position_amount:.2f} {base_currency}")
            print(f"   Margen: {position_size_usdt:.2f} USDT")
            print(f"   Margen: {self.position_size} USDT")
            
            if self.use_futures:
                effective_size = position_size_usdt * self.leverage
                print(f"   Control efectivo: {effective_size:.2f} USDT (apalancamiento {self.leverage}x)")
            
            if not self.enable_real_trading:
                print(f"   [SIMULACIÓN - No se ejecutó orden real]")
        else:
            print(f"❌ No se pudo ejecutar la orden {position_side}")
    
    def _execute_sell(self, current_price: float, reason: str):
        """
        Ejecuta una orden de cierre de posición con orden LIMIT
        
        Args:
            current_price: Precio actual del activo
            reason: Razón de la venta (TP o SL)
        """
        side_emoji = "🟢" if self.position_side == 'LONG' else "🔴"
        print(f"\n{side_emoji} SEÑAL DE CIERRE {self.position_side} DETECTADA")
        print(f"   Razón: {reason}")
        print(f"   Precio actual: ${current_price:.4f}")
        
        # Calcular precio límite para cierre (con pequeño offset como en bot.py)
        if self.position_side == 'LONG':
            # Para LONG: vender un poco más arriba
            limit_price = current_price + (current_price * 0.00002)  # +0.002%
        else:  # SHORT
            # Para SHORT: comprar un poco más abajo
            limit_price = current_price - (current_price * 0.00002)  # -0.002%
        
        if self.position_side == 'LONG':
            order = utils.create_limit_sell_order(
                self.exchange,
                self.symbol,
                self.position_amount,
                limit_price,
                self.enable_real_trading,
                self.position_side
            )
        else:  # SHORT
            order = utils.close_limit_short_order(
                self.exchange,
                self.symbol,
                self.position_amount,
                limit_price,
                self.enable_real_trading
            )
        
        if order:
            # Calcular P/L estimado
            if self.position_side == 'LONG':
                profit_loss_percent = utils.calculate_profit_loss_percent(
                    self.entry_price,
                    limit_price
                )
                profit_loss_usd = (limit_price - self.entry_price) * self.position_amount
            else:  # SHORT
                profit_loss_percent = -utils.calculate_profit_loss_percent(
                    self.entry_price,
                    limit_price
                )
                profit_loss_usd = (self.entry_price - limit_price) * self.position_amount
            
            # Aplicar apalancamiento al cálculo de ganancias en Futures
            if self.use_futures:
                profit_loss_usd *= self.leverage
            
            print(f"✅ Orden de cierre LIMIT colocada")
            print(f"   Estado: Pendiente de ejecución")
            print(f"   Precio límite: ${limit_price:.4f}")
            print(f"   Cantidad: {self.position_amount:.2f}")
            
            if profit_loss_percent >= 0:
                print(f"   💰 Profit estimado: +{profit_loss_percent:.2f}% (+${profit_loss_usd:.2f} USD)")
                self.winning_trades += 1
            else:
                print(f"   💸 Pérdida estimada: {profit_loss_percent:.2f}% (${profit_loss_usd:.2f} USD)")
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
            self.active_order_id = None
            self.last_close_time = datetime.now()
            
            print(f"\n   ⏳ Cooldown activado: {self.cooldown_seconds}s antes de nueva posición")
        else:
            print(f"❌ No se pudo cerrar la posición {self.position_side}")


def main():
    """
    Función principal para iniciar el bot
    """
    # Verificar que las credenciales estén configuradas
    if config.API_KEY == 'your api key' or config.API_SECRET == 'your api secret' or not config.API_KEY:
        print("❌ ERROR: Configura tus credenciales de API en config.py")
        print("   Para obtener credenciales: https://www.binance.com/en/my/settings/api-management")
        
        if config.USE_SANDBOX:
            print("\n💡 NOTA: Estás en modo SANDBOX. Puedes usar credenciales de testnet:")
            print("   https://testnet.binance.vision/")
        
        return
    
    # Menú de selección de modo
    print("\n" + "="*60)
    print("🤖 BOT DE SCALPING BINANCE FUTURES")
    print("="*60)
    print("\nSelecciona el modo de operación:")
    print("1. Operación MANUAL (espera entrada del usuario)")
    print("2. Operación AUTOMÁTICA (ejecuta órdenes automáticamente)")
    print("="*60)
    
    while True:
        try:
            choice = input("\nIngresa tu opción (1 o 2): ").strip()
            if choice == '1':
                operation_mode = 'manual'
                break
            elif choice == '2':
                operation_mode = 'automatic'
                break
            else:
                print("⚠️  Opción inválida. Ingresa 1 o 2.")
        except KeyboardInterrupt:
            print("\n❌ Operación cancelada por el usuario")
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
    
    # Crear e iniciar el bot con el modo seleccionado
    bot = ScalpingBot(operation_mode=operation_mode)
    bot.run()


if __name__ == "__main__":
    main()
