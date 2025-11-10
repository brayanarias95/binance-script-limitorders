# Bot de Scalping para Binance

Bot de trading automatizado tipo scalping para Binance usando Python y CCXT.

## 🚀 Características

- **Estrategia EMA**: Compra cuando el precio cruza por encima de la EMA de 20 periodos
- **Gestión de riesgo**: Take Profit (+0.4%) y Stop Loss (-0.3%) configurables
- **Modo Sandbox**: Opera en modo paper trading por defecto (sin dinero real)
- **Timeframe**: Velas de 1 minuto
- **Símbolo por defecto**: BTC/USDT
- **Logs detallados**: Muestra precio actual, EMA, P/L en tiempo real
- **Manejo de errores**: Reintentos automáticos en caso de errores de conexión

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

- `SYMBOL`: Par de trading (default: 'BTC/USDT')
- `TIMEFRAME`: Timeframe de las velas (default: '1m')
- `EMA_PERIOD`: Periodo de la EMA (default: 20)
- `POSITION_SIZE_USDT`: Tamaño de posición en USDT (default: 100)
- `TAKE_PROFIT_PERCENT`: Take profit en % (default: 0.4)
- `STOP_LOSS_PERCENT`: Stop loss en % (default: 0.3)
- `LOOP_INTERVAL`: Segundos entre iteraciones (default: 3)
- `ENABLE_REAL_TRADING`: Activar trading real (default: False)
- `USE_SANDBOX`: Usar modo testnet (default: True)

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

1. **Entrada**: Compra cuando el precio cierra por encima de la EMA(20)
2. **Salida**:
   - Take Profit: Vende si la ganancia es >= +0.4%
   - Stop Loss: Vende si la pérdida es <= -0.3%

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## ⚠️ Disclaimer

Este bot es solo para fines educativos. El trading de criptomonedas conlleva riesgos significativos. No soy responsable de ninguna pérdida que puedas sufrir al usar este software. Úsalo bajo tu propio riesgo.
