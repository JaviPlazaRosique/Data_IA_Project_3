import os

from agent.logging_config import configure_logging

configure_logging(level=os.getenv("AGENT_LOG_LEVEL", "INFO"))

from agent.agent import root_agent  # noqa: E402  (re-export para `adk web`)

__all__ = ["root_agent"]

