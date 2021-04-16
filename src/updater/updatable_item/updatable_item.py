import logging
from typing import List, Optional, Union
from datetime import datetime, timedelta, timezone


class UpdatableItem:

    def __init__(self,
                 update_interval: Optional[timedelta] = None,
                 dependencies: Optional[List[__qualname__]] = None):

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Creating instance")

        if dependencies is None:
            dependencies = []
        self._dependencies = dependencies
        self._update_interval = update_interval

        self._logger.debug(f"Dependency count {len(self._dependencies)}")
        self._logger.debug(f"Update interval {self._update_interval}")

        self._last_update_datetime = None

    def set_dependencies(self, dependencies: List[__qualname__]):
        self._logger.debug(f"Dependencies is set; count {len(self._dependencies)}")

        self._dependencies = dependencies

    def get_dependencies(self) -> List[__qualname__]:
        self._logger.debug(f"Dependencies list is requested")
        return self._dependencies.copy()

    def set_update_interval(self, update_interval: Union[timedelta, None]):
        self._logger.debug(f"Update interval is set to {update_interval}")
        self._update_interval = update_interval

    def get_next_update_datetime(self) -> Optional[datetime]:
        self._logger.debug("Requested next update datetime")

        next_update_datetime = None
        if self._update_interval is not None:
            next_update_datetime = self._last_update_datetime + self._update_interval

        self._logger.debug(f"Next update datetime is {next_update_datetime}")
        return next_update_datetime

    def get_last_updated_datetime(self) -> Optional[datetime]:
        self._logger.debug("Last update datetime is requested")
        self._logger.debug(f"Last update datetime is {self._last_update_datetime}")
        return self._last_update_datetime

    async def update_async(self) -> None:
        self._logger.debug(f"Updating")
        await self._run_update_async()
        self._set_last_update_datetime_to_now()

    async def _run_update_async(self) -> None:
        pass

    def _set_last_update_datetime_to_now(self) -> None:
        self._last_update_datetime = datetime.now(tz=timezone.utc)
        self._logger.debug(f"Last update datetime is set to {self._last_update_datetime}")
