"""Bounded retry for Windows atomic checkpoint replacement."""

from pathlib import Path

import pytest

import train as training
from common.config import Config
import json


class Snapshot:
    def __init__(self):
        self.saves = 0

    def save(self, path):
        self.saves += 1
        path.write_bytes(b"new snapshot")


def test_temporary_permission_error_retries_same_snapshot(tmp_path, monkeypatch):
    destination = tmp_path / "checkpoint.pt"
    destination.write_bytes(b"old snapshot")
    replace = Path.replace
    attempts, waits = [], []

    def locked_twice(source, target):
        attempts.append(source)
        if len(attempts) < 3:
            assert destination.read_bytes() == b"old snapshot"
            raise PermissionError("temporarily locked")
        return replace(source, target)

    monkeypatch.setattr(Path, "replace", locked_twice)
    monkeypatch.setattr(training.time, "sleep", waits.append)
    agent = Snapshot()
    training.save_checkpoint(agent, tmp_path)
    assert agent.saves == 1 and len(attempts) == 3 and waits == [0.2, 0.4]
    assert destination.read_bytes() == b"new snapshot"
    assert not (tmp_path / "checkpoint.pt.tmp").exists()


def test_persistent_permission_error_keeps_old_snapshot_and_raises(tmp_path, monkeypatch):
    destination = tmp_path / "checkpoint.pt"
    destination.write_bytes(b"old snapshot")
    attempts, waits = [], []

    def locked(source, target):
        attempts.append(source)
        raise PermissionError("still locked")

    monkeypatch.setattr(Path, "replace", locked)
    monkeypatch.setattr(training.time, "sleep", waits.append)
    agent = Snapshot()
    with pytest.raises(PermissionError, match="still locked"):
        training.save_checkpoint(agent, tmp_path)
    assert agent.saves == 1 and len(attempts) == 6
    assert waits == [0.2, 0.4, 0.8, 1.6, 3.2]
    assert destination.read_bytes() == b"old snapshot"
    assert (tmp_path / "checkpoint.pt.tmp").read_bytes() == b"new snapshot"


def test_unrelated_io_error_is_not_retried(tmp_path, monkeypatch):
    def fail(source, target):
        raise OSError("disk failure")

    monkeypatch.setattr(Path, "replace", fail)
    monkeypatch.setattr(training.time, "sleep", lambda _: pytest.fail("must not retry"))
    with pytest.raises(OSError, match="disk failure"):
        training.save_checkpoint(Snapshot(), tmp_path)


def test_final_save_failure_records_failed_summary(tmp_path, monkeypatch):
    save = training.save_checkpoint
    calls = []

    def fail_final(agent, directory):
        calls.append(directory)
        if len(calls) == 2:
            raise PermissionError("final save failed")
        return save(agent, directory)

    monkeypatch.setattr(training, "save_checkpoint", fail_final)
    with pytest.raises(PermissionError, match="final save failed"):
        training.train(Config(hidden_dim=8), output_dir=tmp_path, total_steps=2)
    summaries = list(tmp_path.glob("*/summary.json"))
    summary = json.loads(summaries[0].read_text(encoding="utf-8"))
    assert summary["status"] == "failed" and summary["global_step"] == 2
    assert "final save failed" in summary["error"]
