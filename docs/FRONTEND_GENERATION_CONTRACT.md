# Frontend Generation Contract

## 1) Outline generation contract

### Frontend input

- Endpoint: `POST /api/presentation/outline`
- Body:
  - `prompt: string`
  - `numberOfCards: number`
  - `language: string`

### Required backend behavior

- Must forward `numberOfCards` to backend service and enforce it as target page count.
- Must stream outline in parseable title chunks (or explicit error text), no fake success placeholders.
- If model auth/config fails, must return explicit error text beginning with `错误：` or `Error:`.

### Frontend acceptance

- `outline.length === numSlides` is required to proceed.
- If error text is detected, show error banner + retry button and keep `outline=[]`.

## 2) Slide generation contract

### Frontend input

- Endpoint: `POST /api/presentation/generate`
- Body:
  - `title: string`
  - `outline: string[]`
  - `language: string`
  - `tone: string`
  - `numSlides: number`

### Required frontend behavior

- Start only if `outline.length === numSlides`.
- Route transition to `/presentation/[id]` then set `shouldStartPresentationGeneration=true`.
- Do not clear `shouldStartPresentationGeneration` during outline completion.

### Stream handling

- NDJSON line parsing must be robust to unknown payloads.
- `status-update` lines feed slide parser.
- Non-status lines append detail logs.
- On any stream failure, clear generation flags and show toast.

## 3) UI-state contract

- `isGeneratingOutline`: controls outline loading and disables outline trigger.
- `isGeneratingPresentation`: controls PPT streaming state.
- `outlineError`: single source of truth for outline failure messaging.

## 4) Regression checklist

1. Select `6 slides` and generate outline.
2. Verify result count is exactly 6 or explicit error (no placeholder deck).
3. Click `生成演示文稿`.
4. Verify auto transition to `/presentation/[id]` and stream updates appear.
5. Verify generation flags reset on completion or error.

## 5) Troubleshooting: 6页却返回10页

典型原因：前端连到了旧版后端实例（常见是 `localhost:8000` 上残留旧进程），而不是当前代码对应的实例。

### 判断方式

- 目录接口响应头应包含：`X-Generation-Contract: outline-v2`
- 幻灯片接口响应头应包含：`X-Generation-Contract: slides-v2`
- 如果缺失上述头，前端会提示“检测到旧版后端服务”。

### 处理方式

1. 停止旧进程或更换端口启动新后端（例如 `8010`）。
2. 在前端环境变量中设置正确网关：

- `FASTAPI_URL=http://127.0.0.1:8010`

3. 重启前端开发服务后再测试。
