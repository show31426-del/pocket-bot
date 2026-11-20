import asyncio
import logging
import os

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pocket-bot")

app = FastAPI()

SSID = os.getenv("POCKET_OPTION", "").strip()
ASSET = os.getenv("ASSET", "EURUSD_otc")

async def automatic_trading_loop():
    logger.info("Automatic trading loop starting...")
    while True:
        try:
            if not SSID:
                logger.error("POCKET_OPTION environment variable is empty.")
                await asyncio.sleep(15)
                continue

            from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

            # Use SSID directly - DO NOT convert to JSON
            async with PocketOptionAsync(SSID) as client:
                logger.info("Connected to PocketOptionAsync.")
                while True:
                    logger.info("Scanning candles for %s...", ASSET)
                    await asyncio.sleep(10)
        except Exception:
            logger.exception("Bot loop hit an error; retrying soon...")
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(automatic_trading_loop())

@app.get("/")
def health_check():
    return {"status": "ok", "asset": ASSET, "mode": "automatic"}
