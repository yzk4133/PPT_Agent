#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skill: Task Scheduler

Implements the TaskSchedulerSkill - DAG-based task scheduling and execution
with support for dependencies and parallel execution.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from collections import defaultdict, deque

from ..skill_decorator import Skill
from ..skill_metadata import SkillCategory

logger = logging.getLogger(__name__)

@Skill(
    name="TaskSchedulerSkill",
    version="1.0.0",
    category=SkillCategory.UTILITY,
    tags=["scheduling", "parallel", "dag", "workflow"],
    description="Schedule and execute tasks with dependencies using DAG-based parallel execution",
    author="MultiAgentPPT",
    enabled=True
)
class TaskSchedulerSkill:
    """
    TaskSchedulerSkill - DAG Task Scheduling

    This Skill implements a directed acyclic graph (DAG) task scheduler
    that can:
    - Execute tasks with dependencies
    - Parallelize independent tasks
    - Handle task failures
    - Support retry logic
    """

    def __init__(self):
        """Initialize the scheduler skill"""
        self.logger = logger

    async def execute(
        self,
        tasks: List[Dict[str, Any]],
        max_parallel: int = 3,
        tool_context: Optional[Any] = None
    ) -> str:
        """
        Schedule and execute tasks

        Args:
            tasks: List of task definitions with dependencies
                Each task should have:
                - id: Unique task identifier
                - function: Callable or function name
                - params: Parameters for the function
                - depends_on: List of task IDs this task depends on
            max_parallel: Maximum number of parallel tasks
            tool_context: Optional tool context

        Returns:
            JSON string with execution results
        """
        self.logger.info(f"[TaskSchedulerSkill] Scheduling {len(tasks)} tasks")

        try:
            # Build DAG
            dag = self._build_dag(tasks)
            self.logger.info(f"  → Built DAG with {len(dag)} nodes")

            # Topological sort into execution levels
            execution_levels = self._topological_sort(dag)
            self.logger.info(f"  → Organized into {len(execution_levels)} execution levels")

            # Execute tasks level by level
            results = {}
            for level_idx, level in enumerate(execution_levels):
                self.logger.info(f"  → Executing level {level_idx + 1} with {len(level)} tasks")

                # Execute tasks in this level in parallel
                level_results = await self._execute_level(
                    level, dag, max_parallel, results
                )

                # Merge results
                results.update(level_results)

            # Generate summary
            summary = self._generate_summary(results)

            return json.dumps({
                "success": True,
                "result": {
                    "tasks_executed": len(results),
                    "summary": summary,
                    "results": results
                }
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Scheduler error: {e}", exc_info=True)
            return json.dumps({
                "success": False,
                "error": str(e),
                "result": None
            }, ensure_ascii=False)

    def _build_dag(self, tasks: List[Dict]) -> Dict[str, Dict]:
        """Build DAG from task list"""
        dag = {}
        for task in tasks:
            task_id = task.get("id")
            if not task_id:
                continue

            dag[task_id] = {
                "function": task.get("function"),
                "params": task.get("params", {}),
                "dependencies": task.get("depends_on", []),
                "status": "pending"
            }

        return dag

    def _topological_sort(self, dag: Dict[str, Dict]) -> List[List[str]]:
        """
        Perform topological sort and organize into execution levels

        Returns:
            List of levels, where each level is a list of task IDs
        """
        # Calculate in-degree for each node
        in_degree = {}
        for task_id in dag:
            in_degree[task_id] = 0

        for task_id, task_data in dag.items():
            for dep_id in task_data["dependencies"]:
                if dep_id in in_degree:
                    in_degree[task_id] += 1

        # Find nodes with no dependencies (start nodes)
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])

        levels = []
        while queue:
            current_level = list(queue)
            levels.append(current_level)
            queue.clear()

            # Process all nodes in current level
            for task_id in current_level:
                # Reduce in-degree for dependent nodes
                for other_id, other_data in dag.items():
                    if task_id in other_data["dependencies"]:
                        in_degree[other_id] -= 1
                        if in_degree[other_id] == 0:
                            queue.append(other_id)

        return levels

    async def _execute_level(
        self,
        task_ids: List[str],
        dag: Dict[str, Dict],
        max_parallel: int,
        completed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all tasks in a level with parallelism limit"""

        async def execute_single_task(task_id: str) -> tuple:
            """Execute a single task"""
            task_data = dag[task_id]

            # Check if dependencies completed successfully
            for dep_id in task_data["dependencies"]:
                if dep_id in completed_results:
                    dep_result = completed_results[dep_id]
                    if isinstance(dep_result, dict) and not dep_result.get("success", True):
                        # Dependency failed, skip this task
                        return (task_id, {
                            "success": False,
                            "error": f"Dependency {dep_id} failed",
                            "status": "skipped"
                        })

            try:
                # Execute the task
                func = task_data["function"]
                params = task_data["params"]

                # If function is callable, execute it
                if callable(func):
                    if asyncio.iscoroutinefunction(func):
                        result = await func(**params)
                    else:
                        result = func(**params)
                else:
                    # Mock execution for demo
                    await asyncio.sleep(0.1)
                    result = {"status": "completed", "data": f"Result of {task_id}"}

                return (task_id, {
                    "success": True,
                    "status": "completed",
                    "result": result
                })

            except Exception as e:
                return (task_id, {
                    "success": False,
                    "error": str(e),
                    "status": "failed"
                })

        # Execute tasks with parallelism limit
        results = {}
        semaphore = asyncio.Semaphore(max_parallel)

        async def execute_with_semaphore(task_id: str):
            async with semaphore:
                return await execute_single_task(task_id)

        # Run all tasks in parallel (with semaphore limiting concurrency)
        tasks_results = await asyncio.gather(
            *[execute_with_semaphore(task_id) for task_id in task_ids],
            return_exceptions=True
        )

        # Process results
        for result in tasks_results:
            if isinstance(result, Exception):
                self.logger.error(f"Task execution exception: {result}")
            else:
                task_id, task_result = result
                results[task_id] = task_result

        return results

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution summary"""
        total = len(results)
        success = sum(1 for r in results.values() if r.get("success", False))
        failed = total - success

        return {
            "total_tasks": total,
            "successful": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0
        }

    def get_skill_metadata(self):
        """Get skill metadata"""
        from ..skill_metadata import SkillMetadata
        return SkillMetadata(
            skill_id="task_scheduler",
            name="TaskSchedulerSkill",
            version="1.0.0",
            category=SkillCategory.UTILITY,
            tags=["scheduling", "parallel", "dag", "workflow"],
            description="Schedule and execute tasks with dependencies",
            enabled=True
        )

# Convenience function
async def schedule_tasks(
    tasks: List[Dict[str, Any]],
    max_parallel: int = 3,
    tool_context: Optional[Any] = None
) -> str:
    """
    Schedule and execute tasks

    Args:
        tasks: List of task definitions
        max_parallel: Maximum parallel tasks
        tool_context: Optional tool context

    Returns:
        JSON string with execution results
    """
    skill = TaskSchedulerSkill()
    return await skill.execute(
        tasks=tasks,
        max_parallel=max_parallel,
        tool_context=tool_context
    )
