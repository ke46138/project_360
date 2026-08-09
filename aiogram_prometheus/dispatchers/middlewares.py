import logging
import time
from collections.abc import Awaitable, Callable
from inspect import Traceback
from typing import Any, cast

import aiogram
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from prometheus_client import CollectorRegistry

from aiogram_prometheus.dispatchers.collectors import UpdatesCollector

logger = logging.getLogger('aiogram_prometheus')

__all__ = ('PrometheusUpdatesMiddleware',)


class PrometheusUpdatesMiddleware(BaseMiddleware):
    """Middleware for metrics messages in Dispatcher.

    ### Args

    - collector [PrometheusUpdatesMiddleware] optional

    ### Usage

    Need add to `dp.update.middleware`

    ### Example:

    ```
    from aiogram import Bot
    from aiogram_prometheus import PrometheusUpdatesMiddleware

    dp = Dispatcher()
    dp.update.middleware(PrometheusUpdatesMiddleware())
    ```
    """

    collector: UpdatesCollector

    def __init__(self, registry: CollectorRegistry | None = None, namespace: str | None = None) -> None:
        self.collector = UpdatesCollector.get_collector(registry, namespace)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        update = cast(aiogram.types.Update, event)

        async with UpdateMiddlewareManager(self.collector, update):
            return await handler(event, data)


class UpdateMiddlewareManager(object):
    started_at: float

    def __init__(
        self,
        collector: UpdatesCollector,
        update: aiogram.types.Update,
    ):
        self.collector = collector
        self.update = update

    async def __aenter__(self):
        self.collector.update(self.update)
        self.started_at = time.time()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: Traceback | None = None,
    ):
        delta_time = self.started_at - time.time()
        self.collector.update_executed(self.update, delta_time, exc_value)

        return False
