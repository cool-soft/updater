import time
from datetime import timedelta, datetime

import pytest
from dateutil import tz

from updater.helpers import is_need_update_item
from updater.update_keychain import UpdateKeychain


class TestUpdaterKeychain:

    @pytest.fixture
    def keychain_1(self):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600)
        )

    @pytest.fixture
    def keychain_2(self, keychain_1):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            dependencies=[keychain_1]
        )

    @pytest.fixture
    def keychain_3(self, keychain_1):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            dependencies=[keychain_1]
        )

    @pytest.fixture
    def keychain_4(self, keychain_2, keychain_3):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            dependencies=[keychain_2, keychain_3]
        )

    @pytest.fixture
    def keychain_6(self):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600)
        )

    @pytest.fixture
    def keychain_7(self, keychain_6):
        return UpdateKeychain(
            update_interval=timedelta(seconds=1),
            dependencies=[keychain_6]
        )

    def test_need_update_by_dependency(self, keychain_1, keychain_2, keychain_3, keychain_4):
        datetime1 = datetime.now()
        for keychain in [keychain_1, keychain_2, keychain_3, keychain_4]:
            keychain.set_last_update_datetime(datetime1)

        time.sleep(1)
        datetime2 = datetime.now()
        keychain_1.set_last_update_datetime(datetime2)

        for keychain in [keychain_2, keychain_3, keychain_4]:
            assert is_need_update_item(keychain, datetime1) is True

    def test_need_update_timeout(self, keychain_6, keychain_7):
        datetime1 = datetime.now(tz=tz.UTC)
        for keychain in [keychain_6, keychain_7]:
            keychain.set_last_update_datetime(datetime1)

        time.sleep(2)
        datetime2 = datetime.now(tz=tz.UTC)

        assert is_need_update_item(keychain_7, datetime2) is True
