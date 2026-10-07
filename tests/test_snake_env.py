"""Stage 1 环境测试，逐项对应 ``docs/STAGE_CHECKLIST.md`` 的 Stage 1 清单。

运行：``pytest``
"""
import copy
import pathlib
import subprocess
import sys
from collections import deque

import numpy as np
import pytest

from common.config import Config
from env.random_agent import RandomAgent
from env.snake_env import DEATH_PENALTY, FOOD_REWARD, LEFT, RIGHT, STRAIGHT, SnakeEnv

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 方向表是规范（INTERFACE.md §3），不是实现细节，所以这里独立写一份用于对照，
# 而不是从 env.snake_env 导入 _MOVE。两处不一致即说明实现偏离了规范。
DELTA = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def make_env(**overrides):
    env = SnakeEnv(Config(**overrides))
    env.reset(seed=42)
    return env


def place(env, body, direction, food=(0, 0)):
    """直接摆一个局面，用于构造随机走不出来的几何情形。"""
    env.body = deque(body)
    env.occupied = set(body)
    env.direction = direction
    env.food = food
    env.done = False


# ---- reset / step 基本形态 ----


def test_state_dim_and_n_actions():
    env = make_env()
    assert env.state_dim == 11
    assert env.n_actions == 3


def test_reset_returns_state_and_info():
    env = SnakeEnv(Config())
    state, info = env.reset(seed=42)

    assert state.shape == (11,)
    assert state.dtype == np.float32
    assert set(info) == {
        "score", "steps", "snake_length",
        "food_reward", "death_penalty", "distance_reward", "step_reward",
    }
    assert info["score"] == 0
    assert info["steps"] == 0
    assert info["snake_length"] == Config().initial_length
    assert info["food_reward"] == 0.0
    assert info["death_penalty"] == 0.0
    assert info["distance_reward"] == 0.0
    assert info["step_reward"] == 0.0


def test_step_returns_five_tuple():
    env = make_env()
    result = env.step(STRAIGHT)

    assert len(result) == 5
    state, reward, terminated, truncated, info = result
    assert state.shape == (11,)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_reward_equals_sum_of_components():
    """INTERFACE.md §5 的恒等式。"""
    env = make_env()
    rng = np.random.default_rng(0)
    for _ in range(50):
        _, reward, terminated, truncated, info = env.step(int(rng.integers(3)))
        assert reward == pytest.approx(
            info["food_reward"] + info["death_penalty"]
            + info["distance_reward"] + info["step_reward"]
        )
        if terminated or truncated:
            break


# ---- 随机种子与初始位置 ----


def test_reset_with_same_seed_is_reproducible():
    first, second = SnakeEnv(Config()), SnakeEnv(Config())
    state_a, _ = first.reset(seed=7)
    state_b, _ = second.reset(seed=7)

    assert np.array_equal(state_a, state_b)
    assert list(first.body) == list(second.body)
    assert first.food == second.food


def test_reset_without_seed_does_not_repeat():
    """INTERFACE.md §7：不传 seed 时沿用当前 np_random，连续 episode 不同局。"""
    env = make_env()
    starts = set()
    for _ in range(20):
        env.reset()
        starts.add((env.body[0], env.food))
    assert len(starts) > 1


def test_initial_head_is_honoured():
    env = make_env(initial_head=(4, 6))
    env.reset(seed=7)

    assert list(env.body) == [(4, 6), (4, 5), (4, 4)]
    assert env.food not in env.occupied


def test_initial_head_without_room_raises():
    env = SnakeEnv(Config(initial_head=(4, 1)))  # 长度 3 的蛇身会越界到 col = -1
    with pytest.raises(ValueError):
        env.reset(seed=7)


# ---- 动作语义 ----


