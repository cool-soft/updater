class UpdaterService:

    async def join(self) -> None:
        raise NotImplementedError

    def is_running(self) -> bool:
        raise NotImplementedError

    def stop_service(self) -> None:
        raise NotImplementedError

    async def run_updater_service_async(self) -> None:
        raise NotImplementedError
