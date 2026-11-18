import requests, time, threading
from datetime import datetime
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Sergeant Bot is RUNNING!"

TOKEN = "9062727515:AAEqYM0PdRWmCUX85pcNHNQbIIEg32RM3T4"
CHAT_ID = "9230337312"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)

def ema(data, period):
    k = 2 / (period + 1)
    e = data[0]
    for p in data[1:]:
        e = p * k + e * (1 - k)
    return e

def rsi(closes, period=14):
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# --- NEW: LISTEN FOR /start ---
def listen():
    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"timeout": 30}
            if offset: params["offset"] = offset
            r = requests.get(url, params=params, timeout=35).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                text = msg.get("text", "")
                if text == "/start":
                    send("✅ Sergeant is ONLINE!\n\nI'm watching XAUUSD (PAXG) for you.\nI will send a signal when EMA 9 crosses EMA 21 + RSI confirms.\n\nWait for it... 🎯")
                elif text == "/status":
                    send("🟢 Sergeant is running on Render 24/7")
            time.sleep(1)
        except Exception as e:
            print("LISTEN ERROR:", e); time.sleep(5)

def run_bot():
    send("✅ SERGEANT BOT CLOUD 24/7 STARTED!")
    last_signal = None
    while True:
        try:
            r5 = requests.get("https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=50", timeout=10).json()
            closes5 = [float(k[4]) for k in r5]
            price = closes5[-1]
            ema9 = ema(closes5[-22:], 9)
            ema21 = ema(closes5[-22:], 21)
            prev9 = ema(closes5[-23:-1], 9)
            prev21 = ema(closes5[-23:-1], 21)
            rsi_val = rsi(closes5)
            r15 = requests.get("https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=15m&limit=30", timeout=10).json()
            closes15 = [float(k[4]) for k in r15]
            trend_up = ema(closes15, 9) > ema(closes15, 21)
            trend_down = ema(closes15, 9) < ema(closes15, 21)
            signal = None
            if prev9 < prev21 and ema9 > ema21 and 40 < rsi_val < 72 and trend_up:
                signal = "🟢 BUY"; tp = price + 8; sl = price - 4
            elif prev9 > prev21 and ema9 < ema21 and 20 < rsi_val < 60 and trend_down:
                signal = "🔴 SELL"; tp = price - 8; sl = price + 4
            if signal and signal != last_signal:
                last_signal = signal
                send(f"{signal} XAUUSD FAST 65%!\n\n💰 Entry: {price:.2f}\n🎯 TP: {tp:.2f} (+$8)\n🛑 SL: {sl:.2f} (-$4)\n📊 RSI: {rsi_val:.1f}\n⏰ {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(30)
        except Exception as e:
            print("ERROR:", e); time.sleep(30)

threading.Thread(target=run_bot, daemon=True).start()
threading.Thread(target=listen, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
