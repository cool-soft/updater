import asyncio
from datetime import timedelta

import pytest

from updatable_items_for_tests import SleepingUpdatableItem
from updater.updater_service.simple_updater_service import SimpleUpdaterService


class TestSimpleUpdaterService:

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
    def item_5(self, item_2, item_3, item_4):
        return SleepingUpdatableItem(
            dependencies=[item_2, item_3, item_4]
        )

    @pytest.fixture
    def updater_service(self):
        return SimpleUpdaterService()

    @pytest.fixture
    def updater_service_with_items(self, updater_service, item_5):
        updater_service.set_item_to_update(item_5)
        return updater_service

    # noinspection SpellCheckingInspection
    @pytest.mark.asyncio
    async def test_simple_updater_service(self,
                                          updater_service_with_items,
                                          item_1,
                                          item_2,
                                          item_3,
                                          item_4,
                                          item_5):

        asyncio.get_running_loop().set_debug(True)

        asyncio.create_task(updater_service_with_items.run_updater_service_async())
        while not updater_service_with_items.is_running():
            await asyncio.sleep(1)
        await asyncio.sleep(10)
        await updater_service_with_items.stop_service()
        await updater_service_with_items.join()

        assert item_1.get_last_updated_datetime() < item_2.get_last_updated_datetime()
        assert item_1.get_last_updated_datetime() < item_3.get_last_updated_datetime()
        assert item_2.get_last_updated_datetime() < item_5.get_last_updated_datetime()
        assert item_3.get_last_updated_datetime() < item_5.get_last_updated_datetime()
        assert item_4.get_last_updated_datetime() < item_5.get_last_updated_datetime()
