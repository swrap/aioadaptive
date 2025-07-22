from typing import Self
from unittest.mock import Mock, call, patch

import pytest

from aioadaptive import AdaptiveClient, AdaptiveClientConfig
from aioadaptive.limiter._limiter import AbstractLimiter


@pytest.mark.asyncio
class TestAdaptiveClientUse:
    @pytest.fixture
    def limiter_mock(self):
        limiter = Mock(spec=AbstractLimiter)
        limiter.limit = 1
        limiter.update.return_value = 2  # Simulate new limit
        return limiter

    @pytest.fixture
    def vegas_limiter_patch(self, limiter_mock):
        with patch(
            "aioadaptive.client._adaptive_client.VegasLimiter",
            return_value=limiter_mock,
        ):
            yield

    @pytest.fixture
    def config(self: Self):
        return AdaptiveClientConfig(algorithm="vegas")

    @pytest.fixture
    def client(self: Self, config, vegas_limiter_patch):
        return AdaptiveClient(config)

    async def test_use_context_manager(self: Self, client):
        async with client.use() as c:
            assert c is client

    async def test_use_context_manager_limit_update(self: Self, client, limiter_mock):
        with patch("aioadaptive.client._adaptive_client.time") as time_mock:
            time_mock.time.side_effect = [0, 1]  # start, end
            async with client.use() as c:
                assert c is client
            assert limiter_mock.update.call_args_list == [
                call(1),
            ]
            assert client._capacity_limiter.total_tokens == 2

    async def test_use_context_manager_limit_exception(self: Self, client, limiter_mock):
        with pytest.raises(Exception, match="test exception"):
            async with client.use():
                raise Exception("test exception")
        assert limiter_mock.update.call_args_list == []
        assert client._capacity_limiter.total_tokens == 1


class TestAdaptiveClientConfig:
    def test_adaptive_client_config_default(self: Self):
        config = AdaptiveClientConfig()
        assert config.algorithm == "vegas"

    def test_adaptive_client_config_custom(self: Self):
        config = AdaptiveClientConfig(algorithm="vegas")
        assert config.algorithm == "vegas"

    def test_adaptive_client_config_invalid_algorithm(self: Self):
        config = AdaptiveClientConfig(algorithm="invalid")
        with pytest.raises(ValueError, match="Algorithm 'invalid' not supported"):
            AdaptiveClient(config)
