from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class WorkDomain(str, Enum):
    BUSINESS = "business"
    RESEARCH = "research"
    OPERATIONS = "operations"
    DESIGN = "design"
    CONTENT = "content"
    ENGINEERING = "engineering"
    QA = "qa"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    QA_REVIEW = "qa_review"
    REVISION = "revision"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class SquadSeat:
    seat_id: str
    title: str
    domains: tuple[WorkDomain, ...]
    capabilities: tuple[str, ...]
    passport_id: str | None = None

    @property
    def passport_bound(self) -> bool:
        return bool(self.passport_id)


@dataclass
class TaskEvent:
    status: TaskStatus
    occurred_at: str
    progress: int
    note: str | None = None
    evidence_ref: str | None = None


@dataclass
class SquadTask:
    task_id: str
    title: str
    objective: str
    domain: WorkDomain
    owner_seat: str
    priority: str = "normal"
    status: TaskStatus = TaskStatus.ASSIGNED
    progress: int = 10
    qa_loops: int = 0
    evidence_refs: list[str] = field(default_factory=list)
    events: list[TaskEvent] = field(default_factory=list)


_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.QUEUED: {TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
    TaskStatus.ASSIGNED: {TaskStatus.EXECUTING, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.EXECUTING: {TaskStatus.QA_REVIEW, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.QA_REVIEW: {
        TaskStatus.REVISION,
        TaskStatus.COMPLETED,
        TaskStatus.BLOCKED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.REVISION: {TaskStatus.EXECUTING, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.BLOCKED: {TaskStatus.ASSIGNED, TaskStatus.EXECUTING, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}


class SquadTeam:
    """Assigns cross-functional work and emits progress suitable for Control Room projections."""

    TEAM_ID = "s-squad"
    PERFORMANCE_DIMENSIONS = (
        "instruction_adherence",
        "completion_rate",
        "quality",
        "reliability",
        "efficiency",
    )

    def __init__(self, seats: list[SquadSeat]) -> None:
        self._seats = {seat.seat_id: seat for seat in seats}
        self._tasks: dict[str, SquadTask] = {}

    @classmethod
    def default(cls) -> SquadTeam:
        return cls(
            [
                SquadSeat(
                    "team-lead",
                    "Squad Lead",
                    tuple(WorkDomain),
                    ("planning", "routing", "coordination", "escalation"),
                ),
                SquadSeat(
                    "business-strategy",
                    "Business Strategist",
                    (WorkDomain.BUSINESS,),
                    ("growth", "market-sizing", "commercial-analysis", "business-planning"),
                ),
                SquadSeat(
                    "research-intelligence",
                    "Research and Intelligence Specialist",
                    (WorkDomain.RESEARCH,),
                    ("research", "source-verification", "competitive-intelligence", "synthesis"),
                ),
                SquadSeat(
                    "operations-delivery",
                    "Operations and Delivery Specialist",
                    (WorkDomain.OPERATIONS,),
                    ("workflow-design", "delivery", "coordination", "service-operations"),
                ),
                SquadSeat(
                    "product-design",
                    "Product and Design Specialist",
                    (WorkDomain.DESIGN,),
                    ("product-design", "visual-design", "customer-journeys", "prototyping"),
                ),
                SquadSeat(
                    "content-communications",
                    "Content and Communications Specialist",
                    (WorkDomain.CONTENT,),
                    ("content", "campaigns", "presentations", "stakeholder-communications"),
                ),
                SquadSeat(
                    "engineering-integration",
                    "Engineering and Integration Specialist",
                    (WorkDomain.ENGINEERING,),
                    ("software", "automation", "integrations", "deployment"),
                ),
                SquadSeat(
                    "qa-evidence",
                    "QA and Evidence Specialist",
                    (WorkDomain.QA,),
                    ("quality-assurance", "evidence-verification", "risk", "acceptance-gates"),
                ),
                SquadSeat(
                    "scribe-progress",
                    "Scribe and Progress Specialist",
                    tuple(WorkDomain),
                    ("progress-tracking", "decision-log", "evidence-index", "handoff"),
                ),
            ]
        )

    def bind_passport(self, seat_id: str, passport_id: str) -> None:
        if not passport_id.strip():
            raise ValueError("passport_id cannot be empty")
        seat = self._require_seat(seat_id)
        self._seats[seat_id] = SquadSeat(
            seat_id=seat.seat_id,
            title=seat.title,
            domains=seat.domains,
            capabilities=seat.capabilities,
            passport_id=passport_id,
        )

    def assign(
        self,
        *,
        task_id: str,
        title: str,
        objective: str,
        domain: WorkDomain,
        priority: str = "normal",
    ) -> SquadTask:
        if task_id in self._tasks:
            raise ValueError(f"task {task_id!r} already exists")
        if not title.strip() or not objective.strip():
            raise ValueError("title and objective are required")
        owner = next(
            (seat for seat in self._seats.values() if seat.domains == (domain,)),
            None,
        )
        if owner is None:
            raise ValueError(f"no specialist seat for {domain.value}")
        task = SquadTask(
            task_id=task_id,
            title=title,
            objective=objective,
            domain=domain,
            owner_seat=owner.seat_id,
            priority=priority,
        )
        task.events.append(self._event(task))
        self._tasks[task_id] = task
        return task

    def transition(
        self,
        task_id: str,
        status: TaskStatus,
        *,
        progress: int | None = None,
        note: str | None = None,
        evidence_ref: str | None = None,
    ) -> SquadTask:
        task = self._require_task(task_id)
        if status not in _TRANSITIONS[task.status]:
            raise ValueError(f"invalid transition: {task.status.value} -> {status.value}")
        if status in {TaskStatus.EXECUTING, TaskStatus.QA_REVIEW, TaskStatus.COMPLETED}:
            if not self._require_seat(task.owner_seat).passport_bound:
                raise ValueError(
                    f"seat {task.owner_seat!r} must be passport-bound before execution"
                )
        next_progress = task.progress if progress is None else progress
        if not 0 <= next_progress <= 100:
            raise ValueError("progress must be between 0 and 100")
        if next_progress < task.progress:
            raise ValueError("progress cannot decrease")
        if status is TaskStatus.COMPLETED:
            next_progress = 100
            if not evidence_ref and not task.evidence_refs:
                raise ValueError("completion requires evidence")
        if status is TaskStatus.REVISION:
            task.qa_loops += 1
        if evidence_ref and evidence_ref not in task.evidence_refs:
            task.evidence_refs.append(evidence_ref)
        task.status = status
        task.progress = next_progress
        task.events.append(self._event(task, note=note, evidence_ref=evidence_ref))
        return task

    def snapshot(self) -> dict[str, Any]:
        counts = {status.value: 0 for status in TaskStatus}
        for task in self._tasks.values():
            counts[task.status.value] += 1
        return {
            "team_id": self.TEAM_ID,
            "name": "S/Squad",
            "team_type": "cross-functional-delivery",
            "supported_domains": [domain.value for domain in WorkDomain],
            "performance_dimensions": list(self.PERFORMANCE_DIMENSIONS),
            "seats": [
                {
                    "seat_id": seat.seat_id,
                    "title": seat.title,
                    "domains": [domain.value for domain in seat.domains],
                    "capabilities": list(seat.capabilities),
                    "passport_bound": seat.passport_bound,
                }
                for seat in self._seats.values()
            ],
            "progress": {
                "total": len(self._tasks),
                "by_status": counts,
                "qa_loops": sum(task.qa_loops for task in self._tasks.values()),
                "evidence_count": sum(len(task.evidence_refs) for task in self._tasks.values()),
            },
        }

    def _require_seat(self, seat_id: str) -> SquadSeat:
        try:
            return self._seats[seat_id]
        except KeyError as exc:
            raise ValueError(f"unknown seat {seat_id!r}") from exc

    def _require_task(self, task_id: str) -> SquadTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise ValueError(f"unknown task {task_id!r}") from exc

    @staticmethod
    def _event(
        task: SquadTask,
        *,
        note: str | None = None,
        evidence_ref: str | None = None,
    ) -> TaskEvent:
        return TaskEvent(
            status=task.status,
            occurred_at=datetime.now(UTC).isoformat(),
            progress=task.progress,
            note=note,
            evidence_ref=evidence_ref,
        )
