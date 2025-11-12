# Bot de Scalping para Binance

Bot de trading automatizado tipo scalping para Binance usando Python y CCXT.

## 🚀 Características

- **Estrategia EMA**: Compra cuando el precio cruza por encima de la EMA de 12 periodos
- **Profit Fijo de 2 USDT**: 🆕 El bot calcula automáticamente el precio de take profit necesario para obtener exactamente 2 USDT de ganancia en cada operación
- **Órdenes LIMIT**: Todas las operaciones usan órdenes limit para mejor control de precios
- **Gestión de riesgo**: Stop Loss (-0.4%) configurable para limitar pérdidas
- **Tamaño de posición dinámico**: El bot consulta automáticamente el balance disponible y ajusta el tamaño de cada operación según el porcentaje configurado
- **Futures Trading**: Soporte para Binance Futures con apalancamiento configurable
- **Posiciones LONG y SHORT**: Aprovecha movimientos alcistas y bajistas
- **Modo Sandbox**: Opera en modo paper trading por defecto (sin dinero real)
- **Timeframe**: Velas de 1 minuto
- **Logs detallados**: Muestra precio actual, EMA, balance disponible, take profit calculado y P/L en tiempo real
- **Manejo de errores**: Reintentos automáticos en caso de errores de conexión
- **Prevención de duplicados**: Verifica posiciones abiertas y espera a que se cierren antes de abrir nuevas

## 📋 Requisitos

- Python 3.8 o superior
- Cuenta en Binance (o Binance Testnet para sandbox)

## 🔧 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/brayanarias95/binance-script-limitorders.git
cd binance-script-limitorders
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura tus credenciales en `config.py`:
```python
API_KEY = 'tu_api_key'
API_SECRET = 'tu_api_secret'
```

Para obtener credenciales de testnet (recomendado para pruebas):
- Testnet: https://testnet.binance.vision/

## 🎮 Uso

### Ejecutar en modo sandbox (recomendado):
```bash
python main.py
```

### Para activar trading real:
1. Edita `config.py` y cambia:
```python
ENABLE_REAL_TRADING = True
```

2. Ejecuta el bot:
```bash
python main.py
```

⚠️ **ADVERTENCIA**: El trading real involucra riesgos. Solo activa esta opción si entiendes completamente lo que hace el bot.

## ⚙️ Configuración

Todas las opciones configurables están en `config.py`:

### Trading Configuration
- `SYMBOL`: Par de trading (default: 'DOGE/USDT')
- `TIMEFRAME`: Timeframe de las velas (default: '1m')
- `EMA_PERIOD`: Periodo de la EMA (default: 12)
- `TARGET_PROFIT_USDT`: 🆕 Ganancia objetivo fija por operación en USDT (default: 2.0)
- `STOP_LOSS_PERCENT`: Stop loss en % (default: 0.4)

### Position Sizing
- `USE_DYNAMIC_POSITION_SIZE`: Usar tamaño dinámico basado en balance (default: True)
- `POSITION_SIZE_PERCENT`: Porcentaje del balance a usar por operación (default: 10%)
- `POSITION_SIZE_USDT`: Tamaño fijo en USDT (usado solo si dynamic está deshabilitado, default: 5)

**Nota:** Con tamaño dinámico habilitado, el bot consulta automáticamente tu balance disponible antes de cada operación y usa el porcentaje configurado. Esto significa que:
- ✅ No necesitas modificar el config cuando cambia tu balance
- ✅ El riesgo se ajusta automáticamente según tu capital disponible
- ✅ Evitas errores de margen insuficiente

### Futures Configuration
- `USE_FUTURES`: Activar trading de Futures (default: True)
- `LEVERAGE`: Apalancamiento (default: 10x)
- `MARGIN_MODE`: Modo de margen 'isolated' o 'cross' (default: 'isolated')
- `ENABLE_SHORT_POSITIONS`: Permitir posiciones SHORT (default: True)

### Execution Settings
- `LOOP_INTERVAL`: Segundos entre iteraciones (default: 3)
- `COOLDOWN_SECONDS`: Espera después de cerrar posición (default: 60)
- `ENABLE_REAL_TRADING`: Activar trading real (default: True)
- `USE_SANDBOX`: Usar modo testnet (default: False)

## 💰 Ganancia Fija de 2 USDT por Operación

El bot ahora calcula automáticamente el precio de take profit necesario para obtener **exactamente 2 USDT de ganancia** en cada operación, independientemente del precio del activo o el tamaño de la posición.

### ¿Cómo funciona?

1. Cuando abres una posición (LONG o SHORT), el bot calcula:
   - Cantidad de activo comprado/vendido = Margen / Precio de entrada
   - Cambio de precio necesario = 2 USDT / (Cantidad × Apalancamiento)
   - Precio de take profit = Precio de entrada ± Cambio necesario

