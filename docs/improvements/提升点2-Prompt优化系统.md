# 提升点 2: Prompt 优化系统

**重要性**: ⭐⭐⭐⭐
**难度**: ⭐⭐⭐⭐ (较难)
**预期收益**: 质量 +15-30%, 长期积累
**实施周期**: 1-2 月
**建议时机**: 数据充足后（50+ 任务样本）

---

## 一、什么是 Prompt 优化系统？

### 1.1 核心概念

**Prompt 优化系统**是指：基于历史任务的执行数据，**自动发现 Prompt 的问题**，并**生成改进建议**或**直接优化 Prompt** 的系统。

```
传统方式:
  手写 Prompt → 发现效果不好 → 手动修改 → 测试 → 重复

Prompt 优化系统:
  Prompt → 运行任务 → 收集数据 → 分析问题 → 自动优化 → 验证效果
                                              ↓
                                       持续改进
```

### 1.2 为什么需要 Prompt 优化？

| 问题 | 说明 |
|------|------|
| **Prompt 主观性强** | 不同人写的 Prompt 效果差异大 |
| **难以知道好坏** | 没运行前不知道 Prompt 是否有效 |
| **手动优化成本高** | 需要反复试验、对比 |
| **缺乏数据支撑** | 优化决策凭感觉，不是凭数据 |
| **难以持续改进** | 没有系统化的优化流程 |

### 1.3 Prompt 优化的价值

```
假设 ContentAgent 的初始 Prompt：
  "请为这个页面生成内容"

运行 100 个任务后，发现：
  - 40% 的任务内容过短
  - 30% 的任务内容偏离主题
  - 20% 的任务结构混乱

优化后的 Prompt：
  "请为这个页面生成内容，要求：
   1. 内容至少 200 字
   2. 紧密围绕页面主题
   3. 使用清晰的要点结构"

效果：
  ✅ 内容过短的问题减少到 10%
  ✅ 内容偏离的问题减少到 5%
  ✅ 结构混乱的问题减少到 5%

质量提升：+30%
```

---

## 二、核心挑战（诚实说明）

### 2.1 数据需求挑战

| 数据类型 | 需求量 | 现实情况 |
|---------|--------|---------|
| **任务样本** | 100+ 个 | 可能只有 10-20 个 |
| **质量评分** | 每个样本都需要 | 缺乏系统的评分 |
| **Prompt 版本** | 记录每次使用的 Prompt | 通常没有记录 |
| **对比数据** | 同一任务的不同 Prompt 版本 | 很少收集 |

### 2.2 评估难题

```python
# 问题：如何判断一个 Prompt 是否"更好"？

# 场景 A: 使用 LLM 评估
cost = 每次评估额外调用 LLM
     = 每个任务 +10% 成本
accuracy = LLM 评估可能不准确

# 场景 B: 用户反馈
feedback = 用户很少主动反馈
         = 数据量太小

# 场景 C: 客观指标（如字数）
limit = 只能评估部分维度
       = 无法评估内容质量

# 结论：没有完美的评估标准！
```

### 2.3 优化算法挑战

```python
# 问题：如何自动"优化" Prompt？

# 方法 1: 让 LLM 自己优化
→ 陷入"元问题"：LLM 如何知道怎么改会更好？
→ 容易"幻觉"：可能改了反而更差

# 方法 2: 强化学习
→ 需要数千个样本
→ 训练成本极高
→ 不切实际

# 方法 3: 遗传算法/搜索
→ 需要定义"搜索空间"和"目标函数"
→ 评估每个候选 Prompt 需要运行任务
→ 成本高昂

# 结论：没有通用的自动化优化方法！
```

### 2.4 验证困境

```
假设优化了 Prompt：
  新 Prompt = 旧 Prompt + 改进

如何验证新 Prompt 确实更好？

方法 A: 在历史数据上回测
  → 问题：历史数据是用旧 Prompt 生成的
  → 不公平的对比

方法 B: 在新任务上 A/B 测试
  → 问题：任务条件不同，无法控制变量
  → 需要大量实验

方法 C: 人工评估
  → 问题：主观、耗时
  → 无法大规模进行

结论：验证效果很难！
```

---

## 三、实现路径（从简单到复杂）

