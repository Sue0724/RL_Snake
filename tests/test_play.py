"""``play.py`` 的入口与循环测试。

human 模式要人工按键，无法自动跑；这里覆盖 CLI 组合与 random 模式循环。
"""
import pathlib
import subprocess
import sys

from common.config import Config
from env.random_agent import RandomAgent
from env.snake_env import SnakeEnv
from play import run

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
