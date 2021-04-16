import asyncio
import logging
from enum import Enum
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from updater.updatable_item.updatable_item import UpdatableItem
from updater.updater_service.updater_service import UpdaterService


class SimpleUpdaterService(UpdaterService):

    class ServiceRunningState(Enum):
        RUNNING = 1
        STOPPING = 2
        STOPPED = 3

    def __init__(self, item_to_update: Optional[UpdatableItem] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Creating instance")

        self._item_to_update = item_to_update
        self._logger.debug(f"Item to update is {item_to_update}")

        self._service_running_state_condition = asyncio.Condition()
        self._service_running_state = self.ServiceRunningState.STOPPED

    def set_item_to_update(self, item_to_update: UpdatableItem) -> None:
        self._logger.debug(f"Item to update is set to {item_to_update}")
        self._item_to_update = item_to_update

    async def join(self) -> None:
        self._logger.debug("Waiting for service stop")

        async with self._service_running_state_condition:
            service_stopped_coroutine = self._service_running_state_condition.wait_for(
                lambda: self._service_running_state is self.ServiceRunningState.STOPPED
            )
            await service_stopped_coroutine

    def is_running(self) -> bool:
        self._logger.debug(f"Service running status is {self._service_running_state}")

        is_service_running = self._service_running_state is not self.ServiceRunningState.STOPPED
        return is_service_running

    async def stop_service(self) -> None:
        self._logger.debug("Stopping service")

        await self._make_service_status_stopping()

    async def _make_service_status_stopping(self):
        self._logger.debug("Making service status \"stopping\"")

        async with self._service_running_state_condition:
            self._service_running_state = self.ServiceRunningState.STOPPING
            self._service_running_state_condition.notify_all()

    async def run_updater_service_async(self) -> None:
        self._logger.debug("Service is started")

        await self._make_service_status_running()
        while True:
            self._logger.debug("Running updating cycle")
            await self._update_items()
            await self._sleep_to_next_update()
            if self._service_running_state is self.ServiceRunningState.STOPPING:
                await self._make_service_status_stopped()
                break

    async def _make_service_status_running(self) -> None:
        self._logger.debug("Making service status \"running\"")

        async with self._service_running_state_condition:
            self._service_running_state = self.ServiceRunningState.RUNNING
            self._service_running_state_condition.notify_all()

    async def _make_service_status_stopped(self) -> None:
        self._logger.debug("Making service status \"running\"")

        async with self._service_running_state_condition:
            self._service_running_state = self.ServiceRunningState.STOPPED
            self._service_running_state_condition.notify_all()

    async def _update_items(self) -> None:
        self._logger.debug("Requested items to update unpacked graph")

        update_start_datetime = datetime.now(tz=timezone.utc)
        unpacked_dependencies_graph = self._get_unpacked_dependencies_graph(self._item_to_update)
        for item in unpacked_dependencies_graph:
            if self._is_need_update_item(item, update_start_datetime):
                self._logger.debug(f"Updating item {item.__class__.__name__}")
                await item.update_async()
        if self._is_need_update_item(self._item_to_update, update_start_datetime):
            await self._item_to_update.update_async()

        self._logger.debug("Items are updated")

    def _is_need_update_item(self, item: UpdatableItem, update_start_datetime: datetime) -> bool:
        self._logger.debug("Check need update item")

        if item.get_last_updated_datetime() is None:
            need_update = True
        elif item.get_next_update_datetime() is not None and \
                item.get_next_update_datetime() <= update_start_datetime:
            need_update = True
        else:
            need_update = self._is_item_dependencies_are_updated(item)

        self._logger.debug(f"Item need update status is {need_update}")
        return need_update

    def _is_item_dependencies_are_updated(self, item) -> bool:
        self._logger.debug(f"Check that item dependencies are updated for {item}")

        item_last_update_datetime = item.get_last_updated_datetime()
        item_dependencies = self._get_unpacked_dependencies_graph(item)

        dependencies_updated = False
        for dependency in item_dependencies:
            dependency_last_update_datetime = dependency.get_last_updated_datetime()
            if dependency_last_update_datetime is None:
                raise RuntimeError(f"Dependent item should not be updated before the dependency;"
                                   f"Dependency that need update is {dependency.__class__.__name__}")
            if dependency_last_update_datetime >= item_last_update_datetime:
                dependencies_updated = True
                break

        self._logger.debug(f"Item dependencies update status is {dependencies_updated}")
        return dependencies_updated

    async def _sleep_to_next_update(self) -> None:
        next_update_datetime = self._get_next_update_datetime()
        datetime_now = datetime.now(tz=timezone.utc)

        timedelta_to_next_update = next_update_datetime - datetime_now
        zero_timedelta = timedelta(seconds=0)
        timedelta_to_next_update = max(timedelta_to_next_update, zero_timedelta)

        self._logger.debug(f"Sleeping {timedelta_to_next_update}")
        await self._wait_for_timeout_or_service_stopping(timedelta_to_next_update)

    def _get_next_update_datetime(self) -> datetime:
        self._logger.debug("Requested next update datetime")

        next_update_datetime = self._item_to_update.get_next_update_datetime()
        unpacked_dependencies_graph = self._get_unpacked_dependencies_graph(self._item_to_update)
        for item in unpacked_dependencies_graph:
            item_next_update_datetime = item.get_next_update_datetime()
            if next_update_datetime is None:
                next_update_datetime = item_next_update_datetime
            elif item_next_update_datetime is not None:
                next_update_datetime = min(next_update_datetime, item_next_update_datetime)

        self._logger.debug(f"Next update datetime is {next_update_datetime}")
        return next_update_datetime

    def _get_unpacked_dependencies_graph(self, item: UpdatableItem) -> List[UpdatableItem]:
        self._logger.debug("Unpacked dependencies graph is requested")

        unpacked_graph = []
        for dependency in item.get_dependencies():
            sub_graph = self._get_unpacked_dependencies_graph(dependency)
            for sub_item in sub_graph:
                if sub_item not in unpacked_graph:
                    unpacked_graph.append(sub_item)
            unpacked_graph.append(dependency)

        self._logger.debug(f"Dependency count of {item.__class__.__name__}: {len(unpacked_graph)}")
        return unpacked_graph

    async def _wait_for_timeout_or_service_stopping(self, timedelta_to_next_update: timedelta) -> None:
        sleep_coroutine = asyncio.sleep(timedelta_to_next_update.total_seconds())
        service_stopping_coroutine = self._wait_for_service_stopping_or_stopped()
        coroutines_to_wait = (sleep_coroutine, service_stopping_coroutine)
        done_futures, pending_futures = await asyncio.wait(coroutines_to_wait,
                                                           return_when=asyncio.FIRST_COMPLETED)
        for future in pending_futures:
            future.cancel()

    async def _wait_for_service_stopping_or_stopped(self) -> None:
        async with self._service_running_state_condition:
            await self._service_running_state_condition.wait_for(
                lambda: self._service_running_state in (self.ServiceRunningState.STOPPING,
                                                        self.ServiceRunningState.STOPPED)
            )
