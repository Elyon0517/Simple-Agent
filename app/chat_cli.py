import asyncio

from app.ai.runtime.text_runtime_service import TextRuntimeService
from config.settings import settings


async def main() -> None:
    if not settings.GEMINI_API_KEY:
        raise SystemExit("Missing GEMINI_API_KEY in .env")

    runtime = TextRuntimeService()
    session = await runtime.session_service.create_session(user_id="cli_user")

    print(f"Session: {session.id}")
    print("Type a message and press Enter. Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not message:
            continue
        if message.lower() in {"quit", "exit", "q"}:
            print("Bye.")
            break

        print("\nAgent:")
        async for event in runtime.run_text(
            user_id="cli_user",
            session_id=session.id,
            message=message,
        ):
            if event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    author = event.author or "agent"
                    print(f"[{author}] {text}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
