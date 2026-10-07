"""贪吃蛇环境。

返回值与语义冻结于 ``docs/INTERFACE.md``，本文件是其实现。

    env = SnakeEnv(config)
    state, info = env.reset(seed=42)
    next_state, reward, terminated, truncated, info = env.step(action)

只做环境逻辑，不依赖 pygame：渲染交给 ``env/renderer.py``，且仅在
``render_mode`` 非 None 时惰性导入，保证训练时不加载渲染相关代码。

内部只用 ``body``（``deque``，[0] 是蛇头）与 ``occupied``（``set``）表示蛇，
两者只在 ``_place_snake`` 与 ``_advance`` 中同时改动，保证严格同步。
"""
from collections import deque

import numpy as np

# 方向向量 (row, col)，row 向下增大、col 向右增大，见 INTERFACE.md §3
_MOVE = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
_NAME_BY_MOVE = {move: name for name, move in _MOVE.items()}

# 朝向在状态向量中的下标，见 INTERFACE.md §4
_MOVING_INDEX = {"up": 3, "down": 4, "left": 5, "right": 6}

# 相对动作，见 INTERFACE.md §2
STRAIGHT, LEFT, RIGHT = 0, 1, 2

INITIAL_DIRECTION = "right"
STATE_DIM = 11
N_ACTIONS = 3

FOOD_REWARD = 10.0
DEATH_PENALTY = -10.0


