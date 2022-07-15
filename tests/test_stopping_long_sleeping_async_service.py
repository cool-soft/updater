import asyncio
from datetime import timedelta

import pytest

from updatable_items_for_tests import AsyncSleepingUpdatableItem
from updater.updater_service.async_updater_service import AsyncUpdaterService


class TestStoppingLongSleepingService:

    @pytest.fixture
    def item_to_update(self):
        return AsyncSleepingUpdatableItem(
            update_interval=timedelta(hours=100)
        )

    @pytest.fixture
    def updater_service(self, item_to_update):
        return AsyncUpdaterService(item_to_update)

    # noinspection SpellCheckingInspection
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_service(self, updater_service, item_to_update):
        asyncio.get_running_loop().set_debug(True)

        await updater_service.start_service()
        while not updater_service.is_running():
            await asyncio.sleep(1)
        await updater_service.stop_service()
        await updater_service.join()
