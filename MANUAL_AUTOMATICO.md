# Guía de Uso - Modos Manual y Automático

## 🎯 Nuevas Funcionalidades

El bot ahora soporta dos modos de operación:
1. **Modo Manual**: Control total del usuario mediante teclado
2. **Modo Automático**: Ejecución automática basada en señales

## 🚀 Inicio del Bot

Al ejecutar `python main.py`, aparecerá un menú:

```
============================================================
🤖 BOT DE SCALPING BINANCE FUTURES
============================================================

Selecciona el modo de operación:
1. Operación MANUAL (espera entrada del usuario)
2. Operación AUTOMÁTICA (ejecuta órdenes automáticamente)
============================================================

Ingresa tu opción (1 o 2):
```

## 📋 Modo Manual

### Características
- Control completo mediante teclado
- Órdenes LIMIT en lugar de MARKET
- Cierre automático con pequeño profit (0.002%)
- Monitoreo en tiempo real de P/L

### Controles
- **Presiona '2'**: Abrir posición LONG (compra)
- **Presiona '3'**: Abrir posición SHORT (venta)
- **Ctrl+C**: Salir del bot

### Flujo de Operación

1. El bot muestra el precio actual en tiempo real
2. Usuario presiona tecla 2 o 3 para abrir posición
3. Bot coloca orden LIMIT al precio actual
4. Cuando la orden se ejecuta, automáticamente coloca orden de cierre
5. El cierre se ejecuta con un pequeño profit (+0.002%)
6. Bot muestra el profit/loss realizado
7. Usuario puede abrir nueva posición

### Ejemplo de Uso
```
[18:30:15] 💰 Precio actual DOGE/USDT: $0.0823

Usuario presiona '2'...

🟢 ORDEN MANUAL DE COMPRA (LONG)
   Precio actual: $0.0823
   DEBUG: Creando LIMIT LONG - Precio: $0.0823, Cantidad: 60.8, Notional: $5.00 USDT
✅ Orden LIMIT LONG creada
   ID de orden: 12345678
   Precio límite: $0.0823
   Cantidad: 60.80 DOGE
   Margen: 5 USDT
   Control efectivo: 50 USDT (apalancamiento 10x)

   ℹ️  Esperando que la orden se complete...

[18:30:20] 🟢 Posición LONG activa
   Precio entrada: $0.0823
   Precio actual: $0.0824
   P/L estimado: +0.12% (+$0.06 USD)
   Colocando orden de cierre a $0.0824...
   ✅ Orden de cierre colocada (ID: 12345679)
   ⏳ Esperando ejecución de cierre...

📊 RESUMEN DEL TRADE:
   Lado: LONG
   Precio de entrada: $0.0823
   Precio de salida: $0.0824
   Cantidad: 60.80
   💰 Profit realizado: +0.12% (+$0.06 USD)

📈 ESTADÍSTICAS ACUMULADAS:
   Total trades: 1
   Ganadores: 1 | Perdedores: 0
   Win rate: 100.0%
   P/L Total: $0.06 USD
```

## 🤖 Modo Automático

### Características
- Ejecución automática basada en señales EMA
- Órdenes LIMIT con precio actual
- Take Profit y Stop Loss configurables
- Cooldown entre operaciones

### Funcionamiento

1. Bot monitorea el precio y calcula EMA
2. **Señal LONG**: Cuando precio > EMA
3. **Señal SHORT**: Cuando precio < EMA (si está habilitado)
4. Coloca orden LIMIT al precio actual
5. Monitorea la posición
6. Cierra cuando alcanza TP o SL
7. Espera cooldown antes de nueva operación

### Configuración

En `config.py`:
```python
# Estrategia
EMA_PERIOD = 12
TAKE_PROFIT_PERCENT = 0.6  # 0.6%
STOP_LOSS_PERCENT = 0.4     # 0.4%

# Gestión
COOLDOWN_SECONDS = 60       # 60s entre operaciones
ENABLE_SHORT_POSITIONS = True
```

