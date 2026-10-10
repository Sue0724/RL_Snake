"""公共入口的算法分派、配置恢复与训练/评估集成检查。"""

import copy
import dataclasses
import hashlib
import json

import numpy as np
import pytest
import torch

from algorithms.dqn import DQNAgent
from algorithms import factory
from algorithms.factory import create_agent, load_agent
from common.config import Config
from env.random_agent import RandomAgent
from evaluate import evaluate
from train import train


def test_creation_dispatches_dqn_and_random_without_mutating_config():
    config = Config(hidden_dim=16)
    original = dataclasses.asdict(config)
    dqn = create_agent(20, 4, config, training=True)
    assert isinstance(dqn, DQNAgent)
    assert dqn.online_net(torch.zeros(20)).shape == (4,)
    random_config = dataclasses.replace(config, algorithm="random", seed=7)
    first = create_agent(20, 4, random_config)
    second = create_agent(20, 4, random_config)
    assert isinstance(first, RandomAgent)
    assert [first.select_action(None) for _ in range(20)] == [
        second.select_action(None) for _ in range(20)
    ]
    assert dataclasses.asdict(config) == original


@pytest.mark.parametrize("algorithm", ["double_dqn", "dueling_dqn", "unknown"])
def test_unsupported_algorithm_is_rejected_in_factory_and_training(tmp_path, algorithm):
    config = Config(algorithm=algorithm)
    with pytest.raises(ValueError, match="尚未支持"):
        create_agent(11, 3, config)
    with pytest.raises(ValueError, match="尚未支持"):
        train(config, output_dir=tmp_path, total_steps=1)
    assert not list(tmp_path.iterdir())


def test_random_cannot_enter_training(tmp_path):
    with pytest.raises(ValueError, match="不支持训练"):
        train(Config(algorithm="random"), output_dir=tmp_path, total_steps=1)
    assert not list(tmp_path.iterdir())


def test_load_restores_saved_state_and_runtime_config_without_rendering(tmp_path, monkeypatch):
    config = Config(hidden_dim=16, board_size=12, seed=43, initial_head=(5, 5),
                    render_mode="human", learning_rate=0.002)
    agent = create_agent(11, 3, config)
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
    before = path.read_bytes()

    def reject_renderer(*args, **kwargs):
        pytest.fail("模型加载不应创建渲染器")

    monkeypatch.setattr("env.renderer.Renderer", reject_renderer)
    restored, runtime = load_agent(path, device="cpu", render_mode="rgb_array")
    assert runtime == dataclasses.replace(config, device="cpu", render_mode="rgb_array")
    assert restored.config == config
    assert not restored.online_net.training and not restored.target_net.training
    assert restored.global_step == 1 and restored.update_count == 1
    assert restored.epsilon == agent.epsilon
    assert restored.optimizer.param_groups[0]["lr"] == config.learning_rate
    for network in ("online_net", "target_net"):
        for key, value in getattr(agent, network).state_dict().items():
            torch.testing.assert_close(value, getattr(restored, network).state_dict()[key], rtol=0, atol=0)
    rng_before = copy.deepcopy(restored._rng.bit_generator.state)
    state = np.zeros(11)
    assert restored.select_action(state, training=False) == agent.select_action(state, training=False)
    assert restored._rng.bit_generator.state == rng_before
    assert restored.epsilon == agent.epsilon and restored.global_step == 1
    assert restored.update(batch) == pytest.approx(agent.update(batch), rel=0, abs=0)
    assert path.read_bytes() == before


@pytest.mark.parametrize("change,message", [
    ({"format_version": 99}, "格式不支持"),
    ({"config": None}, "有效的 Config"),
    ({"state_dim": 20}, "环境配置不匹配"),
    ({"n_actions": 4}, "环境配置不匹配"),
])
def test_invalid_checkpoint_metadata_is_rejected(tmp_path, change, message):
    path = tmp_path / "checkpoint.pt"
    create_agent(11, 3, Config(hidden_dim=16)).save(path)
    payload = torch.load(path, weights_only=True)
    payload.update(change)
    torch.save(payload, path)
    with pytest.raises(ValueError, match=message):
        load_agent(path)


