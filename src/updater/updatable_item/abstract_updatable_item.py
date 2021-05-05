from datetime import datetime
from typing import List, Union


class AbstractUpdatableItem:

    def get_dependencies(self) -> List[__qualname__]:
        raise NotImplementedError

    def get_next_update_datetime(self) -> Union[datetime, None]:
        raise NotImplementedError

    def get_last_update_datetime(self) -> Union[datetime, None]:
        raise NotImplementedError

    async def update_async(self) -> None:
        raise NotImplementedError
