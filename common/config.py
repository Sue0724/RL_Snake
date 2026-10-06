"""统一配置：所有超参数集中定义，命令行可覆盖。

用法：

    from common.config import Config, parse_args

    cfg = parse_args()      # 命令行覆盖，未传入的字段用默认值
    cfg = Config()          # 全部默认值

训练脚本开头调用一次 ``parse_args()``，并把 ``cfg.seed`` 传给
``env.reset(seed=cfg.seed)``（见 ``docs/INTERFACE.md`` §7）。

字段清单依据 ``docs/AI_DEVELOPMENT_RULES.md`` §12 与 ``docs/INTERFACE.md`` §10。
新增字段只需在 ``Config`` 中加一行，命令行参数自动生成。

不用 YAML 配置文件：``EXPERIMENT_PROTOCOL.md`` 第十节要求的 ``config.json``
是每个 run 的输出记录，不是输入，因此不需要第二份配置来源。
配置存档用 ``dataclasses.asdict(cfg)`` 直接写入 JSON（见 ``docs/INTERFACE.md`` §11）。
"""
import argparse
import dataclasses
import types
from dataclasses import dataclass


@dataclass
class Config:
    # ---- 环境，见 docs/INTERFACE.md §10 ----
    board_size: int = 10
    initial_length: int = 3
    max_steps_per_episode: int = 500
    render_mode: str | None = None

    # ---- 实验标识，见 docs/AI_DEVELOPMENT_RULES.md §12 ----
    seed: int = 42
    device: str = "cpu"
    algorithm: str = "dqn"
    state_mode: str = "v1"
    reward_mode: str = "sparse"

    # ---- 算法，见 docs/AI_DEVELOPMENT_RULES.md §12 ----
    gamma: float = 0.99
    learning_rate: float = 1e-3
    batch_size: int = 64
    buffer_size: int = 100_000
    min_buffer_size: int = 1_000
    target_update_interval: int = 1_000
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.995
    num_episodes: int = 1_000
    hidden_dim: int = 128


def _arg_type(field: dataclasses.Field) -> type:
    """从字段类型注解推断 argparse 的 ``type``。

    ``str | None`` 这类可选类型取其非 None 分支。
    """
    field_type = field.type
    if isinstance(field_type, types.UnionType):
        field_type = next(
            arg for arg in field_type.__args__ if arg is not type(None)
        )
    return field_type


def parse_args(argv: list[str] | None = None) -> Config:
    """解析命令行并返回配置。

    只覆盖显式传入的参数，未传入的保持 ``Config`` 的默认值。
    记录每次实验用的 ``config.json`` 时，对返回的 ``Config`` 调用
    ``dataclasses.asdict()`` 即可。
    """
    parser = argparse.ArgumentParser(description="Snake-RL 配置")
    for field in dataclasses.fields(Config):
        parser.add_argument(
            f"--{field.name}",
            type=_arg_type(field),
            default=None,
            help=f"默认 {field.default!r}",
        )

    args = parser.parse_args(argv)

    config = Config()
    for field in dataclasses.fields(Config):
        value = getattr(args, field.name)
        if value is not None:
            setattr(config, field.name, value)
    return config
