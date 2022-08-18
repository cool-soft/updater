from datetime import datetime, timezone

from updater.logging import logger
from updater.update_keychain import UpdateKeychain


class AbstractUpdatableItem(UpdateKeychain):

    def _set_last_update_datetime_to_now(self) -> None:
        datetime_now = datetime.now(tz=timezone.utc)
        self.set_last_update_datetime(datetime_now)
        logger.debug(f"Last update datetime is set to {datetime_now}")


class AbstractAsyncUpdatableItem(AbstractUpdatableItem):

    async def update(self) -> None:
        logger.debug("Updating")
        await self._run_update()
        self._set_last_update_datetime_to_now()

    async def _run_update(self) -> None:
        raise NotImplementedError


class AbstractSyncUpdatableItem(AbstractUpdatableItem):

    def update(self) -> None:
        logger.debug("Updating")
        self._run_update()
        self._set_last_update_datetime_to_now()

    def _run_update(self) -> None:
        raise NotImplementedError
