import asyncio
import logging
import os
import re

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pocket-bot")

app = FastAPI()

SSID = os.getenv("POCKET_OPTION", "")
ASSET = os.getenv("ASSET", "EURUSD_otc")


def normalize_ssid(raw_ssid: str) -> str:
    ssid = raw_ssid.strip()
    if not ssid.startswith("42"):
        return ssid
    try:
        cleaned = re.sub(r',\s*"session"\s*:\s*"[^"]*"', "", ssid)
        cleaned = re.sub(r'"session"\s*:\s*"[^"]*"\s*,', "", cleaned)
        cleaned = re.sub(
            r'("sessionToken"\s*:\s*("[^"]*"))',
            r'\1,"session":\2',
            cleaned,
            count=1,
        )
        return cleaned
    except Exception:
        logger.exception("Failed to normalize SSID; passing raw value.")
        return ssid


async def automatic_trading_loop():
    logger.info("Automatic trading loop starting...")
    while True:
        try:
            if not SSID:
                logger.error("POCKET_OPTION environment variable is empty.")
                await asyncio.sleep(15)
                continue

            from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

            active_ssid = normalize_ssid(SSID)
            async with PocketOptionAsync(active_ssid) as client:
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