class SnakeEnv:
    """``board_size`` × ``board_size`` 网格上的相对动作贪吃蛇环境。"""

    def __init__(self, config):
        if config.reward_mode != "sparse":
            raise NotImplementedError(
                f"reward_mode={config.reward_mode!r} 尚未实现（Stage 5），当前只支持 'sparse'"
            )
        if config.state_mode != "v1":
            raise NotImplementedError(
                f"state_mode={config.state_mode!r} 尚未实现（Stage 4），当前只支持 'v1'"
            )

        self.config = config
        self.n_rows = self.n_cols = config.board_size
        self.np_random = np.random.default_rng(config.seed)

        self.body = deque()
        self.occupied = set()
        self.direction = INITIAL_DIRECTION
        self.food = None
        self.score = 0
        self.steps = 0
        self.done = False

        self.renderer = None
        if config.render_mode is not None:
            from .renderer import Renderer

            self.renderer = Renderer(config.board_size, config.render_mode)

    # ---- 只读属性，见 INTERFACE.md §1 ----

    @property
    def state_dim(self):
        return STATE_DIM

    @property
    def n_actions(self):
        return N_ACTIONS

    # ---- 生命周期 ----

    def reset(self, seed=None):
        """开始新 episode，返回 ``(state, info)``，见 INTERFACE.md §1。

        ``seed`` 非 None 时用它重建 ``np_random``；为 None 时沿用当前状态，
        因此连续 episode 不会重复同一局（INTERFACE.md §7）。
        """
        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        self.direction = INITIAL_DIRECTION
        self.score = 0
        self.steps = 0
        self.done = False

        head = self.config.initial_head
        self._place_snake(self._random_head() if head is None else tuple(head))
        self._spawn_food()

        _, components = self._compute_reward()
        return self._get_state(), self._make_info(components)

    def step(self, action):
        """走一步，返回 5 元组，见 INTERFACE.md §1。"""
        if not self.body:
            raise RuntimeError("请先调用 reset() 再 step()")
        if self.done:
            raise RuntimeError(
                f"episode 已结束（steps={self.steps}, score={self.score}），"
                "请先调用 reset() 再 step()"
            )
        if action not in (STRAIGHT, LEFT, RIGHT):
            raise ValueError(f"非法动作 {action!r}，取值应为 0 / 1 / 2")

        self.steps += 1
        new_direction = self._turn(self.direction, action)
        dr, dc = _MOVE[new_direction]
        head = self.body[0]
        new_head = (head[0] + dr, head[1] + dc)

        terminated = False
        food_reward = death_penalty = 0.0

        if self._is_collision(new_head):
            terminated = True
            death_penalty = DEATH_PENALTY
        else:
            self.direction = new_direction
            ate = new_head == self.food
            self._advance(new_head, grow=ate)
            if ate:
                self.score += 1
                food_reward = FOOD_REWARD
                if len(self.body) == self.n_rows * self.n_cols:
                    # 棋盘被填满，视为胜利而非死亡，见 INTERFACE.md §8
                    terminated = True
                else:
                    self._spawn_food()

        truncated = not terminated and self.steps >= self.config.max_steps_per_episode
        self.done = terminated or truncated

        reward, components = self._compute_reward(food_reward, death_penalty)
        return self._get_state(), reward, terminated, truncated, self._make_info(components)

    def render(self):
        """见 INTERFACE.md §9。``render_mode`` 为 None 时是空操作。"""
        if self.renderer is None:
            return None
        return self.renderer.draw(self.body, self.food, self.score)

    def close(self):
        """释放渲染资源；未使用渲染时为空操作。"""
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None

    # ---- 内部实现 ----

    @staticmethod
    def _turn(direction, action):
        """相对转向后得到的朝向。

        左转 ``(dr, dc) -> (-dc, dr)``、右转 ``(dr, dc) -> (dc, -dr)``，
        两者都与 INTERFACE.md §3 的方向表一致，测试中逐个校验。
        """
        dr, dc = _MOVE[direction]
        if action == LEFT:
            dr, dc = -dc, dr
        elif action == RIGHT:
            dr, dc = dc, -dr
        return _NAME_BY_MOVE[(dr, dc)]

    def _is_collision(self, cell):
        """落点是否撞墙或撞蛇身，见 INTERFACE.md §4。

        蛇尾是唯一例外：它在同一步会腾出格子，落进去合法。"吃到食物时
        尾巴不动"不会破坏这条规则 —— 吃到食物意味着落点等于食物，而食物
        永远生成在空格子，所以此时落点必然不等于蛇尾。
        """
        row, col = cell
        if not (0 <= row < self.n_rows and 0 <= col < self.n_cols):
            return True
        return cell in self.occupied and cell != self.body[-1]

    def _advance(self, new_head, grow):
        """前进一格。``grow`` 为 False 时同时弹出蛇尾，蛇长不变。"""
        self.body.appendleft(new_head)
        self.occupied.add(new_head)
        if not grow:
            self.occupied.discard(self.body.pop())

    def _place_snake(self, head):
        """把蛇摆在 ``head``，蛇身向初始朝向的反方向延伸，见 INTERFACE.md §8。"""
        dr, dc = _MOVE[INITIAL_DIRECTION]
        body = [(head[0] - dr * i, head[1] - dc * i) for i in range(self.config.initial_length)]
        for row, col in body:
            if not (0 <= row < self.n_rows and 0 <= col < self.n_cols):
                raise ValueError(
                    f"initial_head={head} 处放不下长度 {self.config.initial_length} 的蛇身"
                )
        self.body = deque(body)
        self.occupied = set(body)

    def _random_head(self):
        """随机初始蛇头。朝向固定向右，蛇身向左延伸，故 col 下界为 length - 1。"""
        length = self.config.initial_length
        row = int(self.np_random.integers(0, self.n_rows))
        col = int(self.np_random.integers(length - 1, self.n_cols))
        return row, col

    def _spawn_food(self):
        """从空格子中均匀随机选一个放食物，见 INTERFACE.md §8。

        保证食物不会落在蛇身上，无需拒绝采样循环。调用前棋盘必然有空格
        （``reset`` 时蛇长远小于格子数，``step`` 时已在吃食物后判过胜利）。
        """
        empty = [
            (row, col)
            for row in range(self.n_rows)
            for col in range(self.n_cols)
            if (row, col) not in self.occupied
        ]
        self.food = empty[int(self.np_random.integers(len(empty)))]

    def _compute_reward(self, food_reward=0.0, death_penalty=0.0):
        """按 ``reward_mode`` 汇总奖励分项，见 INTERFACE.md §6。

        返回 ``(total, components)``。shaping 项在 Stage 5 实现，此处恒为 0。
        """
        components = {
            "food_reward": food_reward,
            "death_penalty": death_penalty,
            "distance_reward": 0.0,
            "step_reward": 0.0,
        }
        return sum(components.values()), components

    def _make_info(self, components):
        """``reset`` 与 ``step`` 返回同一组 key，见 INTERFACE.md §5。"""
        info = {"score": self.score, "steps": self.steps, "snake_length": len(self.body)}
        info.update(components)
        return info

    def _get_state(self):
        """State V1，11 维 float32，见 INTERFACE.md §4。"""
        state = np.zeros(STATE_DIM, dtype=np.float32)
        row, col = self.body[0]

        for index, action in enumerate((STRAIGHT, LEFT, RIGHT)):
            dr, dc = _MOVE[self._turn(self.direction, action)]
            state[index] = 1.0 if self._is_collision((row + dr, col + dc)) else 0.0

        state[_MOVING_INDEX[self.direction]] = 1.0

        state[7] = 1.0 if self.food[0] < row else 0.0
        state[8] = 1.0 if self.food[0] > row else 0.0
        state[9] = 1.0 if self.food[1] < col else 0.0
        state[10] = 1.0 if self.food[1] > col else 0.0

        return state
