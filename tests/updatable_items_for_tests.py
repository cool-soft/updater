import asyncio
from time import sleep

from updater.updatable_item import AbstractAsyncUpdatableItem, AbstractSyncUpdatableItem


class AsyncSleepingUpdatableItem(AbstractAsyncUpdatableItem):

    def __init__(self,
                 *args,
                 time_to_sleep: int = 0.1,
                 **kwargs
                 ) -> None:
        super().__init__(*args, **kwargs)
        self._time_to_sleep = time_to_sleep

    async def _run_update(self) -> None:
        await asyncio.sleep(self._time_to_sleep)


class SyncSleepingUpdatableItem(AbstractSyncUpdatableItem):

    def __init__(self,
                 *args,
                 time_to_sleep: int = 0.1,
                 **kwargs
                 ) -> None:
        super().__init__(*args, **kwargs)
        self._time_to_sleep = time_to_sleep

    def _run_update(self) -> None:
        sleep(self._time_to_sleep)
