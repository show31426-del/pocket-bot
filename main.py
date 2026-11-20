import asyncio
import json
import logging
import os

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
        def no_duplicates(pairs):
            clean = {}
            for k, v in pairs:
                if k not in clean:
                    clean[k] = v
            return clean

        parsed = json.loads(ssid[2:], object_pairs_hook=no_duplicates)
        if (
            isinstance(parsed, list)
            and len(parsed) >= 2
            and isinstance(parsed[1], dict)
        ):
            auth_data = parsed[1]
            if "session" not in auth_data and "sessionToken" in auth_data:
                auth_data["session"] = auth_data["sessionToken"]
            return "42" + json.dumps(parsed, separators=(",", ":"))
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
