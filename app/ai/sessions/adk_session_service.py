from google.adk.runners import InMemoryRunner
from google.adk.sessions.session import Session

from config.settings import settings


class AdkSessionService:
    def __init__(self, runner: InMemoryRunner) -> None:
        self._runner = runner

    @property
    def app_name(self) -> str:
        return settings.ADK_APP_NAME

    async def create_session(self, user_id: str) -> Session:
        return await self._runner.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id,
        )

    async def get_session(self, user_id: str, session_id: str) -> Session | None:
        return await self._runner.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