### 路径 1: 人工分析 + 手动优化（最现实）

#### 概念
系统提供数据分析工具，人类根据分析结果手动优化 Prompt。

#### 实现方案

```python
class PromptAnalyzer:
    """Prompt 分析工具（辅助人工决策）"""

    def __init__(self):
        self.task_history = []

    async def analyze_agent_performance(
        self,
        agent_name: str,
        recent_tasks: list
    ):
        """
        分析 Agent 的表现

        Returns:
            分析报告，包括：
            - 常见问题
            - 优化建议
            - 优先级排序
        """

        # 1. 收集数据
        agent_tasks = [
            t for t in recent_tasks
            if t["agent"] == agent_name
        ]

        # 2. 分析低质量任务
        low_quality = [
            t for t in agent_tasks
            if t["quality_score"] < 0.6
        ]

        # 3. 使用 LLM 辅助分析
        analysis_prompt = f"""
        请分析以下 Agent 的任务执行情况：

        Agent: {agent_name}
        总任务数: {len(agent_tasks)}
        低质量任务数: {len(low_quality)}

        低质量任务详情：
        {self.format_tasks(low_quality)}

        请分析：
        1. 最常见的 3 个问题是什么？
        2. 每个问题出现的频率是多少？
        3. 针对每个问题，应该如何优化 Prompt？
        4. 优化的优先级如何排序？

        以 JSON 格式返回：
        {{
            "common_issues": [
                {{
                    "issue": "问题描述",
                    "frequency": "出现频率",
                    "suggestion": "优化建议",
                    "priority": "high|medium|low"
                }}
            ]
        }}
        """

        analysis = await self.llm.ainvoke(analysis_prompt)

        # 4. 生成人类可读的报告
        report = self.generate_human_report(analysis)

        return report

    def generate_human_report(self, analysis):
        """生成人类可读的报告"""

        report = f"""
# {agent_name} Prompt 优化分析报告

## 概述
- 总任务数: {self.total_tasks}
- 低质量任务: {self.low_quality_count}
- 平均质量分: {self.avg_quality:.2f}

## 常见问题

"""

        for idx, issue in enumerate(analysis["common_issues"], 1):
            report += f"""
### {idx}. {issue['issue']}

- **出现频率**: {issue['frequency']}
- **优先级**: {issue['priority']}
- **优化建议**: {issue['suggestion']}

"""

        return report


# 使用示例
analyzer = PromptAnalyzer()

# 运行一段时间后
report = await analyzer.analyze_agent_performance(
    "ContentMaterialAgent",
    recent_tasks=task_history
)

print(report)

# 根据报告手动优化 Prompt
# 开发者阅读报告，理解问题，手动修改 Prompt
```

#### 优势
- ✅ 成本低（只是分析工具）
- ✅ 人工控制（避免盲目优化）
- ✅ 立即可用（不需要大量数据）

#### 劣势
- ❌ 不是自动化的
- ❌ 依赖人工判断

---

### 路径 2: 渐进式优化（平衡方案）

#### 概念
基于持续反馈，小步快跑，每次只做一个小改进。

#### 实现方案