def test_unsupported_algorithm_in_checkpoint_is_not_loaded_as_dqn(tmp_path):
    path = tmp_path / "checkpoint.pt"
    create_agent(11, 3, Config(hidden_dim=16)).save(path)
    payload = torch.load(path, weights_only=True)
    payload["config"]["algorithm"] = "double_dqn"
    torch.save(payload, path)
    with pytest.raises(ValueError, match="尚未支持"):
        load_agent(path)


def test_training_save_load_evaluation_preserves_model_and_separates_runs(tmp_path):
    config = Config(hidden_dim=16, batch_size=4, min_buffer_size=4, buffer_size=32,
                    target_update_interval=5, max_steps_per_episode=20)
    first, status = train(config, output_dir=tmp_path / "train", total_steps=40)
    second, _ = train(config, output_dir=tmp_path / "train", total_steps=40)
    assert status == "completed" and first != second
    for directory in (first, second):
        assert all((directory / name).is_file() for name in (
            "config.json", "metrics.csv", "summary.json", "checkpoint.pt",
        ))
        summary = json.loads((directory / "summary.json").read_text())
        assert summary["global_step"] == 40 and summary["update_count"] == 37
    first_agent, _ = load_agent(first / "checkpoint.pt")
    second_agent, _ = load_agent(second / "checkpoint.pt")
    for key, value in first_agent.online_net.state_dict().items():
        torch.testing.assert_close(value, second_agent.online_net.state_dict()[key], rtol=0, atol=0)
    path = first / "checkpoint.pt"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    evaluation = evaluate([path, second / "checkpoint.pt"], num_episodes=3,
                          compare_random=True, output_dir=tmp_path / "evaluate")
    summary = json.loads((evaluation / "summary.json").read_text())
    assert summary["status"] == "completed"
    assert len(summary["models"]) == 3
    assert all(model["num_episodes"] == 3 for model in summary["models"])
    assert summary["models"][0]["mean_score"] == summary["models"][1]["mean_score"]
    assert summary["protocol"]["exploration"] is False
    assert summary["protocol"]["network_update"] is False
    assert summary["protocol"]["replay_write"] is False
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_evaluation_rejects_mismatched_environments_before_creating_output(tmp_path):
    paths = []
    for index, board_size in enumerate((10, 12)):
        path = tmp_path / f"model{index}.pt"
        create_agent(11, 3, Config(board_size=board_size, hidden_dim=16)).save(path)
        paths.append(path)
    output = tmp_path / "evaluation"
    with pytest.raises(ValueError, match="环境、状态和奖励配置必须一致"):
        evaluate(paths, output_dir=output)
    assert not output.exists()


def test_registered_agent_uses_same_training_and_evaluation_loop(tmp_path, monkeypatch):
    # 测试替身验证扩展点，无需实现或冒充后续正式算法。
    class TestAgent(DQNAgent):
        pass

    monkeypatch.setitem(factory.AGENT_CLASSES, "test_agent", TestAgent)
    config = Config(algorithm="test_agent", hidden_dim=16)
    directory, _ = train(config, total_steps=2, output_dir=tmp_path / "train")
    restored, runtime = load_agent(directory / "checkpoint.pt")
    assert isinstance(restored, TestAgent) and runtime.algorithm == "test_agent"
    evaluation = evaluate([directory / "checkpoint.pt"], num_episodes=2,
                          output_dir=tmp_path / "evaluate")
    summary = json.loads((evaluation / "summary.json").read_text())
    model = summary["models"][0]
    assert model["algorithm"] == "test_agent"
    assert model["model_id"] == "test_agent_1_seed42"
    assert model["training_seed"] == 42
    assert "dqn_across_models" not in summary
