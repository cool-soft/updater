import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Awaitable

from updater.updater_service import helpers
from updater.logging import logger
from updater.updatable_item.abstract_async_updatable_item import AbstractAsyncUpdatableItem


class AsyncUpdaterService:

    class ServiceRunningState(Enum):
        RUNNING = 1
        STOPPING = 2
        STOPPED = 3

    def __init__(self, item_to_update: AbstractAsyncUpdatableItem) -> None:
        self._item_to_update = item_to_update

        self._running_state_condition = asyncio.Condition()
        self._running_state = self.ServiceRunningState.STOPPED

        logger.debug(
            f"Creating instance:"
            f"item_to_update: {item_to_update}"
        )

    async def join(self) -> None:
        logger.debug("Waiting for service stop")
        await self._wait_service_running_state(self.ServiceRunningState.STOPPED)

    def is_running(self) -> bool:
        return self._running_state != self.ServiceRunningState.STOPPED

    async def stop_service(self) -> None:
        logger.debug("Stopping service")
        if self._running_state is not self.ServiceRunningState.STOPPED:
            await self._set_service_running_state(self.ServiceRunningState.STOPPING)

    async def start_service(self) -> None:
        logger.debug("Starting service")
        await self._set_service_running_state(self.ServiceRunningState.RUNNING)
        asyncio.create_task(self._run())

    async def _run(self) -> None:
        logger.debug("Service is started")
        try:
            while True:
                logger.debug("Run update cycle")
                await self._update_items()
                await self._wait_for_first_completed_coroutines([
                    self._sleep_to_next_update(),
                    self._wait_service_running_state(self.ServiceRunningState.STOPPING)
                ])

                if self._running_state is not self.ServiceRunningState.RUNNING:
                    break

        finally:
            await self._set_service_running_state(self.ServiceRunningState.STOPPED)

    async def _wait_service_running_state(self, state: ServiceRunningState) -> None:
        logger.debug(f"Waiting for service state {state.name}")

        async with self._running_state_condition:
            await self._running_state_condition.wait_for(
                lambda: self._running_state is state
            )
            logger.debug(f"Service state is {self._running_state.name}")

    async def _set_service_running_state(self, state: ServiceRunningState) -> None:
        logger.debug(f"Making service running state {state.name}")
        async with self._running_state_condition:
            self._running_state = state
            self._running_state_condition.notify_all()

    async def _update_items(self) -> None:
        logger.debug("Requested items to update unpacked graph")

        update_start_datetime = datetime.now(tz=timezone.utc)
        items_to_update_list = helpers.get_dependencies_list(self._item_to_update)
        items_to_update_list.append(self._item_to_update)
        for item in items_to_update_list:
            if helpers.is_need_update_item(item, update_start_datetime):
                logger.debug(f"Updating item {item.__class__.__name__}")
                # noinspection PyUnresolvedReferences
                await item.update()

        logger.debug("Items are updated")

    # noinspection PyMethodMayBeStatic
    async def _wait_for_first_completed_coroutines(self,
                                                   coroutines: List[Awaitable]
                                                   ) -> None:
        logger.debug("Waiting for coroutines and cancel not done")
        _, pending_futures = await asyncio.wait(
            coroutines,
            return_when=asyncio.FIRST_COMPLETED
        )
        for future in pending_futures:
            future.cancel()

    async def _sleep_to_next_update(self) -> None:
        next_update_datetime = helpers.calc_next_update_datetime(self._item_to_update)
        datetime_now = datetime.now(tz=timezone.utc)

        timedelta_to_next_update = next_update_datetime - datetime_now
        zero_timedelta = timedelta(seconds=0)
        timedelta_to_next_update = max(timedelta_to_next_update, zero_timedelta)

        logger.debug(f"Sleeping {timedelta_to_next_update}")
        await asyncio.sleep(timedelta_to_next_update.total_seconds())