```python
class IncrementalPromptOptimizer:
    """渐进式 Prompt 优化器"""

    def __init__(self):
        self.feedback_buffer = []
        self.optimization_history = {}

    async def collect_feedback(
        self,
        agent_name: str,
        task_id: str,
        reflection: dict
    ):
        """
        收集反思反馈

        反思结果包含：
        - quality_score
        - issues
        - suggestions
        """

        feedback = {
            "agent_name": agent_name,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "reflection": reflection
        }

        self.feedback_buffer.append(feedback)

        # 每收集 20 个反馈，触发一次优化分析
        if len(self.feedback_buffer) >= 20:
            await self.analyze_and_optimize(agent_name)

    async def analyze_and_optimize(self, agent_name: str):
        """
        分析反馈并决定是否优化
        """

        # 1. 分析最近的反馈
        recent_feedback = self.feedback_buffer[-20:]

        # 2. 统计问题频率
        issue_frequency = self.count_issues(recent_feedback)

        # 3. 判断是否需要优化
        negative_ratio = self.calculate_negative_ratio(recent_feedback)

        if negative_ratio < 0.3:
            # 表现良好，不需要优化
            logger.info(f"[PromptOptimizer] {agent_name} 表现良好，无需优化")
            return

        # 4. 找出最严重的问题
        worst_issue = max(issue_frequency.items(), key=lambda x: x[1])

        # 5. 生成小改进
        improvement = await self.generate_small_improvement(
            agent_name,
            worst_issue[0],
            worst_issue[1]
        )

        # 6. 记录优化建议（供人工审核）
        self.optimization_history[agent_name] = {
            "timestamp": datetime.now().isoformat(),
            "trigger_issue": worst_issue[0],
            "frequency": worst_issue[1],
            "current_prompt": self.get_current_prompt(agent_name),
            "suggested_improvement": improvement,
            "status": "pending_review"
        }

        logger.info(
            f"[PromptOptimizer] {agent_name} 优化建议已生成，"
            f"待人工审核"
        )

    def count_issues(self, feedback_list):
        """统计问题频率"""

        issue_counts = {}

        for feedback in feedback_list:
            issues = feedback["reflection"].get("issues", [])

            for issue in issues:
                # 归类问题（例如："内容太短"归为一类）
                issue_category = self.categorize_issue(issue)

                issue_counts[issue_category] = \
                    issue_counts.get(issue_category, 0) + 1

        return issue_counts

    def categorize_issue(self, issue):
        """将具体问题归类"""

        issue_text = issue.lower()

        if "短" in issue_text or "不够" in issue_text:
            return "content_too_short"
        elif "偏离" in issue_text or "无关" in issue_text:
            return "content_irrelevant"
        elif "结构" in issue_text or "逻辑" in issue_text:
            return "lacks_structure"
        elif "图表" in issue_text or "数据" in issue_text:
            return "missing_chart_data"
        else:
            return "other"

    async def generate_small_improvement(
        self,
        agent_name: str,
        issue_category: str,
        frequency: int
    ):
        """
        生成小改进建议

        原则：最小化修改，最大化效果
        """

        current_prompt = self.get_current_prompt(agent_name)

        # 预定义的常见问题改进模板
        improvement_templates = {
            "content_too_short": """
---
**改进建议**：在 Prompt 中强调字数要求

**添加内容**：
```
注意：请确保生成的每页内容达到要求的字数，
不要过于简略。如果预估字数是 200 字，
那么实际生成应该在 180-250 字之间。
```
""",

            "content_irrelevant": """
---
**改进建议**：在 Prompt 中强调相关性

**添加内容**：
```
注意：请确保内容与页面主题高度相关。
避免：
- 与页面主题无关的背景信息
- 过于宽泛的描述
- 偏离核心观点

请直接围绕页面标题和核心内容展开。
```
""",

            "lacks_structure": """
---
**改进建议**：在 Prompt 中强调结构

**添加内容**：
```
注意：请使用清晰的结构组织内容。
推荐格式：
- 要点 1：[具体描述]
- 要点 2：[具体描述]
- 要点 3：[具体描述]

或使用类似的其他层次结构。
```
"""
        }

        # 如果有预定义的模板，直接使用
        if issue_category in improvement_templates:
            return {
                "type": "predefined",
                "issue_category": issue_category,
                "frequency": frequency,
                "improvement": improvement_templates[issue_category]
            }

        # 否则，让 LLM 生成建议
        custom_prompt = f"""
当前的 Prompt 是：
{current_prompt}

最近的任务反馈显示，最常见的问题是：
{issue_category}
出现频率：{frequency} 次 / 20 个任务

请生成一个最小化的 Prompt 修改来解决这个问题。

要求：
1. 保持原有 Prompt 的核心逻辑不变
2. 只添加或修改必要的部分
3. 修改要具体、可执行
4. 以 diff 格式输出（旧内容 → 新内容）

不要解释，直接输出改进建议。
"""

        return {
            "type": "custom",
            "issue_category": issue_category,
            "frequency": frequency,
            "improvement": await self.llm.ainvoke(custom_prompt)
        }

    async def apply_optimization(
        self,
        agent_name: str,
        optimization: dict,
        require_approval: bool = True
    ):
        """
        应用优化

        Args:
            agent_name: Agent 名称
            optimization: 优化建议
            require_approval: 是否需要人工审核
        """

        if require_approval:
            # 等待人工审核
            logger.warning(
                f"[PromptOptimizer] {agent_name} 优化需要人工审核，"
                f"未应用"
            )
            return

        # 应用优化
        current_prompt = self.get_current_prompt(agent_name)
        improved_prompt = self.apply_improvement(
            current_prompt,
            optimization["improvement"]
        )

        # 保存新版本
        self.save_prompt_version(
            agent_name,
            current_prompt,
            improved_prompt,
            optimization
        )

        # 更新 Agent 的 Prompt
        self.update_agent_prompt(agent_name, improved_prompt)

        logger.info(f"[PromptOptimizer] {agent_name} Prompt 已优化")

    def apply_improvement(self, current_prompt, improvement):
        """应用改进建议"""

        if improvement["type"] == "predefined":
            # 预定义的改进：直接追加
            return current_prompt + "\n\n" + improvement["improvement"]

        elif improvement["type"] == "custom":
            # 自定义改进：解析 diff 并应用
            return self.apply_diff(current_prompt, improvement["improvement"])
```

