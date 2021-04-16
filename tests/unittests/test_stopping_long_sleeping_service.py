import asyncio
from datetime import timedelta

import pytest

from updatable_items_for_tests import SleepingUpdatableItem
from updater.updater_service.simple_updater_service import SimpleUpdaterService


class TestStoppingLongSleepingService:

    @pytest.fixture
    def item_to_update(self):
        return SleepingUpdatableItem(
            update_interval=timedelta(hours=100)
        )

    @pytest.fixture
    def updater_service(self):
        return SimpleUpdaterService()

    @pytest.fixture
    def updater_service_with_items(self, updater_service, item_to_update):
        updater_service.set_item_to_update(item_to_update)
        return updater_service

    # noinspection SpellCheckingInspection
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_simple_updater_service(self,
                                          updater_service_with_items,
                                          item_to_update):

        asyncio.get_running_loop().set_debug(True)

        asyncio.create_task(updater_service_with_items.run_updater_service_async())
        while not updater_service_with_items.is_running():
            await asyncio.sleep(1)
        await updater_service_with_items.stop_service()
        await updater_service_with_items.join()
