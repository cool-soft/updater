from updater.logging import logger
from updater.updatable_item.abstract_updatable_item import AbstractUpdatableItem


class AbstractSyncUpdatableItem(AbstractUpdatableItem):

    def update(self) -> None:
        logger.debug("Updating")
        self._run_update()
        self._set_last_update_datetime_to_now()

    def _run_update(self) -> None:
        raise NotImplementedError
