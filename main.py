"""
Dritara News Monitor — entry point principale.
Avvia in parallelo:
  - Bot Telegram (long polling — ascolta comandi admin)
  - Scheduler (fetch giornaliero + pubblicazione oraria)
  - Health check server (GET /health per monitoraggio esterno)
"""

import asyncio
import sys

from loguru import logger

from src.bot import run_bot
from src.healthcheck import run_healthcheck
from src.scheduler import build_scheduler

# ── Logging ────────────────────────────────────────────────────
logger.remove()  # rimuove handler di default
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
)
logger.add(
    "logs/monitor.log",
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
)


async def main() -> None:
    logger.info("=== Dritara News Monitor avviato ===")

    # Avvia scheduler
    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler attivo — jobs programmati:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.name}")

    # Avvia health check server
    await run_healthcheck()

    # Avvia bot in long polling (blocca qui)
    try:
        await run_bot()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interruzione ricevuta")
    finally:
        scheduler.shutdown()
        logger.info("Scheduler fermato — Monitor spento")


if __name__ == "__main__":
    asyncio.run(main())