#### 优势
- ✅ 数据驱动
- ✅ 小步快跑，风险低
- ✅ 持续改进
- ✅ 可以自动化（部分）

#### 劣势
- ❌ 需要持续收集反馈
- ❌ 优化效果有限（每次小改进）

---

### 路径 3: A/B 测试优化（数据驱动）

#### 概念
同时测试多个 Prompt 变体，用数据决定哪个最好。

#### 实现方案

```python
class PromptABTester:
    """Prompt A/B 测试工具"""

    def __init__(self):
        self.test_results = {}
        self.prompt_variants = {}

    def register_prompt_variant(
        self,
        agent_name: str,
        variant_name: str,
        prompt: str
    ):
        """注册一个 Prompt 变体"""

        if agent_name not in self.prompt_variants:
            self.prompt_variants[agent_name] = {}

        self.prompt_variants[agent_name][variant_name] = {
            "prompt": prompt,
            "created_at": datetime.now().isoformat()
        }

    async def run_ab_test(
        self,
        agent_name: str,
        test_cases: list,
        metrics: list = ["quality", "speed", "cost"]
    ):
        """
        运行 A/B 测试

        Args:
            agent_name: 要测试的 Agent
            test_cases: 测试用例列表
            metrics: 评估指标

        Returns:
            测试结果报告
        """

        variants = self.prompt_variants.get(agent_name, {})

        if len(variants) < 2:
            raise ValueError("至少需要 2 个 Prompt 变体才能进行 A/B 测试")

        results = {}

        # 测试每个变体
        for variant_name, variant_info in variants.items():
            logger.info(
                f"[ABTest] Testing {agent_name} variant: {variant_name}"
            )

            variant_results = []

            # 在测试用例上运行
            for test_case in test_cases:
                # 使用当前变体的 Prompt
                original_prompt = self.get_agent_prompt(agent_name)
                self.set_agent_prompt(agent_name, variant_info["prompt"])

                # 运行任务
                start_time = time.time()
                result = await self.run_agent(agent_name, test_case)
                duration = time.time() - start_time

                # 评估结果
                evaluation = await self.evaluate_result(
                    result,
                    metrics,
                    test_case
                )

                variant_results.append({
                    "test_case_id": test_case["id"],
                    "duration": duration,
                    **evaluation
                })

                # 恢复原 Prompt
                self.set_agent_prompt(agent_name, original_prompt)

            # 计算该变体的平均表现
            results[variant_name] = self.calculate_variant_stats(
                variant_results
            )

        # 生成报告
        report = self.generate_ab_test_report(
            agent_name,
            variants,
            results,
            test_cases,
            metrics
        )

        return report

    async def evaluate_result(
        self,
        result: dict,
        metrics: list,
        test_case: dict
    ):
        """评估单个结果"""

        evaluation = {}

        # 质量评估
        if "quality" in metrics:
            evaluation["quality_score"] = await self.assess_quality(result)

        # 速度已经测量了
        if "speed" in metrics:
            # 将在 calculate_variant_stats 中统计
            pass

        # 成本评估
        if "cost" in metrics:
            evaluation["token_usage"] = result.get("token_usage", 0)

        # 与预期的匹配度
        evaluation["expectation_match"] = self.check_expectation_match(
            result,
            test_case
        )

        return evaluation

    def calculate_variant_stats(self, variant_results):
        """计算变体的统计数据"""

        return {
            "avg_quality": sum(r["quality_score"] for r in variant_results) / len(variant_results),
            "avg_duration": sum(r["duration"] for r in variant_results) / len(variant_results),
            "total_tokens": sum(r.get("token_usage", 0) for r in variant_results),
            "success_rate": sum(1 for r in variant_results if r.get("success", False)) / len(variant_results),
            "sample_count": len(variant_results)
        }

    def generate_ab_test_report(
        self,
        agent_name,
        variants,
        results,
        test_cases,
        metrics
    ):
        """生成 A/B 测试报告"""

        report = f"""
# {agent_name} Prompt A/B 测试报告

## 测试配置
- 测试用例数: {len(test_cases)}
- Prompt 变体数: {len(variants)}
- 评估指标: {', '.join(metrics)}
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 结果对比

"""

        # 找出最好的变体
        best_variant = max(
            results.items(),
            key=lambda x: x[1]["avg_quality"]
        )

        for variant_name, stats in results.items():
            is_best = variant_name == best_variant[0]
            marker = "🏆 " if is_best else ""

            report += f"""
### {marker}{variant_name}

- 平均质量分: {stats['avg_quality']:.3f}
- 平均耗时: {stats['avg_duration']:.2f}s
- Token 使用: {stats['total_tokens']}
- 成功率: {stats['success_rate']:.1%}
- 样本数: {stats['sample_count']}

"""

        # 推荐建议
        report += f"""
## 推荐

根据测试结果，推荐使用：**{best_variant[0]}**

理由：
- 质量得分最高: {best_variant[1]['avg_quality']:.3f}
- 综合表现最优

## 差异分析

"""

        # 分析差异
        baseline = list(results.values())[0]
        for variant_name, stats in results.items():
            if variant_name == list(results.keys())[0]:
                continue

            quality_diff = stats["avg_quality"] - baseline["avg_quality"]
            speed_diff = stats["avg_duration"] - baseline["avg_duration"]

            report += f"""
{variant_name} vs 基线:
- 质量: {"+" if quality_diff > 0 else ""}{quality_diff:.3f}
- 速度: {"+" if speed_diff > 0 else ""}{speed_diff:.2f}s

"""

        return report
```

