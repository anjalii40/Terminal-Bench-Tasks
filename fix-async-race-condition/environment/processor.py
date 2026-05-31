import asyncio
import json

with open("/app/config.json") as f:
    config = json.load(f)

WORKERS = config["workers"]
INCREMENTS = config["increments"]

stats = {"counter": 0}

async def update_counter():
    current = stats["counter"]
    await asyncio.sleep(0)
    stats["counter"] = current + 1

async def increment_many(n):
    for _ in range(n):
        await update_counter()

async def main():
    tasks = [increment_many(INCREMENTS) for _ in range(WORKERS)]
    await asyncio.gather(*tasks)
    with open("/app/output.txt", "w") as f:
        f.write(str(stats["counter"]) + "\n")

asyncio.run(main())
