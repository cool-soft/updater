from datetime import datetime

from sqlalchemy.orm import scoped_session
from updater.update_datetime_memento.update_datetime_db_repository import UpdateDatetimeDBRepository


class AbstractUpdateDatetimeMemento:

    def store(self, update_datetime: datetime) -> None:
        raise NotImplementedError

    def load(self) -> datetime:
        raise NotImplementedError


class UpdateDatetimeMementoWithDBRepo(AbstractUpdateDatetimeMemento):

    def __init__(self,
                 db_session_factory: scoped_session,
                 update_datetime_repository: UpdateDatetimeDBRepository,
                 memento_name: str,
                 remove_session_after_use: bool = True
                 ) -> None:
        self._session_factory = db_session_factory
        self._repository = update_datetime_repository
        self._memento_name = memento_name
        self._remove_session_after_use = remove_session_after_use

    def store(self, update_datetime: datetime) -> None:
        with self._session_factory.begin() as session:
            self._repository.set_last_update_datetime(self._memento_name, update_datetime)
            session.commit()
        if self._remove_session_after_use:
            self._session_factory.remove()

    def load(self) -> datetime:
        with self._session_factory.begin():
            last_update_datetime = self._repository.get_last_update_datetime(self._memento_name)
        if self._remove_session_after_use:
            self._session_factory.remove()
        return last_update_datetime


class InMemoryUpdateDatetimeMemento(AbstractUpdateDatetimeMemento):

    def __init__(self):
        self._last_update_datetime = None

    def store(self, update_datetime: datetime) -> None:
        self._last_update_datetime = update_datetime

    def load(self) -> datetime:
        return self._last_update_datetime
