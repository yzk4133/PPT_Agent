**MultiAgentPPT** **多智能体协作系统**                                2025.12-至今

针对文档自动化生成场景，基于LangChain构建多智能体协作系统，通过多个专业化Agent的分工协作，实现从自然语言需求到PPT文档的自动转换。

技术栈：Python, LangChain, PyTorch, FastAPI, MySQL, Redis等。

·     **多智能体协作：**采用多智能体分层架构，设计MasterGraph协调器统一调度五大Agent，完成从需求解析到文档生成的全流程任务。PagePipeline实现页面级并行处理，StateGraph自动管理Agent间状态传递，构建高效的协作系统。

·     **轻量模型训练：**为准确解析用户需求，基于MiniMind开源项目训练专用意图识别模型。从零完成预训练、SFT训练流程，自主构建意图分类数据并通过LoRA微调，实现25.8M参数模型的意图识别能力。

·     **统一工具系统：**为管理各Agent的众多工具，设计统一注册表整合LangChain Tools、Python Skills、MD Skills三类20+工具，实现自动发现与按需调用，并集成MCP协议支持标准化通信。

·     **分层记忆系统：**为记住用户偏好并复用相似回答，通过MemoryAwareAgent适配层实现用户个性化与数据缓存。采用MySQL存储偏好、Redis实现L2缓存，配合优雅降级机制确保系统稳定运行。







**MultiAgentPPT 多智能体协作系统** | 2024.12-至今

面向企业文档自动化场景，构建基于LangChain的多智能体协作平台，实现自然语言到PPT的端到端生成。日均处理文档X份，平均生成耗时X秒。

技术栈：Python · LangChain · PyTorch · FastAPI · MySQL · Redis

• 多智能体架构：设计MasterGraph协调器调度5大专业化Agent，PagePipeline实现页面级并行处理，较串行方案效率提升X%；StateGraph管理状态流转，支持复杂工作流编排

• 轻量意图识别：基于MiniMind自研25.8M参数意图分类模型，LoRA微调后准确率达X%，CPU推理延迟<Xms，替代调用大模型方案，单次请求成本降低X%

• 统一工具平台：封装LangChain Tools/Python Skills/MD Skills三类20+工具，支持自动发现与MCP协议标准化通信，工具平均响应延迟<Xms

• 分层记忆机制：MySQL持久化用户偏好，Redis L2缓存热点数据，实现个性化推荐与结果复用，重复查询响应时间降低X%，系统可用性达99.X%



接下来要考虑更多的业务，实现了哪些功能。但现阶段只能先这样了。这还不是一个能交的版本，但是我要先看下一个项目了。
