import asyncio
from datetime import timedelta

import pytest

from updatable_items_for_tests import AsyncSleepingUpdatableItem
from updater.updater_service.async_updater_service import AsyncUpdaterService


class TestAsyncUpdaterServiceForceUpdate:

    @pytest.fixture
    def item_1(self):
        return AsyncSleepingUpdatableItem(
            update_interval=timedelta(seconds=600)
        )

    @pytest.fixture
    def item_2(self, item_1):
        return AsyncSleepingUpdatableItem(
            dependencies=[item_1]
        )

    @pytest.fixture
    def item_3(self):
        return AsyncSleepingUpdatableItem()

    @pytest.fixture
    def item_to_update(self, item_2, item_3):
        return AsyncSleepingUpdatableItem(
            dependencies=[item_2, item_3]
        )

    @pytest.fixture
    def updater_service(self, item_to_update):
        return AsyncUpdaterService(item_to_update)

    # noinspection SpellCheckingInspection
    @pytest.mark.timeout(60)
    @pytest.mark.asyncio
    async def test_service(self,
                           updater_service,
                           item_1,
                           item_2,
                           item_3,
                           item_to_update):
        await updater_service.start_service()
        while not updater_service.is_running():
            await asyncio.sleep(1)
        await asyncio.sleep(5)
        await updater_service.force_item_update(item_1)
        await asyncio.sleep(5)
        await updater_service.stop_service()
        await updater_service.join()

        assert item_1.get_last_update_datetime() < item_2.get_last_update_datetime()
        assert item_1.get_last_update_datetime() > item_3.get_last_update_datetime()
        assert item_2.get_last_update_datetime() > item_3.get_last_update_datetime()
