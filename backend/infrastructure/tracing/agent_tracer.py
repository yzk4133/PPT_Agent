"""
Agent Chain Tracing

Provides comprehensive tracing for agent execution chains.
Tracks call hierarchy, performance metrics, inputs/outputs, and errors.
"""

import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from traceback import format_exc


logger = logging.getLogger(__name__)


@dataclass
class Span:
    """
    A single span in the trace.

    Represents one agent execution with timing and metadata.
    """
    span_id: str
    parent_id: Optional[str]
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "agent_name": self.agent_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "inputs": self._serialize_data(self.inputs),
            "outputs": self._serialize_data(self.outputs),
            "error": self.error,
            "error_type": self.error_type,
            "metadata": self.metadata
        }

    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for JSON output"""
        if data is None:
            return None
        try:
            # Try to serialize to JSON
            json.dumps(data)
            return data
        except:
            # If not serializable, convert to string
            return str(data)


@dataclass
class Trace:
    """
    A complete trace of an agent execution chain.

    Contains all spans from root to leaves.
    """
    trace_id: str
    root_span_id: str
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    spans: List[Span] = field(default_factory=list)
    status: str = "running"  # running, completed, failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "root_span_id": self.root_span_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": round(self.total_duration_ms, 2) if self.total_duration_ms else None,
            "status": self.status,
            "span_count": len(self.spans),
            "spans": [s.to_dict() for s in self.spans]
        }

    def add_span(self, span: Span) -> None:
        """Add a span to the trace"""
        self.spans.append(span)

    def complete(self) -> None:
        """Mark the trace as completed"""
        self.end_time = datetime.now()
        self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "completed"

    def fail(self, error: str) -> None:
        """Mark the trace as failed"""
        self.end_time = datetime.now()
        self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "failed"

    def get_span_by_id(self, span_id: str) -> Optional[Span]:
        """Get a span by its ID"""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None

    def get_spans_by_agent(self, agent_name: str) -> List[Span]:
        """Get all spans for a specific agent"""
        return [s for s in self.spans if s.agent_name == agent_name]

    def get_children(self, parent_id: str) -> List[Span]:
        """Get all child spans of a parent"""
        return [s for s in self.spans if s.parent_id == parent_id]

    def get_call_tree(self) -> Dict[str, Any]:
        """
        Build a hierarchical call tree from the spans.

        Returns:
            Nested dictionary representing the call hierarchy
        """
        def build_tree(span_id: str) -> Dict[str, Any]:
            span = self.get_span_by_id(span_id)
            if not span:
                return {}

            children = self.get_children(span_id)
            return {
                "span_id": span.span_id,
                "agent_name": span.agent_name,
                "duration_ms": span.duration_ms,
                "status": "error" if span.error else "success",
                "children": [build_tree(c.span_id) for c in children]
            }

        return build_tree(self.root_span_id)


class AgentTracer:
    """
    Agent execution tracer.

    Provides tracing capabilities for agent execution chains.
    Thread-safe and supports concurrent tracing.
    """

    def __init__(self):
        """Initialize the tracer"""
        self._traces: Dict[str, Trace] = {}
        self._lock = threading.RLock()
        self._current_trace: Optional[str] = None
        self._span_counter = 0
        self._callbacks: List[Callable[[Trace], None]] = []

    def create_trace(
        self,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Trace:
        """
        Create a new trace.

        Args:
            task_id: Optional task ID
            session_id: Optional session ID
            user_id: Optional user ID

        Returns:
            New Trace object
        """
        import uuid

        trace_id = f"trace_{uuid.uuid4().hex[:16]}"
        trace = Trace(
            trace_id=trace_id,
            root_span_id="",  # Will be set when first span is created
            task_id=task_id,
            session_id=session_id,
            user_id=user_id
        )

        with self._lock:
            self._traces[trace_id] = trace
            self._current_trace = trace_id

        logger.debug(f"Created trace: {trace_id}")
        return trace

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Get a trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace object or None
        """
        with self._lock:
            return self._traces.get(trace_id)

    def get_current_trace(self) -> Optional[Trace]:
        """Get the current active trace"""
        with self._lock:
            if self._current_trace:
                return self._traces.get(self._current_trace)
            return None

    def start_span(
        self,
        agent_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> Span:
        """
        Start a new span.

        Args:
            agent_name: Name of the agent
            inputs: Agent input data
            parent_id: Parent span ID (None for root)
            metadata: Optional metadata
            trace_id: Trace ID (uses current if None)

        Returns:
            New Span object
        """
        import uuid

        # Determine which trace to use
        if trace_id:
            trace = self.get_trace(trace_id)
        else:
            trace = self.get_current_trace()

        if not trace:
            logger.warning("No active trace, creating new one")
            trace = self.create_trace()

        # Create span ID
        with self._lock:
            self._span_counter += 1
            span_id = f"span_{self._span_counter}_{uuid.uuid4().hex[:8]}"

        # If this is the first span, make it the root
        if not trace.root_span_id:
            trace.root_span_id = span_id
            parent_id = None

        # Create span
        span = Span(
            span_id=span_id,
            parent_id=parent_id,
            agent_name=agent_name,
            start_time=datetime.now(),
            inputs=inputs,
            metadata=metadata or {}
        )

        # Add to trace
        with self._lock:
            trace.add_span(span)

        logger.debug(f"Started span: {span_id} ({agent_name})")
        return span

    def end_span(
        self,
        span: Span,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        End a span.

        Args:
            span: Span to end
            outputs: Agent output data
            error: Error if any
        """
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.outputs = outputs

        if error:
            span.error = error
            span.error_type = "Exception"

        logger.debug(
            f"Ended span: {span.span_id} ({span.agent_name}) "
            f"in {span.duration_ms:.2f}ms"
        )

    def complete_trace(self, trace_id: Optional[str] = None) -> None:
        """
        Mark a trace as completed.

        Args:
            trace_id: Trace ID (uses current if None)
        """
        if trace_id:
            trace = self.get_trace(trace_id)
        else:
            trace = self.get_current_trace()

        if trace:
            trace.complete()
            self._notify_callbacks(trace)
            logger.debug(f"Completed trace: {trace.trace_id}")

    def fail_trace(self, error: str, trace_id: Optional[str] = None) -> None:
        """
        Mark a trace as failed.

        Args:
            error: Error message
            trace_id: Trace ID (uses current if None)
        """
        if trace_id:
            trace = self.get_trace(trace_id)
        else:
            trace = self.get_current_trace()

        if trace:
            trace.fail(error)
            self._notify_callbacks(trace)
            logger.debug(f"Failed trace: {trace.trace_id} - {error}")

    def export_trace(self, trace_id: str, format: str = "json") -> str:
        """
        Export a trace to a string.

        Args:
            trace_id: Trace ID
            format: Export format (json, csv)

        Returns:
            Exported string
        """
        trace = self.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace not found: {trace_id}")

        if format == "json":
            return json.dumps(trace.to_dict(), indent=2, ensure_ascii=False)
        elif format == "csv":
            return self._export_csv(trace)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_csv(self, trace: Trace) -> str:
        """Export trace as CSV"""
        import io
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "span_id", "parent_id", "agent_name", "start_time",
            "duration_ms", "status", "error"
        ])

        # Rows
        for span in trace.spans:
            writer.writerow([
                span.span_id,
                span.parent_id or "",
                span.agent_name,
                span.start_time.isoformat(),
                span.duration_ms or "",
                "error" if span.error else "success",
                span.error or ""
            ])

        return output.getvalue()

    def register_callback(self, callback: Callable[[Trace], None]) -> None:
        """
        Register a callback to be called when a trace completes.

        Args:
            callback: Function to call with the completed trace
        """
        self._callbacks.append(callback)

    def _notify_callbacks(self, trace: Trace) -> None:
        """Notify all registered callbacks"""
        for callback in self._callbacks:
            try:
                callback(trace)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_statistics(self, trace_id: str) -> Dict[str, Any]:
        """
        Get statistics for a trace.

        Args:
            trace_id: Trace ID

        Returns:
            Statistics dictionary
        """
        trace = self.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace not found: {trace_id}")

        spans_by_agent = {}
        total_agent_time = {}

        for span in trace.spans:
            # Count by agent
            if span.agent_name not in spans_by_agent:
                spans_by_agent[span.agent_name] = 0
            spans_by_agent[span.agent_name] += 1

            # Total time by agent
            if span.agent_name not in total_agent_time:
                total_agent_time[span.agent_name] = 0
            if span.duration_ms:
                total_agent_time[span.agent_name] += span.duration_ms

        # Find slowest spans
        slowest_spans = sorted(
            [s for s in trace.spans if s.duration_ms],
            key=lambda s: s.duration_ms,
            reverse=True
        )[:5]

        # Count errors
        error_count = sum(1 for s in trace.spans if s.error)

        return {
            "trace_id": trace_id,
            "total_spans": len(trace.spans),
            "total_duration_ms": trace.total_duration_ms,
            "spans_by_agent": spans_by_agent,
            "total_agent_time_ms": total_agent_time,
            "slowest_spans": [
                {"agent": s.agent_name, "duration_ms": s.duration_ms}
                for s in slowest_spans
            ],
            "error_count": error_count,
            "success_rate": round((1 - error_count / len(trace.spans)) * 100, 2) if trace.spans else 100
        }

    def clear_traces(self) -> None:
        """Clear all traces"""
        with self._lock:
            self._traces.clear()
            self._current_trace = None
            self._span_counter = 0

    def list_traces(self) -> List[str]:
        """List all trace IDs"""
        with self._lock:
            return list(self._traces.keys())


# Context manager for automatic span management
@contextmanager
def trace_span(
    tracer: AgentTracer,
    agent_name: str,
    inputs: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager for automatic span tracing.

    Example:
        with trace_span(tracer, "MyAgent", {"input": data}) as span:
            result = await my_agent_function(data)
            span.outputs = {"result": result}
    """
    span = tracer.start_span(agent_name, inputs=inputs, metadata=metadata)
    try:
        yield span
        tracer.end_span(span, outputs=span.outputs)
    except Exception as e:
        error_str = f"{type(e).__name__}: {str(e)}"
        tracer.end_span(span, error=error_str)
        raise


# Global tracer instance
_global_tracer: Optional[AgentTracer] = None
_tracer_lock = threading.Lock()


def get_tracer() -> AgentTracer:
    """Get the global agent tracer instance"""
    global _global_tracer
    with _tracer_lock:
        if _global_tracer is None:
            _global_tracer = AgentTracer()
        return _global_tracer


def reset_tracer() -> AgentTracer:
    """Reset the global tracer with a new instance"""
    global _global_tracer
    with _tracer_lock:
        _global_tracer = AgentTracer()
        return _global_tracer


if __name__ == "__main__":
    # Test the tracer
    logging.basicConfig(level=logging.DEBUG)

    tracer = AgentTracer()

    # Create a trace
    trace = tracer.create_trace(
        task_id="task_001",
        session_id="session_001",
        user_id="user_001"
    )

    # Simulate agent execution
    with trace_span(tracer, "RequirementParser", {"input": "Make a PPT about AI"}) as span1:
        time.sleep(0.1)
        span1.outputs = {"result": "parsed"}

        # Nested agent call
        with trace_span(tracer, "FrameworkDesigner", {"pages": 10}) as span2:
            time.sleep(0.05)
            span2.outputs = {"framework": "designed"}

    with trace_span(tracer, "ResearchAgent", {"topic": "AI trends"}) as span3:
        time.sleep(0.15)
        span3.outputs = {"data": "researched"}

    # Complete trace
    tracer.complete_trace()

    # Print results
    print("\n=== Trace Summary ===")
    print(json.dumps(trace.to_dict(), indent=2, ensure_ascii=False))

    print("\n=== Statistics ===")
    stats = tracer.get_statistics(trace.trace_id)
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    print("\n=== Call Tree ===")
    tree = trace.get_call_tree()
    print(json.dumps(tree, indent=2, ensure_ascii=False))

    print("\n=== Export JSON ===")
    exported = tracer.export_trace(trace.trace_id, format="json")
    print(exported[:500] + "...")
