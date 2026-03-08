"""
Dritara News Monitor — entry point principale.
Avvia in parallelo:
  - Bot Telegram (long polling — ascolta comandi admin)
  - Scheduler (fetch giornaliero + pubblicazione oraria)
"""
import asyncio

from loguru import logger

from src.bot import run_bot
from src.scheduler import build_scheduler


async def main() -> None:
    logger.info("=== Dritara News Monitor avviato ===")

    # Avvia scheduler
    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler attivo — jobs programmati:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.name} — prossima esecuzione: {job.next_run_time}")

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