### Ejemplo de Uso
```
🚀 Iniciando bot de scalping en modo AUTOMATIC...

🔍 Verificando posiciones abiertas...
✅ No hay posiciones abiertas. Listo para operar.

[18:35:20] 📊 Estado del mercado:
  💰 Precio actual: $0.08
  📈 EMA(12): $0.08

🟢 SEÑAL DE COMPRA (LONG) DETECTADA
   Precio actual: $0.0800
   DEBUG: Creando LIMIT LONG - Precio: $0.0800, Cantidad: 62.5, Notional: $5.00 USDT
✅ Orden LIMIT LONG creada
   Estado: Pendiente de ejecución
   ID de orden: 987654321
   Precio límite: $0.0800
   Cantidad: 62.50 DOGE
   Margen: 5 USDT
   Control efectivo: 50 USDT (apalancamiento 10x)

[18:37:30] 📊 Estado del mercado:
  💰 Precio actual: $0.08
  📈 EMA(12): $0.08
  🟢 En posición LONG desde: $0.08
  💹 P/L: +0.63% (ganancia)

🟢 SEÑAL DE CIERRE LONG DETECTADA
   Razón: TAKE PROFIT alcanzado: +0.63%
   Precio actual: $0.0805
✅ Orden de cierre LIMIT colocada
   Estado: Pendiente de ejecución
   Precio límite: $0.0805
   Cantidad: 62.50
   💰 Profit estimado: +0.63% (+$0.31 USD)

📊 ESTADÍSTICAS:
   Total trades: 1
   Ganadores: 1 | Perdedores: 0
   Win rate: 100.0%
   P/L Total: $0.31 USD

   ⏳ Cooldown activado: 60s antes de nueva posición
```

## 🛡️ Manejo de Posiciones Abiertas

Al iniciar, el bot **siempre verifica** si hay posiciones abiertas:

```
🔍 Verificando posiciones abiertas...
⚠️  POSICIÓN ABIERTA DETECTADA:
   Lado: LONG
   Precio de entrada: $0.0823
   Cantidad: 60.8
   PnL no realizado: $0.15

   ℹ️  El bot esperará hasta que esta posición se cierre antes de operar.
```

### Comportamiento:
- ✅ Si hay posición abierta: Bot NO abre nuevas posiciones
- ✅ Espera hasta que la posición se cierre
- ✅ Solo después opera normalmente
- ✅ Previene múltiples posiciones simultáneas

## 📊 Logs Mejorados

El bot ahora muestra:
- ✅ Precio actual de la criptomoneda
- ✅ Estado de la orden (Pendiente/Ejecutada)
- ✅ P/L estimado (posiciones abiertas)
- ✅ P/L realizado (trades completados)
- ✅ Estadísticas acumuladas
- ✅ ID de órdenes para tracking

## ⚠️ Notas Importantes

1. **Modo Manual requiere el módulo `keyboard`**
   ```bash
   pip install keyboard
   ```

2. **Las órdenes LIMIT pueden no ejecutarse inmediatamente**
   - Esperan a que el precio alcance el límite
   - En mercados volátiles esto es casi instantáneo
   - En mercados lentos puede tomar tiempo

3. **Posiciones abiertas previas**
   - El bot detecta y respeta posiciones existentes
   - No interfiere con posiciones manuales
   - Espera hasta que se cierren

4. **Trading Real**
   - Siempre prueba primero en modo simulación
   - Configura `ENABLE_REAL_TRADING = True` solo cuando estés seguro
   - Usa montos pequeños al comenzar

## 🔧 Solución de Problemas

### "Módulo 'keyboard' no disponible"
```bash
pip install keyboard
```

### "No se pudo obtener el precio actual"
- Verifica tu conexión a internet
- Verifica tus API keys en config.py

### "No se pudo crear la orden"
- Verifica que tengas saldo suficiente
- Revisa los logs para más detalles
- En modo testnet, solicita fondos de prueba

### La orden no se ejecuta
- Las órdenes LIMIT esperan el precio exacto
- Cancela manualmente si es necesario
- Considera ajustar la estrategia

## 📚 Recursos

- [Documentación CCXT](https://docs.ccxt.com/)
- [API de Binance Futures](https://binance-docs.github.io/apidocs/futures/en/)
- [Binance Testnet](https://testnet.binance.vision/)
