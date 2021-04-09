import asyncio
import logging
from typing import List, Optional

import pandas as pd
from dateutil.tz import tzlocal

from updater.updatable_item.updatable_item import UpdatableItem
from updater.updater_service.updater_service import UpdaterService


class SimpleUpdaterService(UpdaterService):

    def __init__(self, item_to_update: Optional[UpdatableItem] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Creating instance")

        self._item_to_update = item_to_update

        self._logger.debug(f"Item to update is {item_to_update}")

    def set_item_to_update(self, item_to_update: UpdatableItem) -> None:
        self._logger.debug(f"Item to update is set to {item_to_update}")
        self._item_to_update = item_to_update

    async def run_updater_service_async(self) -> None:
        self._logger.debug(f"Service is started")

        while True:
            self._logger.debug("Running updating cycle")
            await self._update_items()
            await self._sleep_to_next_update()

    async def _update_items(self) -> None:
        self._logger.debug("Requested items to update unpacked graph")

        update_start_datetime = pd.Timestamp.now(tz=tzlocal())
        for item in self._get_unpacked_dependencies_graph(self._item_to_update):
            if self._is_need_update_item(item, update_start_datetime):
                self._logger.debug(f"Updating item {item.__class__.__name__}")
                await item.update_async()
        if self._is_need_update_item(self._item_to_update, update_start_datetime):
            await self._item_to_update.update_async()

        self._logger.debug("Items are updated")

    def _is_need_update_item(self, item: UpdatableItem, update_start_datetime: pd.Timestamp) -> bool:
        self._logger.debug("Check need update item")

        if item.get_last_updated_datetime() is None:
            need_update = True
        elif item.get_next_update_datetime() <= update_start_datetime:
            need_update = True
        else:
            need_update = self._is_item_dependencies_are_updated(item)

        self._logger.debug(f"Item need update status is {need_update}")
        return need_update

    def _is_item_dependencies_are_updated(self, item) -> bool:
        self._logger.debug(f"Check that item dependencies are updated for {item}")

        item_last_update_datetime = item.get_last_updated_datetime()
        item_dependencies = self._get_unpacked_dependencies_graph(item)

        dependencies_updated = False
        for dependency in item_dependencies:
            dependency_last_update_datetime = dependency.get_last_updated_datetime()
            if dependency_last_update_datetime is None:
                raise RuntimeError(f"Dependent item should not be updated before the dependency;"
                                   f"Dependency that need update is {dependency.__class__.__name__}")
            if dependency_last_update_datetime >= item_last_update_datetime:
                dependencies_updated = True
                break

        self._logger.debug(f"Item dependecies update status is {dependencies_updated}")
        return dependencies_updated

    async def _sleep_to_next_update(self) -> None:
        next_update_datetime = self._get_next_update_datetime()
        datetime_now = pd.Timestamp.now(tz=tzlocal())

        timedelta_to_next_update = next_update_datetime - datetime_now
        zero_timedelta = pd.Timedelta(seconds=0)
        timedelta_to_next_update = max(timedelta_to_next_update, zero_timedelta)

        self._logger.debug(f"Sleeping {timedelta_to_next_update}")
        await asyncio.sleep(timedelta_to_next_update.total_seconds())

    def _get_next_update_datetime(self) -> pd.Timestamp:
        self._logger.debug("Requested next update datetime")

        next_update_datetime = self._item_to_update.get_next_update_datetime()
        for item in self._get_unpacked_dependencies_graph(self._item_to_update):
            item_next_update_datetime = item.get_next_update_datetime()
            if next_update_datetime is None:
                next_update_datetime = item_next_update_datetime
            elif item_next_update_datetime is not None:
                next_update_datetime = min(next_update_datetime, item_next_update_datetime)

        self._logger.debug(f"Next update datetime is {next_update_datetime}")
        return next_update_datetime

    def _get_unpacked_dependencies_graph(self, item: UpdatableItem) -> List[UpdatableItem]:
        self._logger.debug("Unpacked dependencies graph is requested")

        unpacked_graph = []
        for dependency in item.get_dependencies():
            sub_graph = self._get_unpacked_dependencies_graph(dependency)
            for sub_item in sub_graph:
                if sub_item not in unpacked_graph:
                    unpacked_graph.append(sub_item)
            unpacked_graph.append(dependency)

        self._logger.debug(f"Dependency count of {item.__class__.__name__}: {len(unpacked_graph)}")
        return unpacked_graph
