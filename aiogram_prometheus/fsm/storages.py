import logging
import time
from inspect import Traceback
from typing import Any

from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from prometheus_client import CollectorRegistry

from aiogram_prometheus.fsm.collectors import FsmCollector

logger = logging.getLogger('aiogram_prometheus')

__all__ = ('PrometheusWrapperStorage',)


class PrometheusWrapperStorage(BaseStorage):
    target_storage: BaseStorage
    collector: FsmCollector

    def __init__(
        self,
        target_storage: BaseStorage,
        registry: CollectorRegistry | None = None,
        namespace: str | None = None,
    ) -> None:
        self.target_storage = target_storage
        self.collector = FsmCollector.get_collector(registry, namespace)

    async def close(self) -> None:
        async with ActionStorageManager(self.collector, self.target_storage, 'close', None):
            await self.target_storage.close()

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        async with ActionStorageManager(self.collector, self.target_storage, 'set_state', key):
            await self.target_storage.set_state(key, state)

    async def get_state(self, key: StorageKey) -> str | None:
        async with ActionStorageManager(self.collector, self.target_storage, 'get_state', key):
            return await self.target_storage.get_state(key)

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        async with ActionStorageManager(self.collector, self.target_storage, 'set_data', key):
            await self.target_storage.set_data(key, data)

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        async with ActionStorageManager(self.collector, self.target_storage, 'get_data', key):
            return await self.target_storage.get_data(key)


class ActionStorageManager(object):
    started_at: float

    def __init__(
        self,
        collector: FsmCollector,
        storage: BaseStorage,
        action: str,
        key: StorageKey | None,
    ):
        self.collector = collector
        self.storage = storage
        self.action = action
        self.key = key

    async def __aenter__(self):
        self.started_at = time.time()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: Traceback | None = None,
    ):
        executing_time = self.started_at - time.time()
        self.collector.action(self.storage, self.action, self.key, executing_time, exc_value)

        return False
