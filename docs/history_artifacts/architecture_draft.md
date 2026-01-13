# 系统架构设计草案

## 核心模块
1. **协调器Agent (Coordinator)**: 负责任务分解和流程控制
2. **内容生成Agent (ContentGenerator)**: 生成PPT文本内容
3. **视觉设计Agent (DesignAgent)**: 负责布局和视觉设计
4. **代码生成Agent (CodeGenerator)**: 生成PPTX代码

## 数据流
```
用户需求 → 协调器分析 → 任务分解
         ↓
    并行处理 ← ← ← ← ← ← ←
    ↓          ↓           ↓
内容生成   视觉设计    代码生成
    ↓          ↓           ↓
    └─ → → → 结果合成 → → → ┘
              ↓
          PPT输出
```

## 技术选型理由
- **Claude API**: 内容理解能力强，适合复杂任务
- **FastAPI**: 高性能异步框架
- **React**: 组件化开发，易于维护