#### 使用示例

```python
# 1. 定义 Prompt 变体
tester = PromptABTester()

tester.register_prompt_variant(
    "ContentMaterialAgent",
    "baseline",
    current_prompt
)

tester.register_prompt_variant(
    "ContentMaterialAgent",
    "emphasize_length",
    current_prompt + "\n\n注意：确保内容达到要求字数。"
)

tester.register_prompt_variant(
    "ContentMaterialAgent",
    "add_examples",
    current_prompt + "\n\n示例：\n好的页面内容应该包含3-5个要点，每个要点有具体阐述。"
)

# 2. 运行 A/B 测试
test_cases = select_test_cases(num=10)  # 选择 10 个测试用例
report = await tester.run_ab_test("ContentMaterialAgent", test_cases)

print(report)

# 3. 根据报告选择最好的 Prompt
```

#### 优势
- ✅ 数据驱动决策
- ✅ 有实际验证
- ✅ 可信度高

#### 劣势
- ❌ 成本高（需要运行大量测试）
- ❌ 耗时
- ❌ 测试用例选择可能偏差

---

### 路径 4: LLM 驱动的自动优化（最复杂）

#### 概念
使用 LLM 分析历史数据，自动生成优化的 Prompt。

#### 实现方案

```python
class LLMDrivenPromptOptimizer:
    """LLM 驱动的 Prompt 优化器"""

    def __init__(self):
        self.optimization_iterations = 3  # 最多优化 3 轮

    async def optimize_prompt(
        self,
        agent_name: str,
        current_prompt: str,
        history_data: list
    ):
        """
        使用 LLM 自动优化 Prompt

        Args:
            agent_name: Agent 名称
            current_prompt: 当前 Prompt
            history_data: 历史任务数据

        Returns:
            优化后的 Prompt
        """

        logger.info(
            f"[LLMOptimizer] 开始优化 {agent_name} 的 Prompt，"
            f"基于 {len(history_data)} 个历史任务"
        )

        optimized_prompt = current_prompt

        # 多轮优化
        for iteration in range(1, self.optimization_iterations + 1):
            logger.info(
                f"[LLMOptimizer] 第 {iteration} 轮优化"
            )

            # 分析当前 Prompt 的问题
            analysis = await self.analyze_prompt_problems(
                optimized_prompt,
                history_data
            )

            # 如果没有明显问题，停止优化
            if not analysis["has_problems"]:
                logger.info(
                    f"[LLMOptimizer] 第 {iteration} 轮未发现问题，"
                    f"停止优化"
                )
                break

            # 生成优化版本
            new_prompt = await self.generate_optimized_prompt(
                optimized_prompt,
                analysis
            )

            # 验证新 Prompt（在部分数据上测试）
            validation = await self.validate_prompt_improvement(
                optimized_prompt,
                new_prompt,
                history_data[:10]  # 在前 10 个样本上测试
            )

            if validation["improvement"] > 0.05:  # 改进超过 5%
                optimized_prompt = new_prompt
                logger.info(
                    f"[LLMOptimizer] 第 {iteration} 轮优化有效，"
                    f"改进: {validation['improvement']:.1%}"
                )
            else:
                logger.info(
                    f"[LLMOptimizer] 第 {iteration} 轮优化无效，"
                    f"停止优化"
                )
                break

        return optimized_prompt

    async def analyze_prompt_problems(
        self,
        prompt: str,
        history_data: list
    ):
        """
        分析 Prompt 的问题

        基于:
        1. 低质量任务的共同特征
        2. 失败案例
        3. 反思反馈
        """

        low_quality_tasks = [
            t for t in history_data
            if t.get("quality_score", 0) < 0.6
        ]

        analysis_prompt = f"""
        请分析以下 Prompt 在实际使用中存在的问题：

        Prompt:
        {prompt}

        低质量任务案例（{len(low_quality_tasks)} 个）:
        {self.format_task_samples(low_quality_tasks, max_samples=5)}

        请分析：
        1. Prompt 缺少什么关键指令？
        2. 哪些要求不够明确？
        3. 常见的误解是什么？
        4. 什么改进能带来最大提升？

        以 JSON 格式返回：
        {{
            "has_problems": true/false,
            "critical_issues": [
                {{
                    "issue": "问题描述",
                    "impact": "影响程度 (high/medium/low)",
                    "suggestion": "改进建议"
                }}
            ],
            "reasoning": "分析理由"
        }}
        """

        response = await self.llm.with_structured_output(
            PromptAnalysis
        ).ainvoke(analysis_prompt)

        return response.dict()

    async def generate_optimized_prompt(
        self,
        current_prompt: str,
        analysis: dict
    ):
        """生成优化后的 Prompt"""

        optimization_prompt = f"""
        请优化以下 Prompt：

        当前 Prompt：
        {current_prompt}

        发现的问题：
        {self.format_analysis(analysis)}

        优化要求：
        1. 解决所有关键问题
        2. 保持原有 Prompt 的核心逻辑
        3. 添加必要的明确指令
        4. 消除可能的误解
        5. 使 Prompt 更清晰、更具体

        只输出优化后的 Prompt，不要解释。
        """

        return await self.llm.ainvoke(optimization_prompt)

    async def validate_prompt_improvement(
        self,
        old_prompt: str,
        new_prompt: str,
        validation_samples: list
    ):
        """
        验证 Prompt 改进效果

        在样本数据上对比两个 Prompt
        """

        old_scores = []
        new_scores = []

        for sample in validation_samples:
            # 使用旧 Prompt
            old_result = await self.run_with_prompt(old_prompt, sample)
            old_score = await self.quick_assess(old_result)
            old_scores.append(old_score)

            # 使用新 Prompt
            new_result = await self.run_with_prompt(new_prompt, sample)
            new_score = await self.quick_assess(new_result)
            new_scores.append(new_score)

        old_avg = sum(old_scores) / len(old_scores)
        new_avg = sum(new_scores) / len(new_scores)

        return {
            "old_avg_quality": old_avg,
            "new_avg_quality": new_avg,
            "improvement": (new_avg - old_avg) / old_avg if old_avg > 0 else 0
        }
```

