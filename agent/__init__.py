import os

from agent.logging_config import configure_logging

configure_logging(level=os.getenv("AGENT_LOG_LEVEL", "INFO"))

