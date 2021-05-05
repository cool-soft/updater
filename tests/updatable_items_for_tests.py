import asyncio

from updater.updatable_item.simple_updatable_item import SimpleUpdatableItem


class SleepingUpdatableItem(SimpleUpdatableItem):

    def __init__(self,
                 *args,
                 time_to_sleep: int = 0.1,
                 **kwargs
                 ) -> None:
        super().__init__(*args, **kwargs)
        self._time_to_sleep = time_to_sleep

    async def _run_update_async(self) -> None:
        await asyncio.sleep(self._time_to_sleep)
