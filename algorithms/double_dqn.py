"""Double DQN：Online Network 选动作，Target Network 评估该动作。"""

import torch

from algorithms.dqn import DQNAgent


class DoubleDQNAgent(DQNAgent):
    """复用 DQN 的训练循环，只替换下一状态的 Bellman 目标计算。"""

    @torch.no_grad()
    def _bellman_targets(self, rewards, next_states, terminated):
        next_actions = self.online_net(next_states).argmax(dim=1, keepdim=True)
        next_values = self.target_net(next_states).gather(1, next_actions).squeeze(1)
        next_values = next_values.masked_fill(terminated, 0.0)
        return rewards + self.config.gamma * next_values
