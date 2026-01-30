# 📝 MultiAgentPPT 之简单示例用于生成 PPT 大纲

本项目结合了 **A2A 框架** 与 **Google ADK 架构**，通过 SSE（Server-Sent Events）生成大纲。

---

## ✨ 项目亮点

- 🔗 **A2A + ADK 无缝集成**：实现多智能体任务执行
- 📄 **标准化 XML PPT 输出**：支持基于结构化大纲生成内容丰富、布局多样的 XML 演示文稿
- 🌐 **流式响应支持（SSE）**：支持客户端实时接收 Agent 执行状态及内容更新

---

## 📂 项目结构说明

| 文件 | 说明 |
|------|------|
| `a2a_client.py` | A2A 客户端封装，管理与服务端的交互 |
| `agent.py` | 主控制 Agent，调度执行任务 |
| `main_api.py` | FastAPI 主入口，暴露 SSE 接口 |
| `adk_agent_executor.py` | 实现 A2A 与 ADK 框架的集成逻辑 |
| `.env` | 环境变量配置，需包含 Google GenAI API 密钥等信息 |

---

## 📌 示例：主题生成任务

以下是可以测试的典型主题输入，系统将自动生成结构化内容：

- 电动汽车市场调研

---

## 🚀 运行方法

**1. 配置环境变量**

在 `.env` 文件中先修改模型和模型使用的 key。

**2. 启动服务**

```bash
python main_api.py
```

---

## 📤 A2A Client 输出结果示例

运行 `a2a_client.py` 后的输出示例：

```bash
python a2a_client.py
```

**输出结果：**

```json
{'id': '00857233-1927-4cd4-ab2d-4714b166967b', 'jsonrpc': '2.0', 'result': {'contextId': 'f9788c09-9cf5-44f3-8f00-aacb4199a0e6', 'final': False, 'kind': 'status-update', 'status': {'state': 'submitted'}, 'taskId': 'd9982ce3-f0de-4901-a21f-250d27448bf1'}}

{'id': '00857233-1927-4cd4-ab2d-4714b166967b', 'jsonrpc': '2.0', 'result': {'contextId': 'f9788c09-9cf5-44f3-8f00-aacb4199a0e6', 'final': False, 'kind': 'status-update', 'status': {'state': 'working'}, 'taskId': 'd9982ce3-f0de-4901-a21f-250d27448bf1'}}

... (中间的流式输出省略) ...

{'id': '00857233-1927-4cd4-ab2d-4714b166967b', 'jsonrpc': '2.0', 'result': {'contextId': 'f9788c09-9cf5-44f3-8f00-aacb4199a0e6', 'final': True, 'kind': 'status-update', 'status': {'state': 'completed'}, 'taskId': 'd9982ce3-f0de-4901-a21f-250d27448bf1'}}
```

---

## 🔧 Metadata 数据流动过程

对于携带 metadata 的数据，底层 metadata 元数据的流动过程如下：

### 数据流动步骤

1. **a2a_client.py**
   - 在 payload 中携带 metadata，例如 `send_message_payload` 中

2. **adk_agent_executor.py**
   - `async def execute` 中的 `context.message.metadata` 获取到元数据
   - `async def _process_request` 的 `await self._upsert_session` 在创建新的 session 时，把元数据放到 state 中：
   ```python
   app_name=self.runner.app_name,
   user_id="self",
   session_id=session_id,
   state={"metadata": metadata}
   ```

3. **agent.py**
   - `before_model_callback` 中可以看到元数据：
   ```python
   callback_context.state.get("metadata")
   ```

4. **工具调用**
   - 如果使用了工具，`tool_context` 中的 `tool_context.state.get("metadata")` 可以获取到元数据

5. **工具更新 metadata**
   - 工具调用时的元信息可以附加到 metadata 中：
   ```python
   metadata["tool_document_ids"] = document_ids
   tool_context.state["metadata"] = metadata
   ```

6. **agent.py after_model_callback**
   - 可以看到 metadata，包括工具更新的结果：
   ```python
   metadata = callback_context.state.get("metadata")
   ```

7. **adk_agent_executor.py 获取最终结果**
   - `async def _process_request` 的 `if event.is_final_response():` 中获取：
   ```python
   final_session = await self.runner.session_service.get_session(
       app_name=self.runner.app_name,
       user_id="self",
       session_id=session_id
   )
   print("最终的session中的结果final_session中的state: ", final_session.state)
   ```

8. **客户端打印最终 metadata**
   ```json
   {
     'id': '57071402-98d3-459d-a447-cbdf384e8323',
     'jsonrpc': '2.0',
     'result': {
       'artifact': {
         'artifactId': '156b98ac-3aa6-412c-97e2-6dff3148c46b',
         'metadata': {
           'user_data': 'hello',
           'tool_document_ids': [0, 1, 2, 3]
         },
         'parts': [
           {
             'kind': 'text',
             'text': '# 电动汽车全球市场概况...'
           }
         ]
       },
       'contextId': 'cdbf96d6-8a35-40e2-b3cd-e026c2c446f1',
       'kind': 'artifact-update',
       'taskId': '3d5160e2-42ef-4244-872f-e23046b685f1'
     }
   }
   ```
