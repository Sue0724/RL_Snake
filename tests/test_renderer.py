"""渲染测试。

``rgb_array`` 可以自动断言；``human`` 只能人工肉眼确认，这里仅保证它不抛异常。
"""
import numpy as np
import pytest

from common.config import Config
from env.renderer import CELL
from env.snake_env import SnakeEnv


def rgb_env(**overrides):
    """固定初始蛇头，避免随机开局正好贴边导致第一步就撞墙。"""
    return SnakeEnv(Config(render_mode="rgb_array", initial_head=(5, 5), **overrides))


def test_rgb_array_frame_shape_and_dtype():
    env = rgb_env()
    env.reset(seed=1)

    frame = env.render()
    assert frame.shape == (10 * CELL, 10 * CELL, 3)
    assert frame.dtype == np.uint8
    env.close()


def test_frame_reflects_the_current_board():
    """帧必须随局面变化，否则录出来的视频是静止的。"""
    env = rgb_env()
    env.reset(seed=1)

    before = env.render()
    env.step(0)  # 直行，蛇头一定移动
    assert not np.array_equal(before, env.render())
    env.close()


def test_board_size_is_reflected_in_frame():
    env = rgb_env(board_size=6)
    env.reset(seed=1)

    assert env.render().shape == (6 * CELL, 6 * CELL, 3)
    env.close()


def test_human_mode_renders_and_closes():
    """human 模式会弹出真实窗口，只验证不抛异常。"""
    env = SnakeEnv(Config(render_mode="human"))
    env.reset(seed=1)

    assert env.render() is None
    env.close()


def test_unknown_render_mode_raises():
    with pytest.raises(ValueError):
        SnakeEnv(Config(render_mode="ansi"))