#### 优势
- ✅ 理论上全自动
- ✅ 可以发现人类忽略的问题

#### 劣势
- ❌ 成本非常高（多次 LLM 调用）
- ❌ 优化方向可能不可靠
- ❌ 难以验证效果
- ❌ 可能"越优化越差"

---

## 四、推荐的实施路线图

### 阶段 1: 数据收集（第 1-2 周）

```python
# 实施基础监控

class MonitoringSystem:
    """基础监控系统"""

    async def record_task_execution(
        self,
        task_id: str,
        agent_name: str,
        prompt_used: str,
        result: dict,
        quality_score: float
    ):
        """记录每次任务执行"""

        record = {
            "task_id": task_id,
            "agent_name": agent_name,
            "prompt_used": prompt_used,
            "result": result,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat(),
            "token_usage": result.get("token_usage", {})
        }

        # 保存到数据库
        await self.db.save(record)
```

**目标**: 收集 20-30 个任务样本

---

### 阶段 2: 人工分析优化（第 3-4 周）

```python
# 使用 PromptAnalyzer 工具

analyzer = PromptAnalyzer()
report = await analyzer.analyze_agent_performance(
    "ContentMaterialAgent",
    recent_tasks
)

# 根据报告，手动优化 Prompt
```

**目标**: 完成 1-2 轮人工优化

