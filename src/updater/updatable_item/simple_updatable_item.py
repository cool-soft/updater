from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union

from updater.logger import logger

from .abstract_updatable_item import AbstractUpdatableItem


class SimpleUpdatableItem(AbstractUpdatableItem):

    def __init__(self,
                 update_interval: Optional[timedelta] = None,
                 dependencies: Optional[List[__qualname__]] = None
                 ) -> None:
        if dependencies is None:
            dependencies = []
        self._dependencies = dependencies
        self._update_interval = update_interval

        self._last_update_datetime = None

        logger.debug(
            f"Creating instance:"
            f"dependency count: {len(self._dependencies)}"
            f"update_interval: {self._update_interval}"
        )

    def get_dependencies(self) -> List[__qualname__]:
        logger.debug("Dependencies list is requested")
        return self._dependencies.copy()

    def get_next_update_datetime(self) -> Union[datetime, None]:
        logger.debug("Requested next update datetime")

        next_update_datetime = None
        if self._update_interval is not None:
            next_update_datetime = self._last_update_datetime + self._update_interval

        logger.debug(f"Next update datetime is {next_update_datetime}")
        return next_update_datetime

    def get_last_update_datetime(self) -> Union[datetime, None]:
        logger.debug(f"Requested last update datetime: {self._last_update_datetime}")
        return self._last_update_datetime

    async def update_async(self) -> None:
        logger.debug("Updating")
        await self._run_update_async()
        self._set_last_update_datetime_to_now()

    async def _run_update_async(self) -> None:
        pass

    def _set_last_update_datetime_to_now(self) -> None:
        self._last_update_datetime = datetime.now(tz=timezone.utc)
        logger.debug(f"Last update datetime is set to {self._last_update_datetime}")
