"""经验回放池：保存六项转移数据，随机采样 NumPy batch。

回放池由训练循环持有，不负责网络更新或 min_buffer_size 预热判断。
环形存储在容量满时覆盖最旧记录；采样使用独立随机数生成器。
"""

import numpy as np


class ReplayBuffer:
    """固定容量、均匀无放回采样的经验回放池。

    ``add`` 保存状态的副本，防止调用方后续改动污染历史记录。
    ``sample`` 返回 states/actions/rewards/next_states/terminated/truncated
    六个数组；批量形状及类型见 docs/INTERFACE.md 第 12 节。
    """

    def __init__(self, capacity: int, seed: int | None = None):
        if not isinstance(capacity, (int, np.integer)) or capacity <= 0:
            raise ValueError("capacity 必须为正整数")
        self.capacity = int(capacity)
        self._rng = np.random.default_rng(seed)
        self._transitions = []
        self._next_index = 0
        self._state_dim = None

    def __len__(self) -> int:
        return len(self._transitions)

    def add(self, state, action, reward, next_state, terminated, truncated):
        """保存一次 env.step 的经历，保留两个独立结束标记。"""
        state = np.array(state, dtype=np.float32, copy=True)
        next_state = np.array(next_state, dtype=np.float32, copy=True)
        if state.ndim != 1 or state.size == 0 or next_state.shape != state.shape:
            raise ValueError("state 与 next_state 必须为相同长度的非空一维向量")
        if self._state_dim is not None and state.size != self._state_dim:
            raise ValueError(f"同一回放池的状态维度必须保持为 {self._state_dim}")
        if not isinstance(action, (int, np.integer)) or action < 0:
            raise ValueError("action 必须为非负整数")

        transition = (
            state, int(action), float(reward), next_state,
            bool(terminated), bool(truncated),
        )
        self._state_dim = state.size
        if len(self) < self.capacity:
            self._transitions.append(transition)
        else:
            self._transitions[self._next_index] = transition
        self._next_index = (self._next_index + 1) % self.capacity

    def sample(self, batch_size: int) -> dict[str, np.ndarray]:
        """随机抽取 batch_size 条不同经历；不足时明确报错。"""
        if not isinstance(batch_size, (int, np.integer)) or batch_size <= 0:
            raise ValueError("batch_size 必须为正整数")
        if batch_size > len(self):
            raise ValueError(f"需要 {batch_size} 条经历，回放池当前只有 {len(self)} 条")

        indices = self._rng.choice(len(self), size=batch_size, replace=False)
        states, actions, rewards, next_states, terminated, truncated = zip(
            *(self._transitions[int(index)] for index in indices)
        )
        return {
            "states": np.stack(states),
            "actions": np.asarray(actions, dtype=np.int64),
            "rewards": np.asarray(rewards, dtype=np.float32),
            "next_states": np.stack(next_states),
            "terminated": np.asarray(terminated, dtype=np.bool_),
            "truncated": np.asarray(truncated, dtype=np.bool_),
        }
