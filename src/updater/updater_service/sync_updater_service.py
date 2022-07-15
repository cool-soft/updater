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
        self._running_state_condition = threading.Condition()
        self._running_state = self._ServiceRunningState.STOPPED
        self._runner_thread = threading.Thread(target=self._run)
        logger.debug(
            f"Creating instance:"
            f"item to update: {item_to_update}"
        )

    def join(self, timeout: Optional[float] = None) -> None:
        logger.debug("Waiting for service stop")
        self._runner_thread.join(timeout)

    def is_running(self) -> bool:
        logger.debug(f"Service running status is {self._running_state}")
        return self._running_state is not self._ServiceRunningState.STOPPED

    def stop_service(self) -> None:
        logger.debug("Stopping service")
        if self._running_state is self._ServiceRunningState.RUNNING:
            self._set_service_running_state(self._ServiceRunningState.STOPPING)

    def start_service(self) -> None:
        logger.debug("Starting service")
        if self._running_state is self._ServiceRunningState.STOPPED:
            self._running_state = self._ServiceRunningState.RUNNING
            try:
                self._runner_thread.start()
            except RuntimeError:
                self._set_service_running_state(self._ServiceRunningState.STOPPED)
                raise

    def _run(self) -> None:
        logger.debug("Service is started")
        try:
            while self._running_state is self._ServiceRunningState.RUNNING:
                logger.debug("Run update cycle")
                self._update_items()
                self._sleep_to_next_update()
        finally:
            self._set_service_running_state(self._ServiceRunningState.STOPPED)

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
        timedelta_to_next_update = next_update_datetime - datetime.now(tz=timezone.utc)
        timedelta_to_next_update = max(timedelta_to_next_update, timedelta(seconds=0))
        logger.debug(f"Sleeping {timedelta_to_next_update}")
        self._wait_service_running_state(
            self._ServiceRunningState.STOPPING,
            timedelta_to_next_update.total_seconds()
        )

    def _wait_service_running_state(self,
                                    state: _ServiceRunningState,
                                    timeout: Optional[float] = None
                                    ) -> None:
        logger.debug(f"Waiting for service state {state.name}")
        with self._running_state_condition:
            self._running_state_condition.wait_for(
                lambda: self._running_state is state,
                timeout=timeout
            )
        logger.debug(f"Service state {self._running_state.name} is reached")

    def _set_service_running_state(self, state: _ServiceRunningState):
        logger.debug(f"Set service running state to {state.name}")
        with self._running_state_condition:
            self._running_state = state
            self._running_state_condition.notify_all()
