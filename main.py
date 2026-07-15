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
from src.config import RuntimeSettings, get_settings, redact_runtime_secrets
from src.database import init_db
from src.healthcheck import run_healthcheck
from src.scheduler import build_scheduler

LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
    "{name}:{function}:{line} - {message}"
)


def configure_logging(settings: RuntimeSettings) -> None:
    """Configura i sink solo all'avvio, dopo la validazione dei settings."""
    logger.remove()
    logger.configure(
        patcher=lambda record: record.update(
            message=redact_runtime_secrets(record["message"], settings)
        )
    )
    logger.add(sys.stderr, level=settings.log_level.upper(), format=LOG_FORMAT)
    logger.add(
        "logs/monitor.log",
        level=settings.log_level.upper(),
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format=LOG_FORMAT,
    )


async def main() -> None:
    settings = get_settings().validated_for_runtime()
    configure_logging(settings)
    logger.info("=== Dritara News Monitor avviato ===")

    # Garantisce schema e seed prima che scheduler e bot interroghino il DB.
    init_db()

    # Avvia scheduler
    scheduler = build_scheduler(settings)
    scheduler.start()
    logger.info("Scheduler attivo — jobs programmati:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.name}")

    # Avvia health check server
    await run_healthcheck()

    # Avvia bot in long polling (blocca qui)
    try:
        await run_bot(settings)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interruzione ricevuta")
    finally:
        scheduler.shutdown()
        logger.info("Scheduler fermato — Monitor spento")


if __name__ == "__main__":
    asyncio.run(main())
