from updater.logging import logger
from updater.updatable_item.abstract_updatable_item import AbstractUpdatableItem


class AbstractAsyncUpdatableItem(AbstractUpdatableItem):

    async def update(self) -> None:
        logger.debug("Updating")
        await self._run_update()
        self._set_last_update_datetime_to_now()

    async def _run_update(self) -> None:
        raise NotImplementedError
