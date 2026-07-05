from google.adk.agents.llm_agent import Agent

from app.ai.agents.market_analysis.agent import market_analysis_agent
from app.ai.agents.orchestrator.instruction import DESCRIPTION, INSTRUCTION
from config.settings import settings

orchestrator_agent = Agent(
    name="orchestrator",
    model=settings.GEMINI_TEXT_MODEL_DEFAULT,
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    sub_agents=[market_analysis_agent],
)

root_agent = orchestrator_agent
