from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_assigns_non_code_work_to_the_matching_seat() -> None:
    from teams.squad.runtime import SquadTeam, WorkDomain

    team = SquadTeam.default()
    task = team.assign(
        task_id="SQ-001",
        title="Assess a new market",
        objective="Produce an evidence-backed market entry recommendation",
        domain=WorkDomain.BUSINESS,
    )

    assert task.owner_seat == "business-strategy"
    assert task.status.value == "assigned"
    assert task.progress == 10


def test_requires_passport_binding_before_execution() -> None:
    from teams.squad.runtime import SquadTeam, TaskStatus, WorkDomain

    team = SquadTeam.default()
    task = team.assign(
        task_id="SQ-002",
        title="Prepare campaign",
        objective="Create the launch campaign packet",
        domain=WorkDomain.CONTENT,
    )

    with pytest.raises(ValueError, match="passport-bound"):
        team.transition(task.task_id, TaskStatus.EXECUTING)


def test_tracks_progress_qa_loops_and_evidence() -> None:
    from teams.squad.runtime import SquadTeam, TaskStatus, WorkDomain

    team = SquadTeam.default()
    team.bind_passport("research-intelligence", "passport:squad-research")
    task = team.assign(
        task_id="SQ-003",
        title="Research competitors",
        objective="Map direct and adjacent competitors",
        domain=WorkDomain.RESEARCH,
    )

    team.transition(task.task_id, TaskStatus.EXECUTING, progress=35)
    team.transition(
        task.task_id, TaskStatus.QA_REVIEW, progress=80, evidence_ref="evidence://report-v1"
    )
    team.transition(task.task_id, TaskStatus.REVISION, note="Sources need stronger provenance")
    team.transition(task.task_id, TaskStatus.EXECUTING, progress=90)
    team.transition(task.task_id, TaskStatus.QA_REVIEW, progress=95)
    completed = team.transition(
        task.task_id,
        TaskStatus.COMPLETED,
        progress=100,
        evidence_ref="evidence://report-final",
    )

    assert completed.qa_loops == 1
    assert completed.evidence_refs == ["evidence://report-v1", "evidence://report-final"]
    assert completed.progress == 100
    assert completed.status is TaskStatus.COMPLETED


def test_snapshot_uses_shared_performance_dimensions() -> None:
    from teams.squad.runtime import SquadTeam

    snapshot = SquadTeam.default().snapshot()

    assert snapshot["team_id"] == "s-squad"
    assert set(snapshot["performance_dimensions"]) == {
        "instruction_adherence",
        "completion_rate",
        "quality",
        "reliability",
        "efficiency",
    }
    assert snapshot["supported_domains"] == [
        "business",
        "research",
        "operations",
        "design",
        "content",
        "engineering",
        "qa",
    ]


def test_manifest_pins_upstream_and_declares_durable_progress_sink() -> None:
    manifest_path = Path(__file__).parents[1] / "teams" / "squad" / "team.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["team_id"] == "s-squad"
    assert manifest["upstream"]["release"] == "v0.13.1"
    assert manifest["governance"]["activation_requires_passport"] is True
    assert manifest["tracking"]["canonical_store"] == "supabase"
    assert set(manifest["work_domains"]) >= {"business", "research", "design", "operations"}
