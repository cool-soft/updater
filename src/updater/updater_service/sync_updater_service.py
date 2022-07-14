import threading
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from updater.logging import logger
from updater.updatable_item.abstract_sync_updatable_item import AbstractSyncUpdatableItem
from updater.updater_service import helpers


class SyncUpdaterService:
    class ServiceRunningState(Enum):
        RUNNING = 1
        STOPPING = 2
        STOPPED = 3

    def __init__(self, item_to_update: AbstractSyncUpdatableItem) -> None:
        self._item_to_update = item_to_update
        self._service_state_condition = threading.Condition()
        self._service_state = self.ServiceRunningState.STOPPED
        self._runner_thread = threading.Thread(target=self._run)
        logger.debug(
            f"Creating instance:"
            f"item to update: {item_to_update}"
        )

    def join(self, timeout: Optional[float] = None) -> None:
        logger.debug("Waiting for service stop")
        self._runner_thread.join(timeout)

    def is_running(self) -> bool:
        logger.debug(f"Service running status is {self._service_state}")
        return self._runner_thread.is_alive()

    def stop_service(self) -> None:
        logger.debug("Stopping service")
        if self._runner_thread.is_alive():
            with self._service_state_condition:
                self._service_state = self.ServiceRunningState.STOPPING
                self._service_state_condition.notify_all()

    def start_service(self) -> None:
        logger.debug("Starting service")
        self._service_state = self.ServiceRunningState.RUNNING
        try:
            self._runner_thread.start()
        except RuntimeError:
            self._service_state = self.ServiceRunningState.STOPPED
            raise

    def _run(self) -> None:
        logger.debug("Service is started")
        try:
            while self._service_state is self.ServiceRunningState.RUNNING:
                logger.debug("Run update cycle")
                self._update_items()
                self._sleep_to_next_update()
        finally:
            self._service_state = self.ServiceRunningState.STOPPED

    def _update_items(self) -> None:
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

    def _sleep_to_next_update(self) -> None:
        next_update_datetime = helpers.calc_next_update_datetime(self._item_to_update)
        datetime_now = datetime.now(tz=timezone.utc)
        timedelta_to_next_update = next_update_datetime - datetime_now
        timedelta_to_next_update = max(timedelta_to_next_update, timedelta(seconds=0))
        logger.debug(f"Sleeping {timedelta_to_next_update}")
        with self._service_state_condition:
            self._service_state_condition.wait(timedelta_to_next_update.total_seconds())
