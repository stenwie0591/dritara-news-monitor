"""
Health check server — espone GET /health per monitoraggio esterno (es. UptimeRobot).
Risponde 200 OK se il sistema è attivo.
"""

from aiohttp import web
from loguru import logger


async def handle_health(request):
    return web.Response(text="OK", status=200)


async def run_healthcheck(host: str = "0.0.0.0", port: int = 8088) -> None:
    app = web.Application()
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Health check server attivo su {host}:{port}/health")
    # Non blocca — ritorna subito lasciando il server in background
