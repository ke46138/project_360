from collections.abc import Generator

import aiogram
from prometheus_client import CollectorRegistry, Counter, Histogram, Metric

from aiogram_prometheus.base_collector import SafeCollector


def get_unknown_attr(obj: object, attrs_str: str):
    attrs = attrs_str.split('.')

    for attr in attrs:
        obj = getattr(obj, attr, 'unknown')

    return obj


class UpdatesCollector(SafeCollector):
    def __init__(self, registry: CollectorRegistry, namespace: str) -> None:
        super().__init__(registry, namespace)

        self.m_events = Counter(
            'updates',
            'Aiogram`s updates',
            ['bot_id', 'bot_username', 'update_type'],
            namespace=self.namespace,
            registry=None,
        )
        self.m_events_processed = Counter(
            'updates_processed',
            'Aiogram`s processed updates',
            ['bot_id', 'bot_username', 'update_type', 'error'],
            namespace=self.namespace,
            registry=None,
        )

        self.m_events_processed_time = Histogram(
            'updates_time',
            'Aiogram`s processed updates spent time',
            ['bot_id', 'bot_username', 'update_type', 'error'],
            registry=None,
        )

        self.commands_total = Counter(
            'commands_total',
            'Total number of commands executed',
            ['command']
        )

    def manager(self):
        pass

    def update(self, update: aiogram.types.Update):
        self.m_events.labels(**{
            'bot_id': get_unknown_attr(update, 'bot.id'),
            'bot_username': get_unknown_attr(update, 'bot._me.username'),
            'update_type': update.event_type,
        }).inc()

        if update.message and update.message.text and update.message.text.startswith("/"):
            command, *_ = update.message.text.split(maxsplit=1)
            self.commands_total.labels(command=command).inc()

    def update_executed(
        self,
        update: aiogram.types.Update,
        executing_time: float,
        ex: BaseException | None = None,
    ):
        self.m_events_processed.labels(**{
            'bot_id': get_unknown_attr(update, 'bot.id'),
            'bot_username': get_unknown_attr(update, 'bot._me.username'),
            'update_type': update.event_type,
            'error': type(ex).__name__,
        }).inc()

        self.m_events_processed_time.labels(**{
            'bot_id': get_unknown_attr(update, 'bot.id'),
            'bot_username': get_unknown_attr(update, 'bot._me.username'),
            'update_type': update.event_type,
            'error': type(ex).__name__,
        }).observe(executing_time)

    def collect(self) -> Generator[Metric]:
        yield from self.m_events.collect()
        yield from self.m_events_processed.collect()
        yield from self.m_events_processed_time.collect()
