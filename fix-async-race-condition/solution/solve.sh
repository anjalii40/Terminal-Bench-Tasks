#!/bin/bash
python3 - << 'PYEOF'
import re

with open("/app/processor.py", "r") as f:
    source = f.read()

fixed = source.replace(
    "async def update_counter():\n    current = stats[\"counter\"]\n    await asyncio.sleep(0)\n    stats[\"counter\"] = current + 1",
    "async def update_counter():\n    async with lock:\n        stats[\"counter\"] += 1"
)

fixed = fixed.replace(
    "stats = {\"counter\": 0}",
    "stats = {\"counter\": 0}\nlock = asyncio.Lock()"
)

with open("/app/processor.py", "w") as f:
    f.write(fixed)
PYEOF

python3 /app/processor.py
