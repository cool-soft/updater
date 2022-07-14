import asyncio
from datetime import timedelta

import pytest

from updatable_items_for_tests import SleepingUpdatableItem
from updater.updater_service.async_updater_service import AsyncUpdaterService


class TestAsyncUpdaterService:

    @pytest.fixture
    def item_1(self):
        return SleepingUpdatableItem(
            update_interval=timedelta(seconds=2)
        )

    @pytest.fixture
    def item_2(self, item_1):
        return SleepingUpdatableItem(
            dependencies=[item_1]
        )

    @pytest.fixture
    def item_3(self, item_1):
        return SleepingUpdatableItem(
            dependencies=[item_1]
        )

    @pytest.fixture
    def item_4(self):
        return SleepingUpdatableItem(
            update_interval=timedelta(seconds=3)
        )

    @pytest.fixture
    def item_to_update(self, item_2, item_3, item_4):
        return SleepingUpdatableItem(
            dependencies=[item_2, item_3, item_4]
        )

    @pytest.fixture
    def updater_service(self, item_to_update):
        return AsyncUpdaterService(item_to_update)

    # noinspection SpellCheckingInspection
    @pytest.mark.asyncio
    async def test_service(self,
                           updater_service,
                           item_1,
                           item_2,
                           item_3,
                           item_4,
                           item_to_update):
        asyncio.get_running_loop().set_debug(True)

        await updater_service.start_service()
        while not updater_service.is_running():
            await asyncio.sleep(1)
        await asyncio.sleep(10)
        await updater_service.stop_service()
        await updater_service.join()

        assert item_1.get_last_update_datetime() < item_2.get_last_update_datetime()
        assert item_1.get_last_update_datetime() < item_3.get_last_update_datetime()
        assert item_2.get_last_update_datetime() < item_to_update.get_last_update_datetime()
        assert item_3.get_last_update_datetime() < item_to_update.get_last_update_datetime()
        assert item_4.get_last_update_datetime() < item_to_update.get_last_update_datetime()
