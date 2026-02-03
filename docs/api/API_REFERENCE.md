# API 接口详细说明

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **API 版本**: v2.0.0

---

## 大纲与幻灯片

### 1. 生成大纲

生成 PPT 大纲，返回流式响应。

**端点**: `POST /api/ppt/outline/generate`

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "prompt": "生成关于人工智能的PPT大纲",
  "numberOfCards": 10,
  "language": "zh-CN"
}
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 | 可选值 |
|------|------|------|------|--------|
| prompt | string | ✅ | 用户输入的主题描述 | - |
| numberOfCards | integer | ✅ | 期望的卡片数量 | 1-100 |
| language | string | ✅ | 语言 | `zh-CN`, `en-US`, `ja-JP`, `ko-KR` |

**响应**: Server-Sent Events (SSE)

```
data: {"content": "# 人工智能发展历程\n\n"}
data: {"content": "## 1. 引言\n\n- 人工智能的定义\n"}
data: {"content": "## 2. 发展历程\n\n- 1950年代：图灵测试\n"}
```

**示例**:
```bash
curl -X POST http://localhost:8000/api/ppt/outline/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "生成关于AI的PPT", "numberOfCards": 10, "language": "zh-CN"}'
```

---

### 2. 生成幻灯片

根据大纲生成完整的幻灯片内容。

**端点**: `POST /api/ppt/slides/generate`

**请求体**:
```json
{
  "title": "人工智能应用",
  "outline": ["引言", "技术原理", "应用场景", "未来展望"],
  "language": "zh-CN",
  "tone": "professional",
  "numSlides": 10
}
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 | 可选值 |
|------|------|------|------|--------|
| title | string | ✅ | PPT 标题 | - |
| outline | array | ✅ | 大纲数组 | - |
| language | string | ✅ | 语言 | `zh-CN`, `en-US` 等 |
| tone | string | ❌ | 风格 | `professional`, `casual`, `creative` |
| numSlides | integer | ❌ | 幻灯片数量 | 默认 10 |

**响应**: Newline-Delimited JSON (NDJSON)

```
{"type": "status-update", "data": "正在生成第1页...", "metadata": ""}
{"type": "status-update", "data": "正在生成第2页...", "metadata": ""}
{"type": "artifact-update", "data": "<slide>...</slide>", "metadata": ""}
```

**事件类型**:

| type | 说明 |
|------|------|
| status-update | 状态更新（生成进度） |
| artifact-update | 内容更新（生成的幻灯片） |
| error | 错误信息 |

**示例**:
```bash
curl -X POST http://localhost:8000/api/ppt/slides/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI应用",
    "outline": ["引言", "技术原理", "应用场景"],
    "language": "zh-CN",
    "tone": "professional",
    "numSlides": 10
  }'
```

---

### 3. 健康检查

检查 API 网关及 Agent 服务的健康状态。

**端点**: `GET /api/ppt/health`

**响应**: JSON

```json
{
  "status": "healthy",
  "service": "ppt_generation_api",
  "timestamp": "2025-02-03T12:00:00"
}
```

**示例**:
```bash
curl http://localhost:8000/api/ppt/health
```

---

## 演示文稿管理

### 1. 创建演示文稿

创建新的演示文稿并开始生成。

**端点**: `POST /api/presentation/create`

**请求体**:
```json
{
  "outline": "人工智能的发展历程",
  "num_slides": 10,
  "language": "EN-US",
  "user_id": "user123",
  "theme": "modern",
  "style": "professional"
}
```

**响应**: JSON

```json
{
  "presentation_id": "ppt_20250203_120000_user123",
  "title": "人工智能的发展历程",
  "status": "generating",
  "message": "演示文稿创建成功，正在生成中..."
}
```

---

### 2. 查询生成进度

查询演示文稿的生成进度。

**端点**: `GET /api/presentation/progress/{presentation_id}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| presentation_id | string | 演示文稿 ID |

**响应**: JSON

```json
{
  "presentation_id": "ppt_20250203_120000_user123",
  "title": "人工智能的发展历程",
  "status": "generating",
  "stages": {
    "topics": {"stage": "topics", "completed": true, "count": 5},
    "research": {"stage": "research", "completed": false},
    "slides": {"stage": "slides", "completed": false}
  },
  "created_at": "2025-02-03T12:00:00"
}
```

---

### 3. 获取演示文稿详情

获取演示文稿的详细信息。

**端点**: `GET /api/presentation/detail/{presentation_id}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| presentation_id | string | 演示文稿 ID |

**响应**: JSON

```json
{
  "presentation_id": "ppt_20250203_120000_user123",
  "title": "人工智能的发展历程",
  "outline": "人工智能的发展历程...",
  "status": "completed",
  "generated_content": "```xml\n<PRESENTATION>\n...",
  "progress": {
    "status": "completed",
    "stages": {
      "topics": {"completed": true, "count": 5},
      "research": {"completed": true, "total": 5, "success": 5},
      "slides": {"completed": true, "total": 10}
    }
  },
  "created_at": "2025-02-03T12:00:00",
  "completed_at": "2025-02-03T12:05:00"
}
```

---

## 错误响应

所有错误响应遵循统一格式：

```json
{
  "status": "error",
  "error_code": "OUTLINE_GENERATION_FAILED",
  "message": "大纲生成失败",
  "timestamp": "2025-02-03T12:00:00"
}
```

### 常见错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|------------|------|
| VALIDATION_ERROR | 400 | 请求参数验证失败 |
| NOT_FOUND | 404 | 资源不存在 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| AGENT_ERROR | 500 | Agent 执行失败 |

---

## 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

## 分页

列表类接口支持分页：

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| limit | integer | 20 | 每页数量 |

**示例**:
```
GET /api/ppt/outline/list?user_id=123&page=1&limit=10
```

---

## 速率限制

当前版本未实现速率限制。生产环境建议添加：

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/ppt/outline/generate")
@limiter.limit("5/minute")
async def generate_outline(...):
    ...
```

---

## 认证授权

当前版本未实现认证。生产环境建议添加：

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/ppt/outline/generate")
async def generate_outline(
    request: GenerateOutlineRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # 验证 token
    ...
```

---

**版本**: 2.0.0
**最后更新**: 2025-02-03
