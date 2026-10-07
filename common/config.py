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
import typing
from dataclasses import dataclass


@dataclass
class Config:
    # ---- 环境，见 docs/INTERFACE.md §10 ----
    board_size: int = 10
    initial_length: int = 3
    max_steps_per_episode: int = 500
    initial_head: tuple[int, int] | None = None
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


def _parse_int_pair(text: str) -> tuple[int, int]:
    """解析 ``--initial_head 4,6`` 形式的坐标。"""
    row, _, col = text.partition(",")
    if not col:
        raise argparse.ArgumentTypeError(f"应为 'row,col' 形式，收到 {text!r}")
    return int(row), int(col)


def _arg_type(field: dataclasses.Field):
    """从字段类型注解推断 argparse 的 ``type``。

    ``str | None`` 这类可选类型取其非 None 分支；``tuple[int, int]``
    这类无法直接实例化的类型改用专门的解析函数。
    """
    field_type = field.type
    if isinstance(field_type, types.UnionType):
        field_type = next(
            arg for arg in field_type.__args__ if arg is not type(None)
        )
    if typing.get_origin(field_type) is tuple:
        return _parse_int_pair
    return field_type


def build_parser(description: str = "Snake-RL 配置", parser=None):
    """构造带全部配置字段的 ``ArgumentParser``。

    ``parser`` 非 None 时在其上追加，用于 ``play.py`` 这类还有自有参数的
    入口脚本：先建 parser、加自己的参数，再交给本函数，这样 ``-h`` 能
    一次列全所有可传参数。
    """
    if parser is None:
        parser = argparse.ArgumentParser(description=description)
    for field in dataclasses.fields(Config):
        parser.add_argument(
            f"--{field.name}",
            type=_arg_type(field),
            default=None,
            help=f"默认 {field.default!r}",
        )
    return parser


def config_from_args(args) -> Config:
    """从已解析的 namespace 取出配置。

    只覆盖显式传入的字段，未传入的保持 ``Config`` 的默认值。
    记录每次实验用的 ``config.json`` 时，对返回的 ``Config`` 调用
    ``dataclasses.asdict()`` 即可。
    """
    config = Config()
    for field in dataclasses.fields(Config):
        value = getattr(args, field.name)
        if value is not None:
            setattr(config, field.name, value)
    return config


def parse_args(argv: list[str] | None = None) -> Config:
    """解析命令行并返回配置。配置之外的参数请用 ``build_parser`` + ``config_from_args``。"""
    return config_from_args(build_parser().parse_args(argv))
