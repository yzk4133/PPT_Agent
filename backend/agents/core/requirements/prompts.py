"""
需求解析智能体 - Prompt模板

定义用于LLM需求解析的Prompt模板和Few-Shot示例
"""

# 需求解析Prompt模板
REQUIREMENT_PARSER_PROMPT = """你是一名专业的PPT需求分析专家。

你的任务是分析用户的自然语言输入，提取结构化的PPT生成需求。

用户输入：{user_input}

请按照以下JSON格式输出需求（不要使用markdown包裹，直接输出JSON）：
{{
    "ppt_topic": "PPT主题",
    "page_num": 页数（整数，5-50之间）,
    "language": "语言代码（ZH-CN或EN-US）",
    "template_type": "模板类型（business_template, academic_template, creative_template）",
    "scene": "使用场景（business_report, academic_presentation, product_launch, training）",
    "tone": "语调风格（professional, casual, creative）",
    "core_modules": ["核心模块1", "核心模块2"],
    "need_research": true/false,
    "color_scheme": "色彩方案建议（如果有）",
    "target_audience": "目标受众（如果有）
}}

分析原则：
1. 如果用户指定了页数，使用用户指定的值；否则默认为10页
2. 检测输入语言：包含中文则为ZH-CN，否则为EN-US
3. 根据主题判断场景和模板类型
4. 如果主题需要专业知识（如技术、学术），设置need_research=true
5. 提取3-5个核心模块（如果用户提到）
"""

# Few-Shot示例（用于提升LLM理解）
FEW_SHOT_EXAMPLES = [
    {
        "input": "生成一份关于人工智能的PPT，15页",
        "output": {
            "ppt_topic": "人工智能",
            "page_num": 15,
            "language": "ZH-CN",
            "template_type": "business_template",
            "scene": "business_report",
            "tone": "professional",
            "core_modules": ["AI概述", "应用场景", "未来趋势"],
            "need_research": True,
        }
    },
    {
        "input": "帮我做一个学术研究的论文答辩PPT",
        "output": {
            "ppt_topic": "学术研究论文答辩",
            "page_num": 20,
            "language": "ZH-CN",
            "template_type": "academic_template",
            "scene": "academic_presentation",
            "tone": "professional",
            "core_modules": ["研究背景", "研究方法", "实验结果", "结论"],
            "need_research": True,
        }
    },
    {
        "input": "Create a 10-page presentation about Q3 sales report",
        "output": {
            "ppt_topic": "Q3 Sales Report",
            "page_num": 10,
            "language": "EN-US",
            "template_type": "business_template",
            "scene": "business_report",
            "tone": "professional",
            "core_modules": ["Executive Summary", "Sales Data", "Analysis", "Forecast"],
            "need_research": False,
        }
    },
    {
        "input": "帮我做一个创意设计的作品集展示PPT",
        "output": {
            "ppt_topic": "创意设计作品集展示",
            "page_num": 12,
            "language": "ZH-CN",
            "template_type": "creative_template",
            "scene": "product_launch",
            "tone": "creative",
            "core_modules": ["个人简介", "作品展示", "设计理念", "联系方式"],
            "need_research": False,
        }
    },
]

# JSON格式说明
JSON_FORMAT_INSTRUCTIONS = """
重要提示：
1. 直接输出JSON格式，不要使用markdown代码块（```json ... ```）
2. 所有字符串值用双引号包裹
3. 数字类型不要加引号
4. 布尔值使用 true/false，不要加引号
5. 数组使用方括号 []
6. 确保JSON格式正确，可以被json.loads()解析
"""
