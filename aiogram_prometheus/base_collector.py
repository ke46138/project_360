from __future__ import annotations

from typing import Any, Self

from prometheus_client import REGISTRY, CollectorRegistry
from prometheus_client.registry import Collector


class SafeCollector(Collector):
    DEFAULT_NAMESPACE = 'aiogram'

    registry: CollectorRegistry
    namespace: str

    COLLECTORS_STORAGE: dict[int, Self] = {}

    def __init__(self, registry: CollectorRegistry, namespace: str) -> None:
        self.registry = registry
        self.namespace = namespace

    @classmethod
    def get_collector(
        cls,
        registry: CollectorRegistry | None = None,
        namespace: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        if registry is None:
            registry = REGISTRY

        if namespace is None:
            namespace = cls.DEFAULT_NAMESPACE

        collector_id = hash((id(registry), hash(namespace)))

        if collector_id not in cls.COLLECTORS_STORAGE:
            cls.COLLECTORS_STORAGE[collector_id] = cls(registry, namespace, *args, **kwargs)
            registry.register(cls.COLLECTORS_STORAGE[collector_id])

        return cls.COLLECTORS_STORAGE[collector_id]
