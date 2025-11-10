# Guía de Uso - Bot de Scalping

## 🚀 Inicio Rápido

### 1. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configuración de API Keys

Edita el archivo `config.py` y agrega tus credenciales:

```python
API_KEY = 'tu_api_key_aqui'
API_SECRET = 'tu_api_secret_aqui'
```

#### Obtener API Keys para Testnet (Recomendado para pruebas):

1. Visita: https://testnet.binance.vision/
2. Crea una cuenta de testnet
3. Genera tus API keys en la sección de configuración
4. Copia las keys a `config.py`

#### Obtener API Keys para Trading Real:

1. Visita: https://www.binance.com/en/my/settings/api-management
2. Crea una nueva API key
3. **Importante**: No habilites retiros en la API key
4. Copia las keys a `config.py`

### 3. Ejecutar el Bot

#### Modo Sandbox (Sin dinero real - Recomendado):

```bash
python main.py
```

El bot iniciará en modo sandbox automáticamente. Verás un mensaje:
```
⚠️  MODO SANDBOX ACTIVADO - No se usará dinero real
```

#### Modo Real (Con dinero real - Solo usuarios avanzados):

1. Edita `config.py`:
```python
ENABLE_REAL_TRADING = True
```

2. Ejecuta:
```bash
python main.py
```

3. Confirma cuando se te solicite escribiendo `SI`

## ⚙️ Configuración Personalizada

### Parámetros Principales (`config.py`)

```python
# Par de trading
SYMBOL = 'BTC/USDT'  # Cambiar a 'ETH/USDT', 'BNB/USDT', etc.

# Timeframe de las velas
TIMEFRAME = '1m'  # '1m', '3m', '5m', '15m', '1h', etc.

# Periodo de la EMA
EMA_PERIOD = 20  # Valores comunes: 9, 20, 50, 200

# Tamaño de posición
POSITION_SIZE_USDT = 100  # Cantidad en USDT por operación

# Take Profit y Stop Loss
TAKE_PROFIT_PERCENT = 0.4  # 0.4% de ganancia
STOP_LOSS_PERCENT = 0.3    # 0.3% de pérdida máxima

# Frecuencia de ejecución
LOOP_INTERVAL = 3  # Segundos entre cada ciclo (3-5 recomendado)
```

## 📊 Entendiendo la Estrategia

### Señal de Compra
- El precio actual debe estar **por encima** de la EMA(20)
- Compra a precio de mercado

### Señal de Venta
Se vende cuando se cumple alguna de estas condiciones:

1. **Take Profit**: Ganancia >= +0.4%
2. **Stop Loss**: Pérdida <= -0.3%

### Ejemplo de Operación

```
1. Precio BTC: $45,000
2. EMA(20): $44,950
3. Señal: COMPRA (precio > EMA)
4. Entrada: $45,000

... después de 2 minutos ...

5. Precio BTC: $45,200
6. P/L: +0.44%
7. Señal: VENTA (Take Profit alcanzado)
8. Resultado: +$44 de ganancia (en posición de 100 USDT)
```

## 📝 Logs del Bot

El bot muestra información detallada en cada ciclo:

```
[10:30:15] 📊 Estado del mercado:
  💰 Precio actual: $45,030.00
  📈 EMA(20): $44,980.50
  
🟢 SEÑAL DE COMPRA DETECTADA
   Precio > EMA: $45,030.00
✅ Orden de compra ejecutada
   Precio de entrada: $45,030.00
   Cantidad: 0.002222 BTC
   Total: 100 USDT
   [SIMULACIÓN - No se ejecutó orden real]

[10:32:45] 📊 Estado del mercado:
  💰 Precio actual: $45,210.00
  📈 EMA(20): $45,015.30
  📍 En posición desde: $45,030.00
  💹 P/L: +0.40% (ganancia)
  
🔴 SEÑAL DE VENTA DETECTADA
   Razón: TAKE PROFIT alcanzado: +0.40%
✅ Orden de venta ejecutada
   Precio de salida: $45,210.00
   Cantidad: 0.002222
   💰 Ganancia: +0.40% (+$0.40)
```

## ⚠️ Advertencias y Consideraciones

### Riesgos
- El trading de criptomonedas es **altamente riesgoso**
- Puedes perder parte o todo tu capital
- Los resultados pasados no garantizan resultados futuros
- La volatilidad puede causar pérdidas rápidas

### Recomendaciones
1. **Siempre prueba primero en sandbox/testnet**
2. Comienza con montos pequeños en trading real
3. No inviertas dinero que no puedas permitirte perder
4. Monitorea el bot regularmente
5. Entiende completamente la estrategia antes de usarla

### Limitaciones
- El bot usa órdenes de mercado (pueden tener slippage)
- Requiere conexión a internet estable
- Las comisiones de trading afectan la rentabilidad
- El mercado puede moverse en contra rápidamente

## 🔧 Solución de Problemas

### Error: "API key inválida"
- Verifica que copiaste correctamente las keys en `config.py`
- Asegúrate de estar usando las keys correctas (testnet vs producción)

### Error: "Insufficient balance"
- Verifica que tienes suficiente saldo en tu cuenta
- En testnet, solicita fondos de prueba
- Reduce el `POSITION_SIZE_USDT` en `config.py`

### El bot no ejecuta operaciones
- Verifica que el precio esté cruzando la EMA
- Revisa los logs para ver el estado del mercado
- Puede que las condiciones de mercado no generen señales

### Error de conexión
- Verifica tu conexión a internet
- El bot reintentará automáticamente
- Si persiste, reinicia el bot

## 🛑 Detener el Bot

Para detener el bot de forma segura:

1. Presiona `Ctrl + C` en la terminal
2. El bot se detendrá y mostrará si hay posiciones abiertas
3. Si hay una posición abierta, decide si la cierras manualmente

## 📈 Monitoreo y Optimización

### Métricas a Seguir
- Tasa de éxito (% de operaciones ganadoras)
- Ganancia/pérdida promedio por operación
- Número de operaciones por día
- Drawdown máximo

### Optimización
- Ajusta el periodo de EMA según el mercado
- Modifica los niveles de TP/SL basado en volatilidad
- Prueba diferentes pares de trading
- Ajusta el tamaño de posición según tu capital

## 📚 Recursos Adicionales

- [Documentación CCXT](https://docs.ccxt.com/)
- [API de Binance](https://binance-docs.github.io/apidocs/)
- [Binance Testnet](https://testnet.binance.vision/)

## 🤝 Soporte

Si encuentras problemas:
1. Revisa esta guía completa
2. Verifica los logs del bot para errores específicos
3. Abre un issue en el repositorio de GitHub

---

**Disclaimer**: Este bot es solo para fines educativos. El autor no se hace responsable de ninguna pérdida financiera. Úsalo bajo tu propio riesgo.
