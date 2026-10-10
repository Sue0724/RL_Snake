"""``play.py`` 的入口与循环测试。

human 模式要人工按键，无法自动跑；这里覆盖 CLI、模型配置、演示循环和退出。
"""
import json
import pathlib
import subprocess
import sys

import pygame
import pytest
import torch

import play
from algorithms.factory import create_agent
from common.config import Config
from env.random_agent import RandomAgent
from env.snake_env import SnakeEnv
from evaluate import evaluate
from play import run
from train import train

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Windows 中文控制台按 GBK 输出，不能依赖 locale 猜测；此处断言的又都是 ASCII，
# 所以按 UTF-8 解码并容错即可。
DECODE = {"capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}


def run_play(*args):
    return subprocess.run(
        [sys.executable, "play.py", *args], cwd=ROOT, timeout=60, **DECODE
    )


def test_help_lists_own_options_and_config_options_together():
    """``build_parser`` 必须让 play.py 自有参数与配置参数出现在同一份 help 里。"""
    result = run_play("-h")
    assert result.returncode == 0
    assert "--agent" in result.stdout
    assert "--fps" in result.stdout
    assert "--board_size" in result.stdout
    assert "--checkpoint" in result.stdout and "model" in result.stdout


def test_rejected_render_mode_exits_with_error():
    result = run_play("--render_mode", "rgb_array")
    assert result.returncode != 0
    assert "human" in result.stderr


def test_random_mode_runs_one_episode_without_a_window():
    env = SnakeEnv(
        Config(render_mode="rgb_array", max_steps_per_episode=30, initial_head=(5, 5))
    )
    agent = RandomAgent(env.n_actions, seed=0)

    assert run(env, agent, fps=1000) is True
    env.close()


def test_explicit_seed_is_used_as_is():
    """传了 --seed 就必须原样使用，否则没法复现某一次运行。

    0 也要原样返回：判据是 is None，不是真值判断。
    """
    assert play._pick_seed(7) == 7
    assert play._pick_seed(0) == 0


def test_seed_is_randomised_when_not_given():
    """不传 --seed 时每次应当不同，否则演示和人工验证只会看到同一条轨迹。"""
    seeds = {play._pick_seed(None) for _ in range(50)}

    assert len(seeds) > 1


@pytest.mark.parametrize("arguments,message", [
    (["--agent", "model"], "必须提供 --checkpoint"),
    (["--checkpoint", "unused.pt"], "只能用于 --agent model"),
    (["--fps", "0"], "fps 必须为正整数"),
    (["--fps", "-1"], "fps 必须为正整数"),
    (["--seed", "-1"], "seed 必须"),
    (["--agent", "model", "--checkpoint", "unused.pt", "--board_size", "12"], "--board_size"),
    (["--agent", "model", "--checkpoint", "unused.pt", "--hidden_dim", "16"], "--hidden_dim"),
    (["--agent", "model", "--checkpoint", "unused.pt", "--algorithm", "dqn"], "--algorithm"),
])
def test_invalid_cli_is_rejected_before_environment_creation(monkeypatch, capsys, arguments, message):
    def reject_environment(config):
        pytest.fail("非法参数不应创建环境或窗口")

    monkeypatch.setattr(play, "SnakeEnv", reject_environment)
    with pytest.raises(SystemExit) as error:
        play.main(arguments)
    assert error.value.code == 2
    assert message in capsys.readouterr().err


@pytest.mark.parametrize("corrupted", [False, True])
def test_model_loading_failure_is_reported_as_cli_error(tmp_path, capsys, corrupted):
    path = tmp_path / "missing_or_invalid.pt"
    if corrupted:
        path.write_bytes(b"this is not a checkpoint")
    with pytest.raises(SystemExit) as error:
        play.main(["--agent", "model", "--checkpoint", str(path)])
    assert error.value.code == 2
    assert "模型加载失败" in capsys.readouterr().err


@pytest.mark.parametrize("seed", [0, None])
def test_trained_model_demo_restores_environment_and_never_trains(tmp_path, monkeypatch, seed):
    config = Config(board_size=6, initial_head=(3, 3), max_steps_per_episode=20,
                    hidden_dim=16, seed=43, min_buffer_size=4, batch_size=4, buffer_size=32)
    directory, _ = train(config, total_steps=40, output_dir=tmp_path)
    checkpoint = directory / "checkpoint.pt"
    source = checkpoint.read_bytes()
    evaluation = evaluate([checkpoint], num_episodes=1, eval_seed=0 if seed == 0 else 321,
                          output_dir=tmp_path / "evaluation")
    expected = json.loads((evaluation / "summary.json").read_text())["models"][0]
    recorded = {}
    original_run = play.run

    def reject_training(*args, **kwargs):
        pytest.fail("演示不能更新、计训练步或保存模型")

    def inspect_run(env, agent, fps):
        recorded["env"] = env
        assert env.config.board_size == 6 and env.config.hidden_dim == 16
        assert env.config.initial_head == (3, 3)
        assert env.config.max_steps_per_episode == 20
        assert env.config.seed == (0 if seed == 0 else 321)
        assert env.config.render_mode == "human"
        assert agent.config.seed == 43
        assert not agent.online_net.training
        before = (agent.epsilon, agent.global_step, agent.update_count)
        weights = {key: value.clone() for key, value in agent.online_net.state_dict().items()}
        original_select = agent.select_action
        actions = []

        def select(state, training=True):
            assert training is False
            action = original_select(state, training=training)
            actions.append(action)
            return action

        monkeypatch.setattr(agent, "select_action", select)
        for method in ("update", "on_env_step", "save"):
            monkeypatch.setattr(agent, method, reject_training)
        assert original_run(env, agent, fps) is True
        assert env.score == expected["mean_score"]
        assert env.steps == expected["mean_episode_length"]
        assert actions and (agent.epsilon, agent.global_step, agent.update_count) == before
        for key, value in weights.items():
            torch.testing.assert_close(value, agent.online_net.state_dict()[key], rtol=0, atol=0)

    monkeypatch.setattr(play, "run", inspect_run)
    monkeypatch.setattr(play.time, "sleep", lambda seconds: None)
    if seed is None:
        monkeypatch.setattr(play, "_pick_seed", lambda value: 321)
    args = ["--agent", "model", "--checkpoint", str(checkpoint), "--fps", "1000"]
    if seed is not None:
        args += ["--seed", str(seed)]
    assert play.main(args) == 0
    assert recorded["env"].renderer is None
    assert checkpoint.read_bytes() == source


def test_model_cli_is_reproducible_with_same_seed(tmp_path):
    path = tmp_path / "checkpoint.pt"
    create_agent(11, 3, Config(hidden_dim=16, max_steps_per_episode=10)).save(path)
    arguments = ["--agent", "model", "--checkpoint", str(path), "--seed", "0", "--fps", "1000"]
    first, second = run_play(*arguments), run_play(*arguments)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert "episode 结束" in first.stdout


@pytest.mark.parametrize("event_type,key", [
    (pygame.QUIT, None), (pygame.KEYDOWN, pygame.K_q), (pygame.KEYDOWN, pygame.K_ESCAPE),
])
def test_agent_demo_quits_before_next_action(monkeypatch, event_type, key):
    env = SnakeEnv(Config(render_mode="rgb_array"))
    agent = create_agent(env.state_dim, env.n_actions, Config(hidden_dim=16))

    def request_exit(seconds):
        pygame.event.post(pygame.event.Event(event_type, {} if key is None else {"key": key}))

    def reject_action(*args, **kwargs):
        pytest.fail("退出事件之后不应再走一步")

    monkeypatch.setattr(play.time, "sleep", request_exit)
    monkeypatch.setattr(agent, "select_action", reject_action)
    try:
        assert play.run(env, agent, fps=10) is False
        assert env.steps == 0
    finally:
        env.close()


def test_keyboard_interrupt_closes_model_environment(tmp_path, monkeypatch):
    path = tmp_path / "checkpoint.pt"
    create_agent(11, 3, Config(hidden_dim=16)).save(path)
    recorded = {}

    def interrupt(env, agent, fps):
        recorded["env"] = env
        raise KeyboardInterrupt

    monkeypatch.setattr(play, "run", interrupt)
    assert play.main(["--agent", "model", "--checkpoint", str(path), "--seed", "0"]) == 0
    assert recorded["env"].renderer is None
