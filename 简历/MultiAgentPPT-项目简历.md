**MultiAgentPPT** **多智能体文档生成系统** 2025.12-至今

围绕「自然语言 → PPT 自动生成」场景，使用 LangChain 搭建多智能体协作工作流，将复杂生成任务拆分为可调度子任务 DAG，打通规划、生成与导出的全流程自动化。

技术栈：Python, LangChain, PyTorch, MCP, FastAPI, MySQL

  **多智能体协作：**将串行生成流程拆分为多个专职 Agent，通过 LangChain DAG 调度与页面级并行 Pipeline 编排协作，提升生成吞吐与并行效率。

  **轻量模型训练：**基于 MiniMind 自建意图分类数据集，完成预训练 + SFT + LoRA 微调，训练 25.8M 参数模型降低对大模型调用依赖，实现低延迟、低成本识别。

  **统一工具系统：**搭建 Tool Registry 整合 LangChain Tools 与自定义 Skills，通过 MCP 协议统一 Agent 通信接口，实现动态注册与按需调用，提升扩展性。

  **分层记忆系统****：**MySQL 持久化用户画像，Redis L2 缓存复用历史上下文与生成结果，并结合降级与失效策略保障稳定性，实现低延迟、低成本的个性化 Agent 记忆能力。
