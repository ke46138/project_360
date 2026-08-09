from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from aiogram.fsm.storage.base import BaseStorage, StorageKey
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from prometheus_client.metrics_core import InfoMetricFamily, Metric

from aiogram_prometheus.base_collector import SafeCollector

logger = logging.getLogger('aiogram_prometheus')


class FsmCollector(SafeCollector):
    """Collector for metric Storages action."""

    DEFAULT_NAMESPACE = 'aiogram_fsm'

    uniq_sets: dict[str, dict[str, set[Any]]]

    storages: set[BaseStorage]

    def __init__(self, registry: CollectorRegistry, namespace: str):
        super().__init__(registry, namespace)

        self.m_storage = Gauge(
            'storages',
            'Aiogram`s storages',
            ['storage_type'],
            registry=None,
        )

        self.m_storage_actinos = Counter(
            'actions',
            'Aiogram`s received messages',
            ['storage_type', 'action', 'error'],
            registry=None,
        )

        self.m_storage_actinos_time = Histogram(
            'actions_time',
            'Aiogram`s received messages',
            ['storage_type', 'action', 'error'],
            registry=None,
        )

        # self.m_bots = Gauge(
        #     'chats',
        #     'Count of uniq chats in storage',
        #     #['storage_type'],
        #     registry=None,
        # )

        self.m_chats = Gauge(
            'chats',
            'Count of uniq chats in storage',
            #['storage_type'],
            registry=None,
        )

        self.m_threads = Gauge(
            'threads',
            'Count of uniq threads in storage',
            #['storage_type'],
            registry=None,
        )

        self.m_destinies = Gauge(
            'destinies',
            'Count of uniq destinies in storage',
            #['storage_type'],
            registry=None,
        )

        self.m_users = Gauge(
            'users',
            'Count of uniq users in storage',
            #['storage_type'],
            registry=None,
        )

        self.m_business_connection = Gauge(
            'business_connection',
            'Count of uniq business_connection in storage',
            #['storage_type'],
            registry=None,
        )

        self.storages = set()
        self.uniq_sets = {}

    def action(
        self,
        storage: BaseStorage,
        action: str,
        key: StorageKey | None,
        executing_time: float,
        ex: BaseException | None = None,
    ):
        storage_type = type(storage).__name__

        self.storages.add(storage)

        if key is not None:
            if storage_type not in self.uniq_sets:
                self.uniq_sets[storage_type] = {
                    'bot_id': set(),
                    'chat_id': set(),
                    'thread_id': set(),
                    'destiny': set(),
                    'user_id': set(),
                    'business_connection_id': set(),
                }

            self.uniq_sets[storage_type]['bot_id'].add(key.bot_id)
            self.uniq_sets[storage_type]['chat_id'].add(key.chat_id)
            self.uniq_sets[storage_type]['thread_id'].add(key.thread_id)
            self.uniq_sets[storage_type]['destiny'].add(key.destiny)
            self.uniq_sets[storage_type]['user_id'].add(key.user_id)
            self.uniq_sets[storage_type]['business_connection_id'].add(key.business_connection_id)

        self.m_storage_actinos.labels(**{
            'storage_type': storage_type,
            'action': action,
            'error': type(ex).__name__,
        }).inc()

        self.m_storage_actinos_time.labels(**{
            'storage_type': storage_type,
            'action': action,
            'error': type(ex).__name__,
        }).observe(executing_time)

    def collect(self) -> Iterable[Metric]:
        for storage_type in self.uniq_sets:
            #self.m_bots.set(len(self.uniq_sets[storage_type]['bot_id']))
            self.m_chats.set(len(self.uniq_sets[storage_type]['chat_id']))
            self.m_threads.set(len(self.uniq_sets[storage_type]['thread_id']))
            self.m_destinies.set(len(self.uniq_sets[storage_type]['destiny']))
            self.m_users.set(len(self.uniq_sets[storage_type]['user_id']))
            self.m_business_connection.set(len(self.uniq_sets[storage_type]['business_connection_id']))

        for storage in self.storages:
            self.m_storage.labels(storage_type=type(storage).__name__,).set(1)

            yield InfoMetricFamily(
                'storages',
                'Info about aiogram storage',
                value={
                    'type': storage.__class__.__name__,
                },
            )

        yield from self.m_storage_actinos.collect()
        yield from self.m_storage_actinos_time.collect()

        #yield from self.m_bots.collect()
        yield from self.m_chats.collect()
        yield from self.m_threads.collect()
        yield from self.m_destinies.collect()
        yield from self.m_users.collect()
        yield from self.m_business_connection.collect()

        yield from self.m_storage.collect()
