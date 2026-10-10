"""标准 DQN：epsilon-greedy、目标网络、Bellman 更新及 checkpoint。

回放池由训练循环持有；预热时传 update(None)，完成训练环境一步后
调用 on_env_step()。评估只调用 select_action(..., training=False)。
"""

import copy
import dataclasses
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from algorithms.networks import QNetwork
from common.config import Config


class DQNAgent:
    """复用 QNetwork 的 DQN 智能体，接口见 docs/INTERFACE.md 第 12 节。"""

    def __init__(self, state_dim: int, n_actions: int, config: Config):
        self.config = dataclasses.replace(config)
        self._validate_config(self.config)
        self.state_dim = state_dim
        self.n_actions = n_actions
        self.device = torch.device(self.config.device)
        self._rng = np.random.default_rng(self.config.seed)

        # 在 CPU 上可复现地初始化，不改变调用方的 Torch 随机数状态。
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(self.config.seed)
            self.online_net = QNetwork(state_dim, n_actions, self.config.hidden_dim)
        self.online_net.to(self.device)
        self.target_net = copy.deepcopy(self.online_net)
        self.target_net.requires_grad_(False)
        self.target_net.eval()
        self.optimizer = torch.optim.Adam(
            self.online_net.parameters(), lr=self.config.learning_rate
        )
        self.epsilon = self.config.epsilon_start
        self.global_step = 0
        self.update_count = 0

    @staticmethod
    def _validate_config(config: Config):
        if not 0 <= config.gamma <= 1:
            raise ValueError("gamma 必须在 [0, 1] 内")
        if not 0 <= config.epsilon_end <= config.epsilon_start <= 1:
            raise ValueError("epsilon 必须满足 0 <= end <= start <= 1")
        if not 0 < config.epsilon_decay <= 1:
            raise ValueError("epsilon_decay 必须在 (0, 1] 内")
        if not config.learning_rate > 0:
            raise ValueError("learning_rate 必须大于 0")
        if (not isinstance(config.target_update_interval, int)
                or config.target_update_interval <= 0):
            raise ValueError("target_update_interval 必须为正整数")

    def select_action(self, state, training=True) -> int:
        """训练时按 epsilon 随机探索；评估时直接选最大 Q 值的动作。"""
        state = np.asarray(state, dtype=np.float32)
        if state.shape != (self.state_dim,):
            raise ValueError(f"state 形状应为 ({self.state_dim},)，收到 {state.shape}")
        if training and self._rng.random() < self.epsilon:
            return int(self._rng.integers(self.n_actions))
        with torch.no_grad():
            tensor = torch.as_tensor(state, dtype=torch.float32, device=self.device)
            return int(self.online_net(tensor).argmax().item())

    def on_env_step(self, training=True):
        """训练循环在成功完成 env.step 后调用一次，包含结束的最后一步。"""
        if training:
            self.global_step += 1
            self.epsilon = max(
                self.config.epsilon_end, self.epsilon * self.config.epsilon_decay
            )

    def _batch_tensors(self, batch):
        """校验六项数据，防止形状广播或动作类型错误悄悄改变训练目标。"""
        fields = ("states", "actions", "rewards", "next_states", "terminated", "truncated")
        if any(field not in batch for field in fields):
            raise ValueError("batch 必须包含回放池定义的六项数组")
        arrays = {field: np.asarray(batch[field]) for field in fields}
        states = arrays["states"]
        if states.ndim != 2 or states.shape[1] != self.state_dim or len(states) == 0:
            raise ValueError(f"states 应为非空 (batch_size, {self.state_dim}) 数组")
        size = len(states)
        if arrays["next_states"].shape != states.shape:
            raise ValueError("next_states 与 states 的形状必须相同")
        for field in ("actions", "rewards", "terminated", "truncated"):
            if arrays[field].shape != (size,):
                raise ValueError(f"{field} 的形状必须为 ({size},)")
        actions = arrays["actions"]
        if (not np.issubdtype(actions.dtype, np.integer)
                or np.any(actions < 0) or np.any(actions >= self.n_actions)):
            raise ValueError("actions 必须为动作范围内的整数")
        for field in ("terminated", "truncated"):
            if arrays[field].dtype != np.bool_:
                raise ValueError(f"{field} 必须为 bool 数组")
        dtypes = {
            "states": torch.float32, "actions": torch.int64,
            "rewards": torch.float32, "next_states": torch.float32,
            "terminated": torch.bool, "truncated": torch.bool,
        }
        return {
            field: torch.as_tensor(arrays[field], dtype=dtypes[field], device=self.device)
            for field in fields
        }

    @torch.no_grad()
    def _bellman_targets(self, rewards, next_states, terminated):
        """真终止时只有即时奖励；截断时继续估计未来价值。"""
        next_values = self.target_net(next_states).max(dim=1).values
        next_values = next_values.masked_fill(terminated, 0.0)
        return rewards + self.config.gamma * next_values

    def update(self, batch) -> float | None:
        """对采样好的 batch 更新一次；None 表示预热阶段，直接跳过。"""
        if batch is None:
            return None
        tensors = self._batch_tensors(batch)
        self.online_net.train()
        predictions = self.online_net(tensors["states"]).gather(
            1, tensors["actions"].unsqueeze(1)
        ).squeeze(1)
        targets = self._bellman_targets(
            tensors["rewards"], tensors["next_states"], tensors["terminated"]
        )
        # Smooth L1 在误差较大时比平方误差温和；目标分支不计算梯度。
        loss = F.smooth_l1_loss(predictions, targets)
        if not torch.isfinite(loss):
            raise FloatingPointError("DQN loss 不是有限值，请检查 batch 和网络参数")
        self.optimizer.zero_grad()
        loss.backward()
        if any(not torch.isfinite(parameter.grad).all()
               for parameter in self.online_net.parameters() if parameter.grad is not None):
            self.optimizer.zero_grad()
            raise FloatingPointError("DQN 梯度不是有限值，本次未更新参数")
        self.optimizer.step()
        self.update_count += 1
        if self.update_count % self.config.target_update_interval == 0:
            self.target_net.load_state_dict(self.online_net.state_dict())
        return float(loss.detach().item())

    def save(self, path):
        """保存智能体状态；回放池和环境状态由调用方单独管理。"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "format_version": 1,
            "state_dim": self.state_dim,
            "n_actions": self.n_actions,
            "config": dataclasses.asdict(self.config),
            "online_net": self.online_net.state_dict(),
            "target_net": self.target_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "global_step": self.global_step,
            "update_count": self.update_count,
            "rng_state": self._rng.bit_generator.state,
        }, path)

    def load(self, path):
        """加载匹配结构的 checkpoint，使用当前智能体配置的设备。"""
        checkpoint = torch.load(path, map_location=self.device, weights_only=True)
        if (checkpoint["format_version"] != 1
                or checkpoint["state_dim"] != self.state_dim
                or checkpoint["n_actions"] != self.n_actions
                or checkpoint["config"]["hidden_dim"] != self.config.hidden_dim):
            raise ValueError("checkpoint 的格式或网络维度与当前智能体不匹配")
        restored_config = Config(**checkpoint["config"])
        restored_config.device = str(self.device)
        self._validate_config(restored_config)
        self.online_net.load_state_dict(checkpoint["online_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.config = restored_config
        self.epsilon = float(checkpoint["epsilon"])
        self.global_step = int(checkpoint["global_step"])
        self.update_count = int(checkpoint["update_count"])
        self._rng.bit_generator.state = checkpoint["rng_state"]
        self.online_net.train()
        self.target_net.eval()
