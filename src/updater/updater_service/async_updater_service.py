import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from updater.logging import logger
from updater.updatable_item import AbstractAsyncUpdatableItem
from updater import helpers


class AsyncUpdaterService:

    class _ServiceRunningState(Enum):
        RUNNING = 1
        STOPPING = 2
        STOPPED = 3

    def __init__(self, item_to_update: AbstractAsyncUpdatableItem) -> None:
        self._item_to_update = item_to_update
        self._items_forced_update_queue = asyncio.Queue()
        self._wake_up_event = asyncio.Event()
        self._running_state_condition = asyncio.Condition()
        self._running_state = self._ServiceRunningState.STOPPED
        logger.debug(f"Creating instance. Item to update: {item_to_update}")

    async def force_item_update(self, item: AbstractAsyncUpdatableItem) -> None:
        logger.debug(f"Force item update {item.__class__.__name__}")
        all_items = helpers.get_dependencies_list(self._item_to_update)
        all_items.append(self._item_to_update)
        if item not in all_items:
            raise ValueError(f"Service does not own item  {item}")
        await self._items_forced_update_queue.put(item)
        self._wake_up_event.set()

    async def join(self, timeout: Optional[float] = None) -> None:
        logger.debug("Waiting for service stop")
        wait_service_stop_coroutine = self._running_state_condition.wait_for(
            lambda: self._running_state is self._ServiceRunningState.STOPPED,
        )
        async with self._running_state_condition:
            try:
                await asyncio.wait_for(
                    wait_service_stop_coroutine,
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                pass

    def is_running(self) -> bool:
        logger.debug(f"Service running status is {self._running_state}")
        return self._running_state is not self._ServiceRunningState.STOPPED

    async def stop_service(self) -> None:
        logger.debug("Stopping service")
        if self._running_state is self._ServiceRunningState.RUNNING:
            await self._set_running_state(self._ServiceRunningState.STOPPING)
            self._wake_up_event.set()

    async def start_service(self) -> None:
        logger.debug("Starting service")
        if self._running_state is self._ServiceRunningState.STOPPED:
            self._running_state = self._ServiceRunningState.RUNNING
            asyncio.create_task(self._run())
        else:
            logger.debug("Service already started")

    async def _run(self) -> None:
        logger.debug("Service is started")
        try:
            while self._running_state is self._ServiceRunningState.RUNNING:
                logger.debug("Run update cycle")
                if not self._items_forced_update_queue.empty():
                    await self._update_one_item_from_queue()
                await self._update_items_full_cycle()
                await self._sleep_to_next_update_or_signal()
        finally:
            await self._set_running_state(self._ServiceRunningState.STOPPED)

    async def _set_running_state(self, state: _ServiceRunningState) -> None:
        logger.debug(f"Set running state to {state.name}")
        async with self._running_state_condition:
            self._running_state = state
            self._running_state_condition.notify_all()

    async def _update_items_full_cycle(self) -> None:
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

    async def _update_one_item_from_queue(self) -> None:
        logger.debug("Requested forced item update")
        item_to_update: AbstractAsyncUpdatableItem = await self._items_forced_update_queue.get()
        logger.debug(f"Updating item {item_to_update.__class__.__name__}")
        await item_to_update.update()

    async def _sleep_to_next_update_or_signal(self) -> None:
        next_update_datetime = helpers.calc_next_update_datetime(self._item_to_update)
        timedelta_to_next_update = next_update_datetime - datetime.now(tz=timezone.utc)
        timedelta_to_next_update = max(timedelta_to_next_update, timedelta(seconds=0))
        logger.debug(f"Sleeping {timedelta_to_next_update}")
        try:
            await asyncio.wait_for(
                self._wake_up_event.wait(),
                timeout=timedelta_to_next_update.total_seconds()
            )
        except TimeoutError:
            pass
