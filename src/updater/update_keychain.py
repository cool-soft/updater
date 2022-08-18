from datetime import timedelta, datetime
from typing import List, Optional, Union

from updater.update_datetime_memento.update_datetime_memento import \
    AbstractUpdateDatetimeMemento, \
    InMemoryUpdateDatetimeMemento


class UpdateKeychain:

    def __init__(self,
                 update_interval: Optional[timedelta] = None,
                 dependencies: Optional[List[__qualname__]] = None,
                 update_datetime_memento: AbstractUpdateDatetimeMemento = None
                 ) -> None:
        self._update_interval = update_interval
        if dependencies is None:
            dependencies = []
        self._dependencies = dependencies.copy()
        if update_datetime_memento is None:
            update_datetime_memento = InMemoryUpdateDatetimeMemento()
        self._update_datetime_memento = update_datetime_memento

    def get_dependencies(self) -> List[__qualname__]:
        return self._dependencies.copy()

    def get_next_update_datetime(self) -> Union[datetime, None]:
        next_update_datetime = None
        last_update_datetime = self.get_last_update_datetime()
        if self._update_interval is not None and last_update_datetime is not None:
            next_update_datetime = last_update_datetime + self._update_interval
        return next_update_datetime

    def get_last_update_datetime(self) -> datetime:
        return self._update_datetime_memento.load()

    def set_last_update_datetime(self, update_datetime: datetime) -> None:
        self._update_datetime_memento.store(update_datetime)
