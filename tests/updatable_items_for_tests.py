import asyncio

from updater.updatable_item.updatable_item import UpdatableItem


class SleepingUpdatableItem(UpdatableItem):

    def __init__(self, *args, time_to_sleep: int = 0.1, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._time_to_sleep = time_to_sleep

    def set_time_to_sleep(self, time_to_sleep: int) -> None:
        self._time_to_sleep = time_to_sleep

    async def _run_update_async(self) -> None:
        await asyncio.sleep(self._time_to_sleep)