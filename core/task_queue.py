"""
Async Task Queue for Auto Makah.

Queue tasks, process them in parallel with a configurable concurrency cap,
and inspect queue stats — all with ``asyncio`` under the hood.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    """A queued unit of work."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None

    # ── internals (not serialized) ───────────────────────────────────
    _coro: Callable[..., Coroutine[Any, Any, Any]] | None = field(default=None, repr=False)
    _args: tuple[Any, ...] = field(default_factory=tuple, repr=False)
    _kwargs: Dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


class TaskQueue:
    """
    Asynchronous bounded-parallel task queue.

    Usage::

        q = TaskQueue(max_concurrency=5)

        # enqueue coroutine functions (not already-awaited coroutines)
        q.enqueue("fetch-data", fetch_some_api, "https://api.example.com")
        q.enqueue("send-email", send_mail, to="user@example.com")

        # process everything
        results = await q.process_all()

        # inspect
        print(q.status())
    """

    def __init__(self, max_concurrency: int = 5) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        self._max_concurrency = max_concurrency
        self._queue: List[Task] = []
        self._semaphore = asyncio.Semaphore(max_concurrency)

    # ── public API ───────────────────────────────────────────────────

    def enqueue(
        self,
        task_name: str,
        task_fn: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Task:
        """
        Add a task to the queue.

        Args:
            task_name: Human-readable label.
            task_fn: Async callable **(not a coroutine object)**.
            *args: Positional arguments forwarded to *task_fn*.
            **kwargs: Keyword arguments forwarded to *task_fn*.

        Returns:
            The ``Task`` record (status = ``PENDING``).
        """
        task = Task(name=task_name)
        task._coro = task_fn
        task._args = args
        task._kwargs = kwargs
        self._queue.append(task)
        return task

    async def process_all(self) -> List[Task]:
        """
        Run every queued task in parallel, capped at *max_concurrency*.

        Already-processed tasks are skipped; only ``PENDING`` tasks are
        scheduled.

        Returns:
            All tasks with their final statuses.
        """
        pending = [t for t in self._queue if t.status == TaskStatus.PENDING]
        if not pending:
            return self._queue

        async def _run(task: Task) -> None:
            async with self._semaphore:
                task.status = TaskStatus.RUNNING
                try:
                    coro = task._coro(*task._args, **task._kwargs)  # type: ignore[misc]
                    task.result = await coro
                    task.status = TaskStatus.DONE
                except Exception as exc:
                    task.error = f"{type(exc).__name__}: {exc}"
                    task.status = TaskStatus.FAILED

        await asyncio.gather(*(_run(t) for t in pending), return_exceptions=True)
        return self._queue

    async def process_one(self, task_id: str) -> Optional[Task]:
        """Run a single task by id. Returns ``None`` if not found."""
        task = self._find(task_id)
        if task is None or task.status != TaskStatus.PENDING:
            return task

        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            try:
                coro = task._coro(*task._args, **task._kwargs)  # type: ignore[misc]
                task.result = await coro
                task.status = TaskStatus.DONE
            except Exception as exc:
                task.error = f"{type(exc).__name__}: {exc}"
                task.status = TaskStatus.FAILED

        return task

    def status(self) -> Dict[str, Any]:
        """Return a snapshot of queue statistics."""
        counts: Dict[str, int] = defaultdict(int)
        for t in self._queue:
            counts[t.status.value] += 1

        return {
            "total": len(self._queue),
            "pending": counts.get("pending", 0),
            "running": counts.get("running", 0),
            "done": counts.get("done", 0),
            "failed": counts.get("failed", 0),
            "max_concurrency": self._max_concurrency,
            "tasks": [t.to_dict() for t in self._queue],
        }

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by id, or ``None``."""
        return self._find(task_id)

    def clear(self) -> None:
        """Remove all tasks from the queue."""
        self._queue.clear()

    # ── internal ─────────────────────────────────────────────────────

    def _find(self, task_id: str) -> Optional[Task]:
        for t in self._queue:
            if t.id == task_id:
                return t
        return None
