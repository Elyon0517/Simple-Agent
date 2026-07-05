import asyncio
import json

from pydantic import ValidationError

from app.ai.agents.market_analysis.schema import MarketAnalysisResult
from app.ai.runtime.text_runtime_service import TextRuntimeService
from config.settings import settings


async def main() -> None:
    if not settings.GEMINI_API_KEY:
        raise SystemExit("Missing GEMINI_API_KEY in .env")

    runtime = TextRuntimeService()
    events = await runtime.run_text_debug(
        """请分析 SPX 走势。用户提供的数据：
- 当前点位：5850
- 20日均线：5780，50日均线：5720
- 近期高点：5900，近期低点：5650
- RSI(14)：58
- 宏观：通胀数据偏温和，联储维持利率不变
请给出关键点位、趋势判断和短线路径。""",
        verbose=True,
    )

    final_text = runtime.extract_final_text(events)
    if not final_text:
        raise SystemExit("No final response from agent.")

    print("\n=== Raw Output ===")
    print(final_text)

    try:
        parsed = MarketAnalysisResult.model_validate_json(final_text)
        print("\n=== Validated MarketAnalysisResult ===")
        print(json.dumps(parsed.model_dump(), indent=2, ensure_ascii=False))
    except ValidationError as exc:
        print("\n=== Schema validation failed ===")
        print(exc)


if __name__ == "__main__":
    asyncio.run(main())
