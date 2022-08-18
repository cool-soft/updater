import time
from datetime import timedelta, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session

from updater.helpers import is_need_update_item
from updater.update_datetime_memento.update_datetime_db_repository import \
    UpdateDatetimeDBRecord, \
    UpdateDatetimeDBRepository
from updater.update_datetime_memento.update_datetime_memento import UpdateDatetimeMementoWithDBRepo
from updater.update_keychain import UpdateKeychain


class TestUpdaterKeychainWithDBStore:

    db_url = "sqlite:///:memory:"

    @pytest.fixture
    def session_factory(self):
        engine = create_engine(self.db_url)
        with engine.begin() as conn:
            UpdateDatetimeDBRecord.metadata.drop_all(conn)
            UpdateDatetimeDBRecord.metadata.create_all(conn)
        db_session_maker = sessionmaker(
            autocommit=False,
            bind=engine,
            class_=Session
        )
        session_factory = scoped_session(
            db_session_maker
        )
        return session_factory

    @pytest.fixture
    def repository(self, session_factory):
        return UpdateDatetimeDBRepository(session_factory)

    @pytest.fixture
    def keychain_1(self, session_factory, repository):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            update_datetime_memento=UpdateDatetimeMementoWithDBRepo(
                db_session_factory=session_factory,
                memento_name="keychain_1",
                update_datetime_repository=repository,
                remove_session_after_use=False
            )
        )

    @pytest.fixture
    def keychain_2(self, keychain_1, session_factory, repository):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            update_datetime_memento=UpdateDatetimeMementoWithDBRepo(
                db_session_factory=session_factory,
                memento_name="keychain_2",
                update_datetime_repository=repository,
                remove_session_after_use=False
            ),
            dependencies=[keychain_1]
        )

    @pytest.fixture
    def keychain_3(self, keychain_1, session_factory, repository):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            update_datetime_memento=UpdateDatetimeMementoWithDBRepo(
                db_session_factory=session_factory,
                memento_name="keychain_3",
                update_datetime_repository=repository,
                remove_session_after_use=False
            ),
            dependencies=[keychain_1]
        )

    @pytest.fixture
    def keychain_4(self, keychain_2, keychain_3, session_factory, repository):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            update_datetime_memento=UpdateDatetimeMementoWithDBRepo(
                db_session_factory=session_factory,
                memento_name="keychain_4",
                update_datetime_repository=repository,
                remove_session_after_use=False
            ),
            dependencies=[keychain_2, keychain_3]
        )

    @pytest.fixture
    def keychain_6(self, session_factory, repository):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            update_datetime_memento=UpdateDatetimeMementoWithDBRepo(
                db_session_factory=session_factory,
                memento_name="keychain_6",
                update_datetime_repository=repository,
                remove_session_after_use=False
            )
        )

    @pytest.fixture
    def keychain_7(self, keychain_6, session_factory, repository):
        return UpdateKeychain(
            update_interval=timedelta(seconds=600),
            update_datetime_memento=UpdateDatetimeMementoWithDBRepo(
                db_session_factory=session_factory,
                memento_name="keychain_7",
                update_datetime_repository=repository,
                remove_session_after_use=False
            ),
            dependencies=[keychain_6]
        )

    def test_need_update_by_dependency(self, keychain_1, keychain_2, keychain_3, keychain_4):
        datetime1 = datetime.now(tz=timezone.utc)
        for keychain in [keychain_1, keychain_2, keychain_3, keychain_4]:
            keychain.set_last_update_datetime(datetime1)

        time.sleep(1)
        datetime2 = datetime.now(tz=timezone.utc)
        keychain_1.set_last_update_datetime(datetime2)

        for keychain in [keychain_2, keychain_3, keychain_4]:
            assert is_need_update_item(keychain, datetime1) is True

    def test_need_update_timeout(self, keychain_7):
        datetime1 = datetime.now(tz=timezone.utc) - timedelta(seconds=1200)
        keychain_7.set_last_update_datetime(datetime1)

        datetime2 = datetime.now(tz=timezone.utc)
        assert is_need_update_item(keychain_7, datetime2) is True