@pytest.mark.parametrize(
    "direction, action, expected",
    [
        ("up", STRAIGHT, "up"), ("up", LEFT, "left"), ("up", RIGHT, "right"),
        ("down", STRAIGHT, "down"), ("down", LEFT, "right"), ("down", RIGHT, "left"),
        ("left", STRAIGHT, "left"), ("left", LEFT, "down"), ("left", RIGHT, "up"),
        ("right", STRAIGHT, "right"), ("right", LEFT, "up"), ("right", RIGHT, "down"),
    ],
)
def test_action_moves_head_per_direction_table(direction, action, expected):
    """INTERFACE.md §2 / §3：12 种（朝向, 动作）组合的位移。

    只放一个蛇头，避免蛇身本身挡住落点干扰判断。
    """
    env = make_env()
    head = (5, 5)
    place(env, [head], direction, food=(0, 0))

    env.step(action)
    dr, dc = DELTA[expected]
    assert env.direction == expected
    assert env.body[0] == (head[0] + dr, head[1] + dc)


# ---- 碰撞 ----


@pytest.mark.parametrize(
    "direction, head",
    [("up", (0, 5)), ("down", (9, 5)), ("left", (5, 0)), ("right", (5, 9))],
)
def test_wall_collision(direction, head):
    env = make_env()
    dr, dc = DELTA[direction]
    place(env, [(head[0] - dr * i, head[1] - dc * i) for i in range(3)], direction, (9, 9))

    _, reward, terminated, truncated, info = env.step(STRAIGHT)
    assert terminated
    assert not truncated
    assert reward == DEATH_PENALTY
    assert info["death_penalty"] == DEATH_PENALTY
    assert info["food_reward"] == 0.0


def test_self_collision_on_body_not_tail():
    """蛇身中段不动，撞上就是死。"""
    env = make_env()
    place(env, [(1, 1), (2, 1), (2, 2), (1, 2), (1, 3)], "up", food=(9, 9))

    _, reward, terminated, _, _ = env.step(RIGHT)  # 头落到 (1,2)，是 body[3]
    assert terminated
    assert reward == DEATH_PENALTY


def test_tail_cell_is_legal():
    """蛇尾同一步会腾出格子，落进去不算碰撞，见 INTERFACE.md §4。"""
    env = make_env()
    place(env, [(1, 1), (2, 1), (2, 2), (1, 2)], "right", food=(9, 9))
    assert env.body[-1] == (1, 2)

    _, reward, terminated, truncated, _ = env.step(STRAIGHT)  # 头落到蛇尾
    assert not terminated
    assert not truncated
    assert reward == 0.0
    assert list(env.body) == [(1, 2), (1, 1), (2, 1), (2, 2)]


def test_danger_features_match_actual_death():
    """danger_* 必须是对"这一步会不会死"的真实预测，见 INTERFACE.md §4。

    把三个动作各自在环境副本上实跑一步，与状态里的对应位逐一比对。
    """
    env = make_env()
    rng = np.random.default_rng(0)

    for _ in range(200):
        state = env._get_state()
        for action in (STRAIGHT, LEFT, RIGHT):
            probe = copy.deepcopy(env)
            _, _, terminated, _, _ = probe.step(action)
            assert bool(state[action]) == terminated, (
                f"朝向 {env.direction}、动作 {action}：状态给出 danger={bool(state[action])}，"
                f"实跑 terminated={terminated}"
            )

        _, _, terminated, truncated, _ = env.step(int(rng.integers(3)))
        if terminated or truncated:
            env.reset()


# ---- 吃食物 ----


def test_eating_grows_snake_and_scores():
    env = make_env()
    place(env, [(5, 5), (5, 4), (5, 3)], "right", food=(5, 6))

    _, reward, terminated, truncated, info = env.step(STRAIGHT)
    assert not terminated
    assert not truncated
    assert reward == FOOD_REWARD
    assert info["food_reward"] == FOOD_REWARD
    assert info["score"] == 1
    assert info["snake_length"] == 4
    assert env.food != (5, 6)
    assert env.food not in env.occupied


def test_food_never_spawns_on_snake():
    env = make_env()
    for _ in range(1000):
        env._spawn_food()
        assert env.food not in env.occupied


