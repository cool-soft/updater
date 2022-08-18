from datetime import datetime
from typing import Union, Dict, Iterator

from dateutil import tz
from sqlalchemy import select, Column, INTEGER, VARCHAR, DATETIME
from sqlalchemy.orm import scoped_session, declarative_base


class UpdateDatetimeDBRepository:

    def __init__(self, db_session_factory: scoped_session) -> None:
        self._session_factory = db_session_factory

    def set_last_update_datetime(self, record_name: str, update_datetime: datetime) -> None:
        session = self._session_factory()
        statement = select(UpdateDatetimeDBRecord).filter(UpdateDatetimeDBRecord.name == record_name)
        record = session.execute(statement).scalars().first()
        if record is not None:
            record.update_datetime = update_datetime.astimezone(tz.UTC)
            session.merge(record)
        else:
            record = UpdateDatetimeDBRecord(name=record_name, update_datetime=update_datetime.astimezone(tz.UTC))
            session.add(record)

    def get_last_update_datetime(self, record_name) -> Union[datetime, None]:
        last_update_datetime = None
        session = self._session_factory()
        statement = select(UpdateDatetimeDBRecord).filter(UpdateDatetimeDBRecord.name == record_name)
        record = session.execute(statement).scalars().first()
        if record is not None:
            last_update_datetime = record.update_datetime.replace(tzinfo=tz.UTC)
        return last_update_datetime

    def get_all_last_updates_datetime(self) -> Dict[str, datetime]:
        session = self._session_factory()
        statement = select(UpdateDatetimeDBRecord)
        # noinspection PyTypeChecker
        last_updates_datetime: Dict[str, datetime] = {}
        records: Iterator[UpdateDatetimeDBRecord] = session.execute(statement).scalars()
        for record in records:
            # noinspection PyTypeChecker
            last_updates_datetime[record.name] = record.update_datetime.replace(tzinfo=tz.UTC)
        return last_updates_datetime


UpdateDatetimeDBRecordBase = declarative_base()


class UpdateDatetimeDBRecord(UpdateDatetimeDBRecordBase):
    __tablename__ = "update_datetime"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(32), unique=True, nullable=False)
    update_datetime = Column(DATETIME)
