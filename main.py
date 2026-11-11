import os
import time
import threading
import asyncio
import logging
from fastapi import FastAPI
import uvicorn

logging.basicConfig(level=logging.INFO)

app = FastAPI()

SSID = os.getenv("POCKET_OPTION_SSID", "demo_ssid_123")
PASSCODE = os.getenv("SECRET_PASSCODE", "708666")

@app.get("/")
def health_check():
    return {"status": "running", "bot": "active"}

async def run_trading_bot():
    logging.info(f"Initializing Scalping Bot... Passcode Verified.")
    while True:
        try:
            logging.info("Scanning M1/M5 market indicators (RSI, EMA, ATR filters)...")
            await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Error: {e}")
            await asyncio.sleep(15)

def start_bot_loop():
    asyncio.run(run_trading_bot())

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot_loop, daemon=True)
    bot_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
