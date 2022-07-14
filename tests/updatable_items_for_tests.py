import asyncio

from updater.updatable_item.abstract_async_updatable_item import AbstractAsyncUpdatableItem


class SleepingUpdatableItem(AbstractAsyncUpdatableItem):

    def __init__(self,
                 *args,
                 time_to_sleep: int = 0.1,
                 **kwargs
                 ) -> None:
        super().__init__(*args, **kwargs)
        self._time_to_sleep = time_to_sleep

    async def _run_update(self) -> None:
        await asyncio.sleep(self._time_to_sleep)
