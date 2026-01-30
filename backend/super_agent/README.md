# super Agent，负责总的任务执行
1. 用户提出1个主题，然后大纲Agent负责生成大纲
2. 用户确认没有问题，那么ppt Agent开始生成ppt

# 🧭 Super Agent 工作流程图（Mermaid）

```mermaid
flowchart TD
    A[👋 用户发起提问<br>或打招呼] --> B[🧠 Super Agent 自我介绍<br>说明流程：先大纲后内容]
    B --> C[📝 用户提供研究主题或问题]
    C --> D[📤 调用 Outline Agent<br>生成结构性大纲]
    D --> E[📑 展示大纲给用户<br>用户确认或修改]
    
    E -->|确认大纲| F[🧠 调用 Content Agent<br>逐段生成详细内容]
    E -->|用户修改| D

    F --> G[📄 返回完整文档内容<br>支持流式输出或全文一次返回]
    G --> H[✅ 总结结果<br>可保存/导出/继续编辑]

    style A fill:#e0f7fa,stroke:#00acc1,stroke-width:2px
    style D fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px
    style F fill:#fce4ec,stroke:#d81b60,stroke-width:2px
    style H fill:#e8f5e9,stroke:#43a047,stroke-width:2px
```

# 缺点和现状
任务委派给某个子Agent，但是不能动态串联2个子Agent一起做某个任务。可能planner能实现，但是每个子Agent的状态怎么返回出来？
如果使用谷歌的ADK的Agent的Tool支持流式的返回吗？即把Agent作为tool呢？
A2A官方对多Agent的使用，把每个Agent作为工具使用。

# 启动SuperAgent
python main_api.py

# 测试客户端
python client.py


## 完整的文字版交流测试记录
```

```

