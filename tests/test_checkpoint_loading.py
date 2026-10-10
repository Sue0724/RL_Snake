"""加载失败提示、单次文件读取与旧加载接口兼容性。"""

import copy

import numpy as np
import pytest
import torch

import evaluate
import play
from algorithms.factory import create_agent, load_agent
from common.checkpoint import CheckpointError
from common.config import Config


def checkpoint_path(tmp_path, problem=None):
    path = tmp_path / "checkpoint.pt"
    if problem == "missing":
        return path
    if problem == "corrupt":
        path.write_bytes(b"this is not a checkpoint")
        return path
    create_agent(11, 3, Config(hidden_dim=16)).save(path)
    if problem:
        payload = torch.load(path, weights_only=True)
        if problem == "format":
            payload["format_version"] = 99
        elif problem == "config":
            payload["config"] = None
        elif problem == "dimensions":
            payload["state_dim"] = 20
        elif problem == "weights":
            payload["online_net"] = {}
        elif problem == "optimizer":
            payload["optimizer"] = {}
        elif problem == "rng":
            payload["rng_state"] = None
        else:
            raise AssertionError(f"未定义的测试问题：{problem}")
        torch.save(payload, path)
    return path


@pytest.mark.parametrize("problem", [
    "missing", "corrupt", "format", "config", "dimensions", "weights", "optimizer", "rng",
])
def test_play_and_evaluate_report_same_loading_error_before_outputs(tmp_path, capsys, problem):
    path = checkpoint_path(tmp_path, problem)
    output = tmp_path / "evaluations"
    messages = []
    calls = [
        (play.main, ["--agent", "model", "--checkpoint", str(path)]),
        (evaluate.main, ["--checkpoint", str(path), "--output_dir", str(output)]),
    ]
    for main, arguments in calls:
        with pytest.raises(SystemExit) as error:
            main(arguments)
        assert error.value.code == 2
        stderr = capsys.readouterr().err
        assert "Traceback" not in stderr
        message = stderr.split("error: ", 1)[1].strip()
        assert message.startswith("模型加载失败：")
        assert str(path.resolve()) in message
        messages.append(message)
    assert messages[0] == messages[1]
    assert not output.exists()


@pytest.mark.parametrize("problem", [
    "missing", "corrupt", "format", "config", "dimensions", "weights", "optimizer", "rng",
])
def test_direct_agent_load_uses_common_error_and_preserves_source(tmp_path, problem):
    path = checkpoint_path(tmp_path, problem)
    before = path.read_bytes() if path.exists() else None
    agent = create_agent(11, 3, Config(hidden_dim=16))
    with pytest.raises(CheckpointError, match="模型加载失败"):
        agent.load(path)
    if before is not None:
        assert path.read_bytes() == before


def test_factory_reads_file_once_and_restores_same_state_as_legacy_load(tmp_path, monkeypatch):
    agent = create_agent(11, 3, Config(hidden_dim=16, seed=43))
    batch = {
        "states": np.zeros((2, 11), dtype=np.float32),
        "actions": np.array([0, 1]), "rewards": np.ones(2, dtype=np.float32),
        "next_states": np.zeros((2, 11), dtype=np.float32),
        "terminated": np.zeros(2, dtype=bool), "truncated": np.zeros(2, dtype=bool),
    }
    agent.update(batch)
    agent.on_env_step()
    path = tmp_path / "checkpoint.pt"
    agent.save(path)
    source = path.read_bytes()
    original_load = torch.load
    reads = []

    def count_load(*args, **kwargs):
        reads.append(args[0])
        return original_load(*args, **kwargs)

    monkeypatch.setattr(torch, "load", count_load)
    restored, runtime = load_agent(path)
    assert len(reads) == 1
    legacy = create_agent(11, 3, Config(hidden_dim=16, seed=7))
    legacy.load(path)
    assert len(reads) == 2  # 两种加载途径各读取一次。
    assert restored.config == legacy.config == runtime
    assert restored.epsilon == legacy.epsilon == agent.epsilon
    assert restored.global_step == legacy.global_step == 1
    assert restored.update_count == legacy.update_count == 1
    assert restored._rng.bit_generator.state == legacy._rng.bit_generator.state
    assert [restored.select_action(np.zeros(11)) for _ in range(20)] == [
        legacy.select_action(np.zeros(11)) for _ in range(20)
    ]
    for network in ("online_net", "target_net"):
        for key, value in getattr(restored, network).state_dict().items():
            torch.testing.assert_close(value, getattr(legacy, network).state_dict()[key], rtol=0, atol=0)
    assert restored.update(batch) == pytest.approx(legacy.update(batch), rel=0, abs=0)
    for key, value in restored.online_net.state_dict().items():
        torch.testing.assert_close(value, legacy.online_net.state_dict()[key], rtol=0, atol=0)
    assert path.read_bytes() == source


def test_restore_from_memory_performs_no_file_read_and_keeps_device(tmp_path, monkeypatch):
    path = checkpoint_path(tmp_path)
    payload = torch.load(path, weights_only=True)
    source = copy.deepcopy(payload)
    agent = create_agent(11, 3, Config(hidden_dim=16, device="cpu"))

    def reject_read(*args, **kwargs):
        pytest.fail("内存恢复不应访问 checkpoint 文件")

    monkeypatch.setattr(torch, "load", reject_read)
    agent.restore_checkpoint(payload)
    assert agent.config.device == "cpu" and str(agent.device) == "cpu"
    for key, value in source["online_net"].items():
        torch.testing.assert_close(value, agent.online_net.state_dict()[key], rtol=0, atol=0)
    assert agent.epsilon == source["epsilon"]


def test_invalid_runtime_device_is_a_common_loading_error(tmp_path):
    path = checkpoint_path(tmp_path)
    with pytest.raises(CheckpointError, match="模型加载失败"):
        load_agent(path, device="invalid_device")
