import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_worker(service, stop: asyncio.Event, interval: float):
    while not stop.is_set():
        try:
            await asyncio.to_thread(service.tick)
        except Exception:
            # Persisted sending intents survive errors. Do not log mail bodies/secrets.
            logger.error("Notification worker failed; inspect queue and persisted sending intents")
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except TimeoutError:
            pass
