import os
from datetime import date

from google.genai import types

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import load_artifacts
from simpleOutline.agent import root_agent as outline_agent
from simplePPT.agent import root_agent as ppt_agent
from create_model import create_model
from prompt import instruction

def setup_before_agent_call(callback_context: CallbackContext):
    """Setup the agent."""

    print("setup_before_agent_call")

model = create_model(model=os.environ["LLM_MODEL"], provider=os.environ["MODEL_PROVIDER"])

root_agent = Agent(
    model=model,
    name="super_agent",
    instruction=instruction,
    global_instruction=(
        f"""
        Todays date: {date.today()}
        """
    ),
    sub_agents=[outline_agent,ppt_agent],
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)