# ---- terminated / truncated ----


def test_terminated_on_death_makes_truncated_false():
    env = make_env()
    place(env, [(0, 5), (1, 5), (2, 5)], "up", food=(9, 9))

    _, _, terminated, truncated, _ = env.step(STRAIGHT)
    assert terminated
    assert not truncated


def test_truncated_when_step_limit_reached():
    env = make_env(max_steps_per_episode=1)
    place(env, [(5, 5), (5, 4), (5, 3)], "right", food=(0, 0))

    _, _, terminated, truncated, info = env.step(STRAIGHT)
    assert not terminated
    assert truncated
    assert info["steps"] == 1


def test_step_after_done_raises():
    env = make_env()
    place(env, [(0, 5), (1, 5), (2, 5)], "up", food=(9, 9))
    env.step(STRAIGHT)

    with pytest.raises(RuntimeError, match="reset"):
        env.step(STRAIGHT)


def test_step_before_reset_raises():
    with pytest.raises(RuntimeError, match="reset"):
        SnakeEnv(Config()).step(STRAIGHT)


def test_invalid_action_raises():
    with pytest.raises(ValueError):
        make_env().step(3)


def test_unimplemented_modes_raise():
    """非法取值必须硬失败，不能静默回退，见 INTERFACE.md §4 / §6。"""
    with pytest.raises(NotImplementedError):
        SnakeEnv(Config(reward_mode="distance"))
    with pytest.raises(NotImplementedError):
        SnakeEnv(Config(state_mode="v2"))


# ---- 状态向量 ----


def test_direction_is_one_hot():
    env = make_env()
    for direction in DELTA:
        place(env, [(5, 5), (5, 4), (5, 3)], direction, food=(0, 0))
        expected = [1.0 if name == direction else 0.0
                    for name in ("up", "down", "left", "right")]
        assert list(env._get_state()[3:7]) == expected


def test_food_features_are_not_mutually_exclusive():
    """INTERFACE.md §4：食物在左上方时 food_up 与 food_left 同时为 1。"""
    env = make_env()
    place(env, [(5, 5), (5, 4), (5, 3)], "right", food=(2, 2))

    state = env._get_state()
    assert state[7] == 1.0 and state[9] == 1.0
    assert state[8] == 0.0 and state[10] == 0.0


def test_state_dim_is_stable_across_episodes():
    env = make_env()
    rng = np.random.default_rng(1)

    for _ in range(5):
        state, _ = env.reset()
        assert state.shape == (11,)
        for _ in range(50):
            state, _, terminated, truncated, _ = env.step(int(rng.integers(3)))
            assert state.shape == (11,)
            assert state.dtype == np.float32
            if terminated or truncated:
                break


# ---- render ----


def test_render_is_noop_without_render_mode():
    env = make_env()
    assert env.render() is None
    env.close()


def test_importing_env_does_not_import_pygame():
    """训练默认不渲染，导入环境不应把 pygame 拉进来（README 风险三）。"""
    code = "import sys, env.snake_env; assert 'pygame' not in sys.modules, sys.modules['pygame']"
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True)


# ---- 连续运行 ----


def test_random_agent_rollout_100_episodes():
    """STAGE_CHECKLIST Stage 1：Random Agent 可连续运行 100 episode 无异常。"""
    env = make_env()
    agent = RandomAgent(env.n_actions, seed=0)

    for episode in range(100):
        state, _ = env.reset(seed=episode)
        assert state.shape == (11,)

        steps = 0
        while True:
            action = agent.select_action(state, training=False)
            state, reward, terminated, truncated, info = env.step(action)
            steps += 1

            assert state.shape == (11,)
            assert info["steps"] == steps
            assert info["snake_length"] == len(env.body)
            assert env.food not in env.occupied
            assert reward == pytest.approx(
                info["food_reward"] + info["death_penalty"]
                + info["distance_reward"] + info["step_reward"]
            )

            if terminated or truncated:
                break
            assert steps < env.config.max_steps_per_episode
