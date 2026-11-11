import json
from pathlib import Path

import pytest

from modelctl.errors import ModelctlError
from modelctl.layout import Layout, atomic_symlink
from modelctl.maintenance import (
    audit_objects,
    audit_staging,
    cleanup_objects,
    cleanup_staging,
    prune_cleanup_quarantine,
)
from modelctl.manifest import parse_manifest
from modelctl.validation import ExpectedFile, write_metadata


def _object(path: Path, name: str = "demo") -> None:
    manifest = parse_manifest({"repo": "org/demo", "runtime": "vllm"}, name)
    path.mkdir(parents=True)
    (path / "config.json").write_bytes(b"data")
    write_metadata(path, manifest, "a" * 40, [ExpectedFile("config.json", 4)], ".")


def _state(root: Path, name: str, state: str, staging: Path) -> None:
    path = root / "state" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "operation": "update",
                "state": state,
                "history": [{"state": state, "staging": str(staging)}],
            }
        )
    )


def test_staging_audit_and_explicit_cleanup(tmp_path):
    layout = Layout(tmp_path)
    layout.prepare()
    failed = layout.staging / "org" / "demo" / "commit--failed"
    resumable = layout.staging / "org" / "demo" / "commit--resumable"
    orphaned = layout.staging / "org" / "other" / "commit--orphaned"
    for path in (failed, resumable, orphaned):
        path.mkdir(parents=True)
        (path / "data").write_bytes(b"data")
    _state(tmp_path, "demo", "FAILED_UNPUBLISHED", failed)
    _state(tmp_path, "resume", "PARTIAL_RESUMABLE", resumable)

    results = {item.path: item for item in audit_staging(tmp_path)}
    assert results[failed].status == "failed_unpublished"
    assert results[failed].name == "demo"
    assert results[resumable].status == "resumable"
    assert results[orphaned].status == "orphaned"

    relative = str(failed.relative_to(layout.staging))
    dry_run = cleanup_staging(tmp_path, [relative])
    assert dry_run[0].status == "failed_unpublished"
    assert failed.exists()
    cleanup_staging(tmp_path, [relative], apply=True)
    assert not failed.exists()

    with pytest.raises(ModelctlError, match="resumable"):
        cleanup_staging(tmp_path, [str(resumable.relative_to(layout.staging))])


def test_prune_cleanup_quarantine_lists_then_removes_debris_only(tmp_path):
    layout = Layout(tmp_path)
    layout.prepare()
    debris = layout.staging / ".cleanup-quarantine" / "deadbeef"
    (debris / "objects").mkdir(parents=True)
    (debris / "objects" / "w.bin").write_bytes(b"x" * 2048)
    # Everything the prune must never touch:
    regular = layout.staging / "org" / "demo" / "commit--x"
    regular.mkdir(parents=True)
    (regular / "data").write_bytes(b"data")
    active_quarantine = layout.staging / ".active-quarantine" / "glm" / "stamp"
    active_quarantine.mkdir(parents=True)
    (active_quarantine / "w.bin").write_bytes(b"keep")
    catalog = tmp_path / "catalog.json"
    catalog.write_text("{}")

    dry = prune_cleanup_quarantine(tmp_path)
    assert [item.status for item in dry] == ["would_remove"]
    assert dry[0].bytes >= 2048  # _tree_bytes reports disk usage, not logical size
    assert debris.exists()  # dry run removes nothing

    removed = prune_cleanup_quarantine(tmp_path, apply=True)
    assert [item.status for item in removed] == ["removed"]
    assert not debris.exists()
    assert not (layout.staging / ".cleanup-quarantine").exists()
    assert regular.exists()
    assert active_quarantine.exists()  # per-model cleanup-quarantine territory
    assert catalog.read_text() == "{}"

    assert prune_cleanup_quarantine(tmp_path) == []


def test_object_audit_and_gc_refuse_active_object(tmp_path):
    layout = Layout(tmp_path)
    layout.prepare()
    active = layout.models / "org" / "demo" / "commit--active"
    orphaned = layout.models / "org" / "demo" / "commit--old"
    _object(active)
    _object(orphaned)
    atomic_symlink(active, layout.active / "demo")

    results = {item.path: item for item in audit_objects(tmp_path)}
    assert results[active].status == "active"
    assert results[orphaned].status == "unreferenced"

    active_relative = str(active.relative_to(layout.models))
    with pytest.raises(ModelctlError, match="active"):
        cleanup_objects(tmp_path, [active_relative], apply=True)

    orphaned_relative = str(orphaned.relative_to(layout.models))
    dry_run = cleanup_objects(tmp_path, [orphaned_relative])
    assert dry_run[0].status == "unreferenced"
    assert orphaned.exists()
    cleanup_objects(tmp_path, [orphaned_relative], apply=True)
    assert not orphaned.exists()
    assert active.exists()
    assert layout.active_path("demo").resolve() == active.resolve()