---

### 阶段 3: 渐进式优化（第 2-3 个月）

```python
# 实施 IncrementalPromptOptimizer

optimizer = IncrementalPromptOptimizer()

# 持续收集反馈
await optimizer.collect_feedback(
    "ContentMaterialAgent",
    task_id,
    reflection
)

# 自动生成优化建议（人工审核）
```

**目标**: 建立持续改进机制

---

### 阶段 4: A/B 测试验证（第 3-4 个月）

```python
# 实施 PromptABTester

tester = PromptABTester()
report = await tester.run_ab_test(
    "ContentMaterialAgent",
    test_cases
)
```

**目标**: 数据驱动的 Prompt 选择

---

## 五、成本效益分析

### 成本估算

| 项目 | 成本 | 说明 |
|------|------|------|
| **监控数据收集** | 低 | 已有日志系统，只需结构化 |
| **人工分析工具** | 低 | 开发 3-5 天，LLM 调用成本低 |
| **渐进式优化** | 中 | 持续运行，定期 LLM 调用 |
| **A/B 测试** | 高 | 需要运行大量测试任务 |
| **LLM 自动优化** | 很高 | 多轮 LLM 调用 + 验证 |

### 收益估算

| 方法 | 提升幅度 | 置信度 | 说明 |
|------|---------|--------|------|
| **人工优化** | +15-25% | ⭐⭐⭐⭐ | 经验驱动，效果明显 |
| **渐进式优化** | +10-20% | ⭐⭐⭐ | 持续改进，累积效果 |
| **A/B 测试优化** | +20-30% | ⭐⭐⭐⭐⭐ | 数据驱动，最可靠 |
| **LLM 自动优化** | +5-15% | ⭐⭐ | 效果不稳定 |

### ROI 分析

```
方案 1: 人工优化
  开发成本: 3-5 天
  运行成本: 每月 1-2 次 LLM 调用
  收益: +20% 质量
  ROI: 非常高 ⭐⭐⭐⭐⭐

方案 2: 渐进式优化
  开发成本: 1-2 周
  运行成本: 每周若干 LLM 调用
  收益: +15% 质量（累积）
  ROI: 高 ⭐⭐⭐⭐

方案 3: A/B 测试
  开发成本: 2-3 周
  运行成本: 每月 10+ 个测试任务
  收益: +25% 质量
  ROI: 中等 ⭐⭐⭐

方案 4: LLM 自动优化
  开发成本: 1-2 月
  运行成本: 频繁 LLM 调用
  收益: +10% 质量（不稳定）
  ROI: 低 ⭐⭐
```

---

## 六、决策指南

### 什么时候应该实施 Prompt 优化？

