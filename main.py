import os
import asyncio
import logging
from fastapi import FastAPI
from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pocket-bot")

app = FastAPI()

SSID = os.getenv("POCKET_OPTION", "")
ASSET = os.getenv("ASSET", "EURUSD_otc")
AMOUNT = float(os.getenv("TRADE_AMOUNT", "1.0"))
DURATION = int(os.getenv("TRADE_DURATION", "60"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
TRADE_COOLDOWN = int(os.getenv("TRADE_COOLDOWN", "120"))


def calculate_ema(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = price * k + ema * (1 - k)
    return ema


def calculate_rsi(prices: list[float], period: int = 14) -> float | None:
    if len(prices) <= period:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def analyze_signal(closes: list[float]) -> str | None:
    ema_fast = calculate_ema(closes, 9)
    ema_slow = calculate_ema(closes, 21)
    rsi = calculate_rsi(closes, 14)
    if ema_fast is None or ema_slow is None or rsi is None:
        return None

    # Automatic M1 scalping rules: EMA trend + RSI filter
    if ema_fast > ema_slow and rsi < 70:
        return "call"
    if ema_fast < ema_slow and rsi > 30:
        return "put"
    return None


async def extract_closes(client: PocketOptionAsync, asset: str, period: int = 60, count: int = 50) -> list[float]:
    candles = await client.get_candles(asset, period, count)
    closes: list[float] = []
    if not candles:
        return closes
    for c in candles:
        if isinstance(c, dict):
            val = c.get("close") or c.get("c")
            if val is not None:
                closes.append(float(val))
        elif hasattr(c, "close"):
            closes.append(float(c.close))
    return closes


async def automatic_trading_loop():
    logger.info("Automatic trading loop starting...")
    if not SSID:
        logger.warning("POCKET_OPTION environment variable is empty. Bot will not trade.")
        return

    client = PocketOptionAsync(SSID)
    last_trade_time = 0.0

    while True:
        try:
            # Connect / ensure active connection
            await client.connect()

            closes = await extract_closes(client, ASSET, period=60, count=50)
            if len(closes) < 22:
                logger.info(f"Waiting for more candle data on {ASSET} (got {len(closes)} candles)...")
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            signal = analyze_signal(closes)
            now = asyncio.get_running_loop().time()

            if signal and (now - last_trade_time) >= TRADE_COOLDOWN:
                logger.info(f"Signal detected on {ASSET}: {signal.upper()} | Placing trade of ${AMOUNT}...")
                if signal == "call":
                    order = await client.buy(asset=ASSET, amount=AMOUNT, time=DURATION)
                else:
                    order = await client.sell(asset=ASSET, amount=AMOUNT, time=DURATION)

                last_trade_time = now
                logger.info(f"Automatic trade executed on {ASSET} ({signal.upper()}): {order}")
            elif signal:
                logger.info(f"Signal {signal.upper()} on {ASSET} skipped due to cooldown.")
            else:
                logger.info(f"Scanning {ASSET}: no entry signal yet.")

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Error in automatic trading loop: {e}")
            await asyncio.sleep(15)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(automatic_trading_loop())


@app.get("/")
def health_check():
    return {"status": "ok", "asset": ASSET, "mode": "automatic"}