2. El bot coloca automáticamente una orden LIMIT de cierre al precio calculado

3. Cuando el precio alcanza el take profit, la orden se ejecuta y obtienes 2 USDT de ganancia

### Ejemplo Real

**Escenario:** LONG en DOGE/USDT
- Precio de entrada: $0.08
- Margen usado: $10 USDT
- Apalancamiento: 10x
- Cantidad comprada: 125 DOGE (10 / 0.08)

**Cálculo:**
- Cambio de precio necesario: 2 / (125 × 10) = $0.0016
- Precio de take profit: $0.08 + $0.0016 = **$0.0816**

**Resultado:**
- Ganancia: ($0.0816 - $0.08) × 125 × 10 = **2.00 USDT** ✅

### Ventajas

- ✅ **Ganancias predecibles**: Siempre sabes exactamente cuánto ganarás
- ✅ **Control de riesgo**: Puedes calcular fácilmente cuántas operaciones exitosas necesitas para recuperar pérdidas
- ✅ **Gestión simple**: No necesitas calcular porcentajes manualmente
- ✅ **Funciona con cualquier activo**: Se ajusta automáticamente al precio del token

### Configuración

El profit objetivo se configura en `config.py`:
```python
TARGET_PROFIT_USDT = 2.0  # Ganancia objetivo por operación en USDT
```

Puedes cambiar este valor según tus preferencias (ej: 1.0, 3.0, 5.0, etc.)

## 💡 Tamaño de Posición Dinámico

El bot ahora soporta **tamaño de posición dinámico** basado en tu balance disponible. Esta característica:

### ¿Cómo funciona?
1. Antes de abrir cada posición, el bot consulta tu balance disponible en Binance Futures
2. Calcula el tamaño de la operación como un porcentaje de ese balance (configurable en `POSITION_SIZE_PERCENT`)
3. Ejecuta la orden con ese tamaño dinámico

### Ventajas
- ✅ **No necesitas editar el config.py** cuando tu balance cambia
- ✅ **Gestión de riesgo consistente**: Siempre arriesgas el mismo porcentaje de tu capital
- ✅ **Evita errores de margen insuficiente**: El bot siempre sabe cuánto puedes operar
- ✅ **Escalable**: Funciona igual con $100 o $10,000 en tu cuenta

### Ejemplo
Si tienes **$200 USDT** disponibles y configuras `POSITION_SIZE_PERCENT = 10`:
- Cada operación usará **$20 USDT** (10% de $200)
- Con apalancamiento 10x, controlarás **$200 USDT** en la posición
- Si ganas y tu balance sube a $250, la próxima operación usará **$25 USDT** (10% de $250)

### Configuración
Para usar tamaño dinámico (recomendado):
```python
USE_DYNAMIC_POSITION_SIZE = True
POSITION_SIZE_PERCENT = 10  # 10% del balance por operación
```

Para usar tamaño fijo (tradicional):
```python
USE_DYNAMIC_POSITION_SIZE = False
POSITION_SIZE_USDT = 5  # Tamaño fijo en USDT
```

## 📁 Estructura del proyecto

```
.
├── main.py          # Lógica principal del bot
├── config.py        # Configuración (API keys, parámetros)
├── utils.py         # Funciones auxiliares (precio, EMA, etc.)
├── requirements.txt # Dependencias de Python
└── README.md        # Este archivo
```

## 🔐 Seguridad

- Nunca compartas tus API keys
- Usa el modo sandbox para pruebas
- Comienza con montos pequeños en trading real
- Asegúrate de entender la estrategia antes de operar con dinero real

## 📊 Estrategia de Trading

1. **Entrada LONG**: Compra cuando el precio cierra por encima de la EMA(12)
2. **Entrada SHORT**: Vende cuando el precio cierra por debajo de la EMA(12)
3. **Salida (Take Profit)**: 
   - El bot calcula automáticamente el precio de cierre necesario para obtener **2 USDT de ganancia**
   - Coloca una orden LIMIT al precio calculado
   - Cuando el precio alcanza el objetivo, la orden se ejecuta automáticamente
4. **Salida (Stop Loss)**: 
   - Si la pérdida alcanza -0.4%, cierra la posición para limitar pérdidas
5. **Cooldown**: Después de cerrar una posición, el bot espera 60 segundos antes de abrir una nueva
6. **Prevención de duplicados**: El bot verifica posiciones abiertas y espera a que se cierren antes de abrir nuevas

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## ⚠️ Disclaimer

Este bot es solo para fines educativos. El trading de criptomonedas conlleva riesgos significativos. No soy responsable de ninguna pérdida que puedas sufrir al usar este software. Úsalo bajo tu propio riesgo.
