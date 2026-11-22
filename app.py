# ROBOT JEFE - RENDER VERSION
# EMA 50 + EMA 200 + RSI + Multi-Timeframe
import os
import time
import threading
import pandas as pd
import ccxt
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

app = Flask(__name__)

# --- CONFIGURACION JEFE ---
SYMBOL = 'BTC/USDT'
TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h']

# PON AQUI TU TOKEN Y TU ID JEFE
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'PON_AQUI_TU_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'PON_AQUI_TU_ID')

@app.route('/')
def home():
    return "ROBOT JEFE ENCENDIDO - BTC/USDT - EMA + RSI"

def enviar_telegram(mensaje, foto=None):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': mensaje}, timeout=10)
        if foto:
            url_foto = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            with open(foto, 'rb') as f:
                requests.post(url_foto, data={'chat_id': TELEGRAM_CHAT_ID}, files={'photo': f}, timeout=15)
    except Exception as e:
        print(f"Error Telegram jefe: {e}")

def get_velas(symbol, timeframe, limit=250):
    exchange = ccxt.binance({'enableRateLimit': True})
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

def calcular(df):
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def hacer_grafico(df, timeframe, señal):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(df['time'], df['close'], label='Precio', color='black', linewidth=1)
    ax1.plot(df['time'], df['EMA50'], label='EMA 50', color='blue', linewidth=1.5)
    ax1.plot(df['time'], df['EMA200'], label='EMA 200', color='red', linewidth=1.5)
    ax1.set_title(f"{SYMBOL} - {timeframe} - {señal} - JEFE")
    ax1.legend(); ax1.grid(True)
    ax2.plot(df['time'], df['RSI'], label='RSI', color='purple')
    ax2.axhline(70, color='red', linestyle='--')
    ax2.axhline(30, color='green', linestyle='--')
    ax2.set_ylim(0, 100); ax2.legend(); ax2.grid(True)
    nombre = f"grafico_{timeframe}.png"
    plt.tight_layout(); plt.savefig(nombre); plt.close()
    return nombre

def analizar():
    señales = {}
    df_15m = None
    for tf in TIMEFRAMES:
        df = get_velas(SYMBOL, tf)
        df = calcular(df)
        ultima = df.iloc[-1]
        señal = "NEUTRO"
        if ultima['close'] > ultima['EMA50'] > ultima['EMA200'] and 50 < ultima['RSI'] < 70:
            señal = "SUBE"
        elif ultima['close'] < ultima['EMA50'] < ultima['EMA200'] and 30 < ultima['RSI'] < 50:
            señal = "BAJA"
        señales[tf] = señal
        print(f"{tf}: {señal} | Precio: {ultima['close']:.2f} | RSI: {ultima['RSI']:.1f}", flush=True)
        if tf == '15m':
            df_15m = df
    return señales, df_15m

def robot():
    print("ROBOT JEFE ENCENDIDO", flush=True)
    ultima_señal = ""
    while True:
        try:
            señales, df_15m = analizar()
            if señales['4h'] == "SUBE" and señales['1h'] == "SUBE" and señales['15m'] == "SUBE":
                if ultima_señal != "SUBE":
                    mensaje = f"🚀 JEFE VA A SUBIR! {SYMBOL}\n4H: SUBE\n1H: SUBE\n15m: SUBE\nEMA50 > EMA200"
                    grafico = hacer_grafico(df_15m, '15m', 'VA A SUBIR')
                    enviar_telegram(mensaje, grafico)
                    ultima_señal = "SUBE"
            elif señales['4h'] == "BAJA" and señales['1h'] == "BAJA" and señales['15m'] == "BAJA":
                if ultima_señal != "BAJA":
                    mensaje = f"📉 JEFE VA A BAJAR! {SYMBOL}\n4H: BAJA\n1H: BAJA\n15m: BAJA"
                    grafico = hacer_grafico(df_15m, '15m', 'VA A BAJAR')
                    enviar_telegram(mensaje, grafico)
                    ultima_señal = "BAJA"
            else:
                print("Esperando jefe... No hay acuerdo", flush=True)
            time.sleep(60)
        except Exception as e:
            print(f"Error jefe: {e}", flush=True)
            time.sleep(10)

# Arrancar robot en segundo plano
threading.Thread(target=robot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
