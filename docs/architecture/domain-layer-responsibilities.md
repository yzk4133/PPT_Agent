# Domain 层职责说明

> **版本**: 1.0
> **日期**: 2025-02-04
> **主题**: DDD架构中Domain层的职责边界

---

## 🎯 核心原则：Domain层是核心

### DDD分层架构的核心理念

```
┌─────────────────────────────────────────────────┐
│              DDD 分层架构                         │
├─────────────────────────────────────────────────┤
│                                                   │
│  User Interface (API)                            │
│  ← 处理HTTP请求、响应                              │
│                                                   │
├─────────────────────────────────────────────────┤
│  Application Layer (Services)                     │
│  ← 编排业务流程、事务管理                          │
│                                                   │
├─────────────────────────────────────────────────┤
│  ↓ Domain Layer (核心) ↓                         │
│  ← 业务逻辑、领域模型、业务规则                    │
│  ← **不依赖任何外部技术**                          │
│                                                   │
├─────────────────────────────────────────────────┤
│  Infrastructure Layer                             │
│  ← 技术实现：数据库、缓存、消息队列等               │
│                                                   │
└─────────────────────────────────────────────────┘
```

---

## 📚 Domain 层的职责

### 1. Domain层管理什么？

#### ✅ 应该在 Domain 层的内容

```
domain/
├── entities/              # 实体（有ID的核心对象）
│   ├── task.py           ✓ 核心业务实体
│   └── presentation.py    ✓ 业务实体
│
├── value_objects/        # 值对象（无ID，由属性定义）
│   ├── requirement.py     ✓ 需求值对象
│   └── framework.py       ✓ PPT框架值对象
│
├── services/             # 领域服务（业务逻辑）
│   └── task_validation_service.py  ✓ 验证业务规则
│
├── events/               # 领域事件（业务事件）
│   └── task_events.py     ✓ TaskCreated, TaskCompleted等
│
├── exceptions/           # 领域异常（业务异常）
│   └── domain_exceptions.py ✓ TaskNotFound, ValidationError等
│
├── repositories/          # 仓储接口（不是实现）
│   └── task_repository.py  ✓ 定义数据访问接口
│
└── models/               # 领域模型
    └── ...
```

#### ❌ 不应该在 Domain 层的内容

```
domain/
├── ❌ 数据库相关
├── ❌ HTTP请求相关
├── ❌ 外部API集成
├── ❌ 技术框架细节
└── ❌ 基础设施实现
```

---

## 🔍 当前项目结构的问题

### 问题1: events 和 exceptions 重复

**当前结构**:
```
backend/
├── domain/
│   ├── events/
│   │   └── task_events.py          # 领域事件 ✓
│   └── exceptions/
│       ├── domain_exceptions.py    # 领域异常 ✓
│       ├── base_exceptions.py      # ⚠️ 应该在基础设施层
│       ├── api_exceptions.py       # ⚠️ 应该在API层
│       └── infrastructure_exceptions.py  # ⚠️ 应该在基础设施层
│
└── infrastructure/
    ├── events/
    │   └── event_store.py         # ⚠️ 事件存储实现
    └── exceptions/
        ├── auth.py                # 认证异常（技术性）
        ├── base.py                # 基础异常（技术性）
        ├── business.py            # 业务异常？
        └── validation.py          # 验证异常（技术性）
```

### 问题分析

#### infrastructure/exceptions/

| 文件 | 内容 | 应该在哪 |
|------|------|----------|
| `auth.py` | 认证异常（401, 403） | API层或Infrastructure |
| `base.py` | 基础异常类 | Infrastructure |
| `business.py` | 业务异常？ | **应该合并到Domain** |
| `validation.py` | 请求验证异常 | API层 |

#### domain/exceptions/

| 文件 | 内容 | 是否正确 |
|------|------|---------|
| `domain_exceptions.py` | TaskNotFound等 | ✓ 正确（领域异常） |
| `base_exceptions.py` | BaseApplicationError | ✓ 正确（基础类） |
| `api_exceptions.py` | API相关异常 | ⚠️ 应该移到API层 |
| `infrastructure_exceptions.py` | 基础设施异常 | ⚠️ 应该移到Infrastructure层或合并 |

---

