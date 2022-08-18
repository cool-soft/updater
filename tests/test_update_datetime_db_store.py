from datetime import timedelta, datetime, timezone
from random import randint

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session

from updater.update_datetime_memento.update_datetime_db_repository import \
    UpdateDatetimeDBRecord, \
    UpdateDatetimeDBRepository


class TestUpdateDatetimeDBStore:

    db_url = "sqlite:///:memory:"
    records_to_store_count = 3

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
    def record_to_store(self):
        records = {}
        datetime_now = datetime.now(tz=timezone.utc)
        for i in range(self.records_to_store_count):
            records[f"record_{i}"] = datetime_now + timedelta(seconds=randint(0, 100))
        return records

    def test_set_get_update_datetime(self, session_factory, repository, record_to_store):
        with session_factory.begin() as session:
            for record_name, record_time in record_to_store.items():
                repository.set_last_update_datetime(record_name, record_time)
            session.commit()

        with session_factory.begin():
            for record_name, record_time in record_to_store.items():
                assert repository.get_last_update_datetime(record_name) == record_time
        session_factory.remove()

    def test_store_load_all_update_datetime(self, session_factory, repository, record_to_store):
        with session_factory.begin() as session:
            for record_name, record_time in record_to_store.items():
                repository.set_last_update_datetime(record_name, record_time)
            session.commit()

        with session_factory.begin():
            loaded_records = repository.get_all_last_updates_datetime()
        session_factory.remove()

        for record_name, record_time in record_to_store.items():
            assert loaded_records[record_name] == record_time