```
✅ 应该实施的情况：
  - 已有 30+ 个任务样本
  - 有明确的质量评分
  - 发现明显的性能问题
  - 有专门的人力投入

❌ 不建议实施的情况：
  - 样本数据太少（< 20 个）
  - 质量评分体系不完善
  - 当前 Prompt 表现良好
  - 资源有限（应优先其他优化）
```

### 选择哪种方法？

```
数据量 < 30:
  → 人工优化（手动）

数据量 30-100:
  → 渐进式优化

数据量 100+:
  → A/B 测试优化

数据量 500+:
  → 考虑 LLM 自动优化
```

---

## 七、与反思机制的关系

### 协同效应

```
反思机制（提升点1）:
  → 每个 Agent 自我检查
  → 发现问题立即改进
  → 收集反思数据

         ↓ 收集数据

Prompt 优化系统（提升点2）:
  → 分析反思数据
  → 识别常见问题
  → 优化 Prompt
  → 预防问题发生
```

### 实施顺序

```
第 1 步: 实施反思机制
  └─ 立即见效，收集数据

第 2 步: 分析反思数据
  └─ 识别 Prompt 问题

第 3 步: 手动优化 Prompt
  └─ 快速改进

第 4 步: 建立自动化优化
  └─ 持续改进
```

---

## 八、成功案例（假设）

### 案例 1: ContentAgent Prompt 优化

**初始 Prompt**:
```
"请为这个页面生成内容"
```

**问题分析**:
- 40% 的任务内容过短
- 30% 的任务偏离主题
- 20% 的任务结构混乱

**优化后 Prompt**:
```
"请为这个页面生成内容，要求：

1. 内容要求：
   - 紧密围绕页面主题
   - 使用清晰的要点结构
   - 确保达到预估字数要求

2. 输出格式：
   - content_text: 主要内容
   - key_points: 3-5 个要点
   - 如需图表：提供 chart_data
   - 如需配图：提供 image_suggestion

3. 质量标准：
   - 内容简洁专业
   - 逻辑清晰连贯
   - 符合页面类型要求"
```

**效果**:
- 内容过短：40% → 10%
- 偏离主题：30% → 5%
- 结构混乱：20% → 5%
- **整体质量提升：+30%**

---

### 案例 2: FrameworkAgent Prompt 优化

**初始 Prompt**:
```
"设计一个 {page_num} 页的 PPT 框架"
```

**问题分析**:
- 研究标记不准确
- 页面类型单调
- 图表分布不均

**优化后 Prompt**:
```
"设计一个 {page_num} 页的 PPT 框架，要求：

1. 结构规则：
   - 第 1 页必须是封面（cover）
   - 第 2 页通常是目录（directory）
   - 最后一页是总结（summary）

2. 类型多样性：
   - 确保包含至少 3 种不同的页面类型
   - 图表页应均匀分布（间隔 3-5 页）

3. 研究标记：
   - 需要外部数据的页面标记 is_need_research=true
   - 提供具体的研究关键词

4. 输出格式：
   - 严格按照 JSON 格式输出
   - 包含所有必需字段"
```

**效果**:
- 框架合理性：+25%
- 研究准确性：+40%
- 整体质量提升：+20%

---

## 九、总结

### 核心要点

1. **Prompt 优化有价值** - 但实施难度高
2. **数据是基础** - 需要充足的历史数据
3. **人工优先** - 前期手动优化更有效
4. **渐进改进** - 小步快跑比一次性优化更可靠
5. **验证重要** - A/B 测试是最可靠的方法

### 实施建议

| 时间 | 行动 |
|------|------|
| **现在** | 完善监控，收集数据 |
| **1-2 周后** | 人工分析，手动优化 |
| **1-2 月后** | 实施渐进式优化 |
| **3-6 月后** | 考虑 A/B 测试 |

### 优先级排序

```
🔥 立即做（提升点1）:
  └─ Agent 反思机制

🔥 紧接着做（新增）:
  └─ 监控和数据收集

🟡 1-2 月后:
  └─ Prompt 优化系统（人工 + 渐进式）

🟢 长期考虑:
  └─ A/B 测试
```

---

**文档版本**: v1.0
**创建日期**: 2026-02-09
**作者**: Claude (Sonnet 4.5)

**下一步**: 参考《提升点 1: Agent 反思机制》
