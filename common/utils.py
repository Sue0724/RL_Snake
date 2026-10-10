"""训练入口使用的随机种子设置。"""

import random

import numpy as np
import torch


def set_global_seed(seed: int) -> None:
    """设置全局 RNG；环境和回放池仍需各自接收同一个 seed。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

