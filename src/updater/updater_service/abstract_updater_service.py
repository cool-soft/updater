class AbstractUpdaterService:

    async def join(self) -> None:
        raise NotImplementedError

    def is_running(self) -> bool:
        raise NotImplementedError

    async def stop_service(self) -> None:
        raise NotImplementedError

    async def start_service(self) -> None:
        raise NotImplementedError
