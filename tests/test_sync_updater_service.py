from datetime import timedelta
from time import sleep

import pytest

from updatable_items_for_tests import SyncSleepingUpdatableItem
from updater.updater_service.sync_updater_service import SyncUpdaterService


class TestSyncUpdaterService:

    @pytest.fixture
    def item_1(self):
        return SyncSleepingUpdatableItem(
            update_interval=timedelta(seconds=2)
        )

    @pytest.fixture
    def item_2(self, item_1):
        return SyncSleepingUpdatableItem(
            dependencies=[item_1]
        )

    @pytest.fixture
    def item_3(self, item_1):
        return SyncSleepingUpdatableItem(
            dependencies=[item_1]
        )

    @pytest.fixture
    def item_4(self):
        return SyncSleepingUpdatableItem(
            update_interval=timedelta(seconds=3)
        )

    @pytest.fixture
    def item_to_update(self, item_2, item_3, item_4):
        return SyncSleepingUpdatableItem(
            dependencies=[item_2, item_3, item_4]
        )

    @pytest.fixture
    def updater_service(self, item_to_update):
        return SyncUpdaterService(item_to_update)

    # noinspection SpellCheckingInspection
    @pytest.mark.timeout(60)
    def test_service(self,
                     updater_service,
                     item_1,
                     item_2,
                     item_3,
                     item_4,
                     item_to_update):
        updater_service.start_service()
        while not updater_service.is_running():
            sleep(1)
        updater_service.stop_service()
        updater_service.join()

        assert item_1.get_last_update_datetime() < item_2.get_last_update_datetime()
        assert item_1.get_last_update_datetime() < item_3.get_last_update_datetime()
        assert item_2.get_last_update_datetime() < item_to_update.get_last_update_datetime()
        assert item_3.get_last_update_datetime() < item_to_update.get_last_update_datetime()
        assert item_4.get_last_update_datetime() < item_to_update.get_last_update_datetime()
