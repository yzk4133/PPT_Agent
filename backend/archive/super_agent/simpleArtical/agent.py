import random
import os
from google.adk.agents import Agent
from create_model import create_model
from dotenv import load_dotenv
load_dotenv()


instruction = """
你是一位资深的文章撰写专家。你的任务是根据以下要求，用Markdown格式生成专业的文章。
"""

SOME_EXAMPLE_IAMGES = """
一些可能用到的电动汽车的图片
2025年4月，全球纯电动车销量同比增长38%.
https://n.sinaimg.cn/spider20250610/598/w955h443/20250610/d5d4-b0eb5848953ded18fbc44aefb452923d.png

2025年4月，电动汽车中国同比增速51%
https://n.sinaimg.cn/spider20250610/663/w855h608/20250610/27b7-9119b6ad6f21a0fdd477e8736232bad2.png

美国2025年4月销量9.54万辆，同比下降4%
https://n.sinaimg.cn/spider20250610/560/w981h379/20250610/f372-46624c7063942fbca5f6f8a933128f9c.png

特斯拉2025年4月销量8.48万辆，同比下降17%
https://n.sinaimg.cn/spider20250610/473/w868h405/20250610/d80c-d608870a0938449e561f725bc00c169a.png

电动汽车卡通图片
https://n.sinaimg.cn/spider20250621/120/w1440h1080/20250621/f8d9-7d234d7b43fda7ec916d01fb81555bae.jpg

ppt背景图：
https://file.51pptmoban.com/d/file/2022/09/13/b2d85362febcf895e78916e0696f1a59.jpg

ppt风景图
https://c-ssl.duitang.com/uploads/blog/202111/27/20211127170036_ecc10.png

ppt背景图2
https://c-ssl.duitang.com/uploads/item/201909/24/20190924003225_luvye.png

"""

model = create_model(model=os.environ["LLM_MODEL"], provider=os.environ["MODEL_PROVIDER"])

root_agent = Agent(
    name="article_agent",
    model=model,
    description=(
        "Write the artical content based on the provided outline"
    ),
    instruction=instruction+SOME_EXAMPLE_IAMGES
)
