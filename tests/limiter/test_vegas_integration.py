import asyncio
import time

import aiohttp
import pytest
import pytest_asyncio

from aioadaptive import AdaptiveClient, AdaptiveClientConfig

# Default configuration is to use `vegas` algorithm
client = AdaptiveClient()
# Same as doing
client = AdaptiveClient(AdaptiveClientConfig(algorithm="vegas"))
# Which is also the same as doing
client = AdaptiveClient(AdaptiveClientConfig(algorithm="vegas"))


async def main():
    async with client.use():
        # Do something with adaptive rate limiting client
        pass


asyncio.run(main())


pytestmark = pytest.mark.integration


# --- Test server setup ---
@pytest_asyncio.fixture
async def server_instance(aiohttp_server):
    async def handler(request):
        latency = float(request.query.get("latency"))
        await asyncio.sleep(latency)
        return aiohttp.web.json_response({"ok": True})

    app = aiohttp.web.Application()
    app.router.add_get("/", handler)
    server = await aiohttp_server(app)
    return server


@pytest.mark.asyncio
async def test_vegas_limiter_stable(server_instance):
    """Test the Vegas limiter integration with a server instance.

    Configures initial request with 100ms to set min_rtt.
    Then sends 200 requests at 150ms.
    Then validates the concurrency limit is not exceeded and stays at maximum queue size of 10.
    Reason:
      When: limit == 10
      Then: 10 * (1 - (0.1 / 0.15)) = 10 * 0.3 = 3
      Therefore: ALPHA < 3 < BETA => No Change in queue limit
    """
    url = f"{server_instance.scheme}://{server_instance.host}:{server_instance.port}"
    config = AdaptiveClientConfig(algorithm="vegas")
    client = AdaptiveClient(config)
    concurrency = client._throughput_limiter.limit
    total_requests = [0.1]
    total_requests += [0.15 for _ in range(200)]
    latencies = []

    async with aiohttp.ClientSession() as session:

        async def make_request(latency: float):
            async with client.use():
                start = time.perf_counter()
                resp = await session.get(f"{url}/?latency={latency}", timeout=2)
                resp.raise_for_status()
                end = time.perf_counter()
                latencies.append(end - start)

                assert client._capacity_limiter.total_tokens == concurrency, "In Progress: Concurrency limit exceeded"

        # Run requests concurrently
        await asyncio.gather(*(make_request(latency) for latency in total_requests))

    # Validate concurrency limit (should not exceed initial limit)
    assert client._capacity_limiter.total_tokens == concurrency, "Complete: Concurrency limit exceeded"


@pytest.mark.asyncio
async def test_vegas_limiter_decrease(server_instance):
    """Test the Vegas limiter integration with a server instance.

    Configures initial request with 100ms to set min_rtt.
    Then sends 2 requests at 200ms to force the limit to decrease.
    Then sends another 20 requests at 150ms to show the limit is stable.
    Validates the concurrency limit decreases to 8 and then stabilizes at 8.
    """
    url = f"{server_instance.scheme}://{server_instance.host}:{server_instance.port}"
    config = AdaptiveClientConfig(algorithm="vegas")
    client = AdaptiveClient(config)
    latencies = []

    async with aiohttp.ClientSession() as session:
        # Step 1: Set min_rtt with a fast request
        async with client.use():
            resp = await session.get(f"{url}/?latency=0.1", timeout=2)
            resp.raise_for_status()

        # Step 2: Force limit to decrease with high-latency requests
        async def make_request(latency: float) -> None:
            async with client.use():
                start = time.perf_counter()
                resp = await session.get(f"{url}/?latency={latency}", timeout=2)
                resp.raise_for_status()
                end = time.perf_counter()
                latencies.append(end - start)

        await asyncio.gather(*(make_request(0.2) for _ in range(2)))

        # Validate concurrency limit decreased to 8
        assert client._capacity_limiter.total_tokens == 8, (
            f"Expected limit to decrease to 8, got {client._capacity_limiter.total_tokens}"
        )

        # Step 3: Stabilize at new limit with more high-latency requests
        await asyncio.gather(*(make_request(0.15) for _ in range(50)))

        # Validate concurrency limit decreased to 8 and stabilized
        assert client._capacity_limiter.total_tokens == 8, (
            f"Expected limit to stabilize at 8, got {client._capacity_limiter.total_tokens}"
        )


@pytest.mark.asyncio
async def test_vegas_limiter_increase(server_instance):
    """Test the Vegas limiter integration with a server instance.

    Configures initial request with 100ms to set min_rtt.
    Then sends 2 requests at 100ms to force the limit to increase.
    Then sends another 20 requests at 130ms to show the limit is stable.
    Validates the concurrency limit increases to 12 and then stabilizes at 12.
    """
    url = f"{server_instance.scheme}://{server_instance.host}:{server_instance.port}"
    config = AdaptiveClientConfig(algorithm="vegas")
    client = AdaptiveClient(config)
    latencies = []

    async with aiohttp.ClientSession() as session:
        # Step 1: Set min_rtt with a fast request
        async with client.use():
            resp = await session.get(f"{url}/?latency=0.1", timeout=2)
            resp.raise_for_status()

        # Step 2: Force limit to decrease with high-latency requests
        async def make_request(latency: float) -> None:
            async with client.use():
                start = time.perf_counter()
                resp = await session.get(f"{url}/?latency={latency}", timeout=2)
                resp.raise_for_status()
                end = time.perf_counter()
                latencies.append(end - start)

        await asyncio.gather(*(make_request(0.1) for _ in range(2)))

        # Validate concurrency limit increased to 12
        assert client._capacity_limiter.total_tokens == 12, (
            f"Expected limit to increase to 12, got {client._capacity_limiter.total_tokens}"
        )

        # Step 3: Stabilize at new limit with more high-latency requests
        await asyncio.gather(*(make_request(0.13) for _ in range(50)))

        # Validate concurrency limit increased to 12 and stabilized
        assert client._capacity_limiter.total_tokens == 12, (
            f"Expected limit to stabilize at 12, got {client._capacity_limiter.total_tokens}"
        )
