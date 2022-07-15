import queue
import threading
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from updater.logging import logger
from updater.updatable_item.abstract_sync_updatable_item import AbstractSyncUpdatableItem
from updater.updater_service import helpers


class SyncUpdaterService:

    class _ServiceRunningState(Enum):
        RUNNING = 1
        STOPPING = 2
        STOPPED = 3

    def __init__(self, item_to_update: AbstractSyncUpdatableItem) -> None:
        self._item_to_update = item_to_update
        self._items_forced_update_queue = queue.Queue()
        self._wait_signal_condition = threading.Condition()
        self._running_state = self._ServiceRunningState.STOPPED
        self._runner_thread = threading.Thread(target=self._run)
        logger.debug(
            f"Creating instance:"
            f"item to update: {item_to_update}"
        )

    def force_item_update(self, item: AbstractSyncUpdatableItem):
        logger.debug(f"Forcing item update {item.__class__.__name__}")
        all_items = helpers.get_dependencies_list(self._item_to_update)
        all_items.append(self._item_to_update)
        if item not in all_items:
            raise ValueError(f"Item {item} does not owned by service")
        with self._wait_signal_condition:
            self._items_forced_update_queue.put(item)
            self._wait_signal_condition.notify_all()

    def join(self, timeout: Optional[float] = None) -> None:
        logger.debug("Waiting for service stop")
        self._runner_thread.join(timeout)

    def is_running(self) -> bool:
        logger.debug(f"Service running status is {self._running_state}")
        return self._running_state is not self._ServiceRunningState.STOPPED

    def stop_service(self) -> None:
        logger.debug("Stopping service")
        if self._running_state is self._ServiceRunningState.RUNNING:
            with self._wait_signal_condition:
                self._running_state = self._ServiceRunningState.STOPPING
                self._wait_signal_condition.notify_all()

    def start_service(self) -> None:
        logger.debug("Starting service")
        if self._running_state is self._ServiceRunningState.STOPPED:
            self._running_state = self._ServiceRunningState.RUNNING
            try:
                self._runner_thread.start()
            except RuntimeError:
                self._running_state = self._ServiceRunningState.STOPPED
                raise
        else:
            logger.debug("Service already started")

    def _run(self) -> None:
        logger.debug("Service is started")
        try:
            while self._running_state is self._ServiceRunningState.RUNNING:
                logger.debug("Run update cycle")
                self._update_one_item_from_queue()
                self._update_items_full_cycle()
                with self._wait_signal_condition:
                    if self._items_forced_update_queue.empty():
                        self._sleep_to_next_update_or_signal()
        finally:
            self._running_state = self._ServiceRunningState.STOPPED

    def _update_items_full_cycle(self) -> None:
        logger.debug("Updating item with dependencies")
        update_start_datetime = datetime.now(tz=timezone.utc)
        items_to_update_list = helpers.get_dependencies_list(self._item_to_update)
        items_to_update_list.append(self._item_to_update)
        for item in items_to_update_list:
            if helpers.is_need_update_item(item, update_start_datetime):
                logger.debug(f"Updating item {item.__class__.__name__}")
                # noinspection PyUnresolvedReferences
                item.update()
        logger.debug("Items are updated")

    def _sleep_to_next_update_or_signal(self) -> None:
        next_update_datetime = helpers.calc_next_update_datetime(self._item_to_update)
        timedelta_to_next_update = next_update_datetime - datetime.now(tz=timezone.utc)
        timedelta_to_next_update = max(timedelta_to_next_update, timedelta(seconds=0))
        logger.debug(f"Sleeping {timedelta_to_next_update}")
        with self._wait_signal_condition:
            timeout_expired = self._wait_signal_condition.wait(timedelta_to_next_update.total_seconds())
        if timeout_expired:
            logger.debug("Waked up by timeout")
        else:
            logger.debug("Waked up by signal")

    def _update_one_item_from_queue(self):
        logger.debug("Requested forced item update")
        if not self._items_forced_update_queue.empty():
            logger.debug("Queue is not empty")
            item_to_update: AbstractSyncUpdatableItem = self._items_forced_update_queue.get()
            logger.debug(f"Updating item {item_to_update.__class__.__name__}")
            item_to_update.update()
        else:
            logger.debug("Queue is empty!!!")