## 🎯 正确的分层策略

### 策略1: 区分领域异常 vs 技术异常

```python
# ✅ domain/exceptions/ - 领域异常（业务相关）

class TaskNotFoundException(DomainError):
    """任务未找到 - 业务概念"""
    pass

class TaskValidationError(DomainError):
    """任务验证失败 - 业务规则"""
    pass

class InvalidStateTransitionError(DomainError):
    """状态转换错误 - 业务规则"""
    pass
```

```python
# ⚠️ infrastructure/exceptions/ - 技术异常（实现相关）

class DatabaseConnectionError(Exception):
    """数据库连接失败 - 技术问题"""
    pass

class LLMAPIError(Exception):
    """LLM API调用失败 - 技术问题"""
    pass

class CacheMissError(Exception):
    """缓存未命中 - 技术问题"""
    pass
```

### 策略2: 区分领域事件 vs 事件存储

```python
# ✅ domain/events/ - 领域事件（业务事件定义）

class TaskEvent:
    """任务事件 - 业务概念"""
    event_type: TaskEventType
    data: Dict[str, Any]  # 业务数据
    timestamp: datetime

# 工厂函数
def create_task_created_event(task_id: str, raw_input: str) -> TaskEvent:
    """创建任务创建事件 - 业务操作"""
    pass
```

```python
# ⚠️ infrastructure/events/ - 事件存储（技术实现）

class EventStore:
    """事件存储器 - 技术实现"""

    def save_event(self, event: TaskEvent):
        """保存事件到数据库 - 技术操作"""
        # 这里是数据库操作
        pass

    def get_events(self, aggregate_id: str):
        """从数据库读取事件 - 技术操作"""
        # 这里是数据库操作
        pass
```

---

## 📋 Domain 层应该管理的内容

### 1. 核心业务模型 (必须)

```
✅ entities/         - 实体（Task, Presentation）
✅ value_objects/   - 值对象（Requirement, Framework）
✅ services/        - 领域服务（业务逻辑）
```

### 2. 业务规则 (必须)

```
✅ 业务规则验证
✅ 状态转换规则
✅ 计算逻辑（如进度计算）
✅ 约束条件（如页数限制）
```

### 3. 领域事件 (必须)

```
✅ events/          - 领域事件定义
   ├─ TaskEventType (枚举)
   ├─ TaskEvent (类)
   └─ 工厂函数
```

### 4. 领域异常 (必须)

```
✅ exceptions/      - 领域异常
   ├─ TaskNotFoundException
   ├─ TaskValidationError
   ├─ InvalidStateTransitionError
   └─ 其他业务相关异常
```

### 5. 仓储接口 (必须)

```
✅ interfaces/       - 仓储接口
   └── repository.py  - 定义数据访问接口
```

### 6. 通信对象 (必须)

```
✅ communication/    - Agent间通信对象
   ├─ agent_context.py
   └─ agent_result.py
```

---

## ❌ Domain 层不应该管理的内容

### 1. 技术实现

```
❌ 数据库连接
❌ 缓存实现
❌ HTTP客户端
❌ 消息队列
❌ 事件存储实现
```

### 2. API相关

```
❌ HTTP请求/响应
❌ 控制器逻辑
❌ 路由配置
❌ API异常（404, 500等）
```

### 3. 基础设施细节

```
❌ 日志配置
❌ 配置文件加载
❌ 第三方库集成
❌ MCP工具加载
```

---

## 🔧 建议的目录结构

### 标准DDD结构

```
backend/
├── domain/                      # Domain层（核心业务）
│   ├── entities/              # ✓ 保留
│   ├── value_objects/        # ✓ 保留
│   ├── services/             # ✓ 保留
│   ├── events/               # ✓ 保留（领域事件）
│   ├── exceptions/           # ⚠️ 需要清理
│   │   ├── domain_exceptions.py      # ✓ 保留
│   │   └── base_exceptions.py        # ✓ 保留
│   ├── interfaces/           # ✓ 保留
│   ├── communication/        # ✓ 保留
│   └── models/               # ✓ 保留
│
├── infrastructure/             # Infrastructure层（技术实现）
│   ├── events/               # ⚠️ 保留（事件存储）
│   │   └── event_store.py
│   ├── exceptions/           # ⚠️ 需要清理
│   │   ├── auth.py                 # 技术异常
│   │   ├── base.py                 # 基础异常
│   │   ├── business.py             # 应该合并到domain
│   │   └── validation.py           # 应该移到API层
│   ├── database/             # ✓ 保留
│   ├── cache/                 # ✓ 保留
│   └── llm/                   # ✓ 保留
│
└── api/                         # API层
    ├── routes/               # ⚠️ 创建或加强
    │   └── ...
    └── exceptions/           # ⚠️ 创建
        └── api_exceptions.py  # API异常（404, 500等）
```

