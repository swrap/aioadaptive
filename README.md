# Aio Adaptive

The goal is to enable an http adaptive rate limit library for python.
Project is based off of [Netflix Concurrency](https://github.com/Netflix/concurrency-limits), but for python!
This library is currently only useful in asyncio setup.
The initial setup allows for someone to configure the Vegas adaptive rate limit.

The library will automatically limit the outbound requests wrapped in `client.use()` context manager.
Within that manager it utilizes an async semaphore to limit the amount of concurrent calls for this client.

See the examples below for how to leverage it.

## Install

You can install `aioadaptive` using pip:

```bash
pip install aioadaptive
```

Or, if you use [uv](https://github.com/astral-sh/uv):

```bash
uv add aioadaptive
```

## How to Use

### Client Setup

```python
from aioadaptive import AdaptiveClient, AdaptiveClientConfig
from aioadaptive.limiter import VegasLimiter

# Default configuration is to use `vegas` algorithm
client = AdaptiveClient()
# Same as doing
client = AdaptiveClient(AdaptiveClientConfig(algorithm="vegas"))
# Which is also the same as doing
client = AdaptiveClient(AdaptiveClientConfig(algorithm=VegasLimiter()))


async def main():
   # Use the `client` wherever you want to have a persistent rate limit
   async with client.use():
      # Do something with adaptive rate limiting client
      pass


asyncio.run(main())
```

I.e. Multiple endpoint setup

```python
from aioadaptive import AdaptiveClient, AdaptiveClientConfig
from aioadaptive.limiter import VegasLimiter

# Create a client per API or endpoint. Anything within the `client.use` will be concurrently rate limited within `async with` block.
client1 = AdaptiveClient()
client2 = AdaptiveClient()

async def main():
   async with client1.use():
      # Make some http calls to endpoint 1
      # Will rate limit adaptively based on the latency
      ...
   async with client2.use():
      # Make some http calls to endpoint 2
      # Will rate limit adaptively based on the latency
      ...


asyncio.run(main())
```

### With aiohttp (async)

*Note* Keep in mind that `aiohttp` has default a [limit connections per host](https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.BaseConnector.limit) of 100.

```python
import aiohttp
from aioadaptive import AdaptiveClient
import asyncio

client = AdaptiveClient()

async def main():
   async with aiohttp.ClientSession() as session:
      async with client.use():
         async with session.get("https://example.com/") as resp:
            data = await resp.json()
            print(data)

asyncio.run(main())
```

### With httpx (async)

```python
import httpx
from aioadaptive import AdaptiveClient
import asyncio

client = AdaptiveClient()

async def main():
   async with httpx.AsyncClient() as session:
      async with client.use():
         resp = await session.get("https://example.com/")
         print(resp.json())

asyncio.run(main())
```

### With requests (sync, not recommended for adaptive concurrency)

> **Note:** `requests` is synchronous and blocking, so you won't get the full benefit of adaptive concurrency and is therefore not supported

## Developer Setup

1. Navigate to the Server Directory

   ```bash
   cd aioadaptive
   ```

2. Install Server Requirements

   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv sync
   ```

## Development Testing

   To run the full test suite (includes integration tests which can be slower)

   ```bash
   pytest
   ```

   Exclude integration tests

   ```bash
   pytest -m "not integration"
   ```
