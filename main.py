
import asyncio
import logging
import os
import json

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pocket-bot")

app = FastAPI()

SSID = (
    os.getenv("POCKET_OPTION_SSID")
    or os.getenv("POCKET_OPTION")
    or ""
).strip()

ASSET = os.getenv("ASSET", "EURUSD_otc")


def validate_ssid(ssid):
    if not ssid.startswith('42["auth",'):
        raise ValueError(
            "Invalid SSID format. Expected 42[\"auth\",...]"
        )

    try:
        data = json.loads(ssid[2:])
    except json.JSONDecodeError as e:
        raise ValueError("SSID contains invalid JSON") from e

    if not isinstance(data, list) or len(data) < 2:
        raise ValueError("Invalid authentication data")

    auth = data[1]

    if not isinstance(auth, dict):
        raise ValueError("Invalid authentication object")

    if not auth.get("session"):
        raise ValueError("Missing session field")

    if not isinstance(auth.get("uid"), int):
        raise ValueError("UID must be a number, not a string")

    return True


async def automatic_trading_loop():
    logger.info("Automatic trading loop starting...")

    while True:
        try:
            if not SSID:
                logger.error("Pocket Option SSID is missing.")
                await asyncio.sleep(15)
                continue

            validate_ssid(SSID)

            from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

            async with PocketOptionAsync(SSID) as client:
                logger.info("Connected to Pocket Option successfully.")

                while True:
                    logger.info("Scanning candles for %s...", ASSET)

                    candles = await client.candles(
                        ASSET, 60, count=10
                    )

                    logger.info("Received %s candles.", len(candles))

                    await asyncio.sleep(10)

        except Exception:
            logger.exception("Connection or scanning error. Retrying...")
            await asyncio.sleep(15)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(automatic_trading_loop())


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "asset": ASSET,
        "mode": "automatic"
    }
