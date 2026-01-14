# Agent间通信协议规范

## 消息格式标准
```json
{
  "id": "uuid-v4",
  "from": "agent_name",
  "to": "agent_name",
  "type": "request|response|notification",
  "payload": {},
  "timestamp": "2026-01-13T10:00:00Z",
  "priority": "high|medium|low"
}
```

## 通信模式

### 1. 请求-响应 (Request-Response)
同步调用模式，适用于需要立即返回结果的场景
```
A → B: request
B → A: response
```

### 2. 发布-订阅 (Pub-Sub)
异步通知模式，适用于事件广播
```
A → Topic: publish
B, C, D → Topic: subscribe
```

### 3. 广播 (Broadcast)
全局消息，所有Agent接收
```
A → All: broadcast
```

## 错误处理
- 超时: 30秒自动重试
- 失败: 返回标准错误码
- 重试: 最多3次指数退避