---

## 🎯 具体建议

### 建议1: 清理 domain/exceptions/

**保留**:
- `domain_exceptions.py` - 领域异常（TaskNotFound等）
- `base_exceptions.py` - 基础异常类

**移除**:
- `api_exceptions.py` → 移到 `api/exceptions/`
- `infrastructure_exceptions.py` → 合并到 `infrastructure/exceptions/`

### 建议2: 清理 infrastructure/exceptions/

**保留**:
- `auth.py` - 认证相关（技术性）
- `base.py` - 基础异常类
- `validation.py` - 请求验证（或移到API层）

**合并到Domain**:
- `business.py` → 合并到 `domain/exceptions/`

### 建议3: events 的职责分离

**domain/events/** - 领域事件（业务事件定义）
```python
# 定义事件类型
class TaskEventType(Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"

# 定义事件结构
@dataclass
class TaskEvent:
    event_type: TaskEventType
    data: Dict
    timestamp: datetime

# 定义工厂函数
def create_task_created_event(...) -> TaskEvent:
    ...
```

**infrastructure/events/** - 事件存储（技术实现）
```python
# 实现事件持久化
class EventStore:
    def append(self, event: TaskEvent):
        # 保存到数据库
        pass

    def get_events(self, aggregate_id: str):
        # 从数据库读取
        pass
```

---

## 📊 快速判断指南

### 如何判断某个类/文件应该在Domain层？

#### ✅ 应该在 Domain 层

1. **它描述业务概念吗？**
   - Task（任务）✓
   - Requirement（需求）✓
   - PPTFramework（PPT框架）✓

2. **它是业务规则的一部分吗？**
   - 状态转换规则 ✓
   - 验证规则 ✓
   - 计算逻辑 ✓

3. **它不依赖任何技术框架吗？**
   - 没有HTTP ✓
   - 没有数据库 ✓
   - 没有第三方库 ✓

#### ❌ 不应该在 Domain 层

1. **它描述技术实现吗？**
   - DatabaseConnection ✗
   - CacheStore ✗
   - HTTPClient ✗

2. **它是框架相关的吗？**
   - Flask/FastAPI ✗
   - SQLAlchemy ✗
   - Redis ✗

3. **它处理外部集成吗？**
   - LLM API调用 ✗
   - 文件系统操作 ✗
   - 消息队列 ✗

---

## 🎓 总结

### Domain层的核心职责

```
┌─────────────────────────────────────┐
│      Domain层的唯一职责              │
├─────────────────────────────────────┤
│                                     │
│  封装核心业务逻辑                   │
│  定义业务模型                       │
│  表达业务规则                       │
│  不依赖技术实现                     │
│  可独立测试和运行                   │
│                                     │
└─────────────────────────────────────┘
```

### 当前项目的问题

1. ⚠️ **events重复**：domain/events 和 infrastructure/events
2. ⚠️ **exceptions混乱**：domain/exceptions 包含了非领域异常
3. ⚠️ **职责不清**：domain/exceptions 包含了 infrastructure_exceptions

### 建议的改进

1. **清理 domain/exceptions/**
   - 只保留领域异常
   - 移除非领域异常到正确的层

2. **明确 events 职责**
   - domain/events：定义领域事件
   - infrastructure/events：实现事件存储

3. **建立清晰的边界**
   - Domain层：业务逻辑
   - Infrastructure层：技术实现
   - API层：接口适配

---

**结论**：Domain层应该管理**核心业务逻辑**，不管理**技术实现**。你观察到的混乱是真实存在的问题，应该进行清理！

需要我帮你重构这些文件，让结构更清晰吗？
