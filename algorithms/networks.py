"""DQN 基线的 Q 网络：状态向量 -> 每个动作的预期累计奖励。

输入、输出维度由环境提供，隐藏层宽度由 Config.hidden_dim 提供。
网络只做前向计算；选动作、目标网络和训练更新由 DQNAgent 实现。
"""

import torch
from torch import nn


class QNetwork(nn.Module):
    """两层隐藏层的 MLP，输出未经归一化的 Q 值。

    接收 float32 Tensor，形状为 (state_dim,) 或 (batch_size, state_dim)，
    分别返回 (n_actions,) 或 (batch_size, n_actions)。
    """

    def __init__(self, state_dim: int, n_actions: int, hidden_dim: int):
        super().__init__()
        if state_dim <= 0 or n_actions <= 0 or hidden_dim <= 0:
            raise ValueError("state_dim、n_actions 和 hidden_dim 必须为正整数")

        self.state_dim = state_dim
        self.n_actions = n_actions
        self.layers = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_actions),
        )

    def forward(self, states: torch.Tensor) -> torch.Tensor:
        """计算每个动作的 Q 值；输出层不使用 softmax。"""
        if states.ndim not in (1, 2) or states.shape[-1] != self.state_dim:
            raise ValueError(
                f"输入形状应为 ({self.state_dim},) 或 (batch_size, {self.state_dim})，"
                f"收到 {tuple(states.shape)}"
            )
        return self.layers(states)


class DuelingQNetwork(nn.Module):
    """共享特征层加 Value / Advantage 双流的 Dueling Q 网络。"""

    def __init__(self, state_dim: int, n_actions: int, hidden_dim: int):
        super().__init__()
        if state_dim <= 0 or n_actions <= 0 or hidden_dim <= 0:
            raise ValueError("state_dim、n_actions 和 hidden_dim 必须为正整数")

        self.state_dim = state_dim
        self.n_actions = n_actions
        self.features = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.value = nn.Linear(hidden_dim, 1)
        self.advantage = nn.Linear(hidden_dim, n_actions)

    def forward(self, states: torch.Tensor) -> torch.Tensor:
        """按 Q=V+(A-mean(A)) 聚合；输出形状与 QNetwork 一致。"""
        if states.ndim not in (1, 2) or states.shape[-1] != self.state_dim:
            raise ValueError(
                f"输入形状应为 ({self.state_dim},) 或 (batch_size, {self.state_dim})，"
                f"收到 {tuple(states.shape)}"
            )
        features = self.features(states)
        value = self.value(features)
        advantage = self.advantage(features)
        return value + advantage - advantage.mean(dim=-1, keepdim=True)
