from collections.abc import AsyncGenerator

from google.adk.events.event import Event
from google.adk.runners import InMemoryRunner

from app.ai.agents.orchestrator.agent import orchestrator_agent
from app.ai.context.chat_context_builder import ChatContextBuilder
from app.ai.sessions.adk_session_service import AdkSessionService
from config.settings import settings


class TextRuntimeService:
    def __init__(self) -> None:
        self._runner = InMemoryRunner(
            agent=orchestrator_agent,
            app_name=settings.ADK_APP_NAME,
        )
        self._session_service = AdkSessionService(self._runner)
        self._context_builder = ChatContextBuilder()

    @property
    def session_service(self) -> AdkSessionService:
        return self._session_service

    async def run_text(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str,
    ) -> AsyncGenerator[Event, None]:
        user_content = self._context_builder.build_user_message(message)
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            yield event

    async def run_text_debug(
        self,
        message: str,
        *,
        verbose: bool = False,
    ) -> list[Event]:
        return await self._runner.run_debug(message, verbose=verbose)

    def extract_final_text(self, events: list[Event]) -> str | None:
        for event in reversed(events):
            if event.is_final_response() and event.content and event.content.parts:
                return event.content.parts[0].text
        return None
