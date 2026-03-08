import asyncio
import yaml
import httpx
from datetime import datetime

async def check_feed(client, feed):
    name = feed["name"]
    url = feed["url"]
    try:
        r = await client.get(url, timeout=15, follow_redirects=True)
        status = "OK" if r.status_code == 200 else f"HTTP {r.status_code}"
        size = len(r.content)
        return (feed["level"], name, url, status, size)
    except Exception as e:
        return (feed["level"], name, url, f"ERRORE: {type(e).__name__}", 0)

async def main():
    with open("config/feeds.yaml") as f:
        config = yaml.safe_load(f)
    feeds = config["feeds"]

    print(f"\nDritara News Monitor — Test feed ({datetime.now().strftime('%H:%M:%S')})")
    print(f"Feed da testare: {len(feeds)}\n")

    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0 (compatible; DritaraBot/1.0)"}) as client:
        tasks = [check_feed(client, f) for f in feeds]
        results = await asyncio.gather(*tasks)

    ok = [r for r in results if r[3] == "OK"]
    ko = [r for r in results if r[3] != "OK"]

    print(f"{'LV':<4} {'TESTATA':<30} {'STATO':<20} {'BYTES':>8}")
    print("─" * 68)
    for lv, name, url, status, size in sorted(results, key=lambda x: (x[0], x[1])):
        icon = "✓" if status == "OK" else "✗"
        print(f"  {lv}  {name:<30} {icon} {status:<18} {size:>8,}")

    print("─" * 68)
    print(f"\nRisultato: {len(ok)}/{len(feeds)} feed OK", end="")
    if ko:
        print(f"  —  {len(ko)} KO:")
        for _, name, url, status, _ in ko:
            print(f"     • {name}: {status}")
    else:
        print(" — tutti operativi!")

asyncio.run(main())
