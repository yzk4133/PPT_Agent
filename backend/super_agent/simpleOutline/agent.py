import os
import random

from google.adk.agents import Agent
from create_model import create_model
from dotenv import load_dotenv
load_dotenv()

instruction = """
根据用户的描述生成大纲。仅生成大纲即可，无需多余说明。
输出示例格式如下：

# 第一部分主题
- 关于该主题的关键要点
- 另一个重要方面
- 简要结论或影响

# 第二部分主题
- 本部分的主要见解
- 支持性细节或示例
- 实际应用或收获
"""

model = create_model(model=os.environ["LLM_MODEL"], provider=os.environ["MODEL_PROVIDER"])

root_agent = Agent(
    name="outline_agent",
    model=model,
    description=(
        "generate outline"
    ),
    instruction=instruction
)
