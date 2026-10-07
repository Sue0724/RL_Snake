"""Stage 0 自检：验证依赖、包结构、配置系统与项目目录可用。

只检查工程地基，不涉及环境与算法逻辑（它们在 Stage 0 尚不存在）。

    python smoke_test.py

在任意目录运行均可，全部通过返回 0，任一失败返回 1。
"""
import os
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import dataclasses  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS = []


def check_dependencies():
    """第三方依赖可导入。"""
    import matplotlib
    import numpy
    import pandas
    import pygame
    import torch

    return (
        f"numpy {numpy.__version__} / torch {torch.__version__} / "
        f"pygame {pygame.version.ver} / matplotlib {matplotlib.__version__} / "
        f"pandas {pandas.__version__}"
    )


def check_packages():
    """项目包结构完整，可导入。"""
    import algorithms  # noqa: F401
    import common  # noqa: F401
    import env  # noqa: F401
    import experiments  # noqa: F401

    return "env / algorithms / common / experiments"


def check_config_defaults():
    """Config 默认值可用且字段数正确。"""
    from common.config import Config

    config = Config()
    n_fields = len(dataclasses.fields(Config))
    return f"{n_fields} 个字段，board_size={config.board_size} seed={config.seed}"


def check_config_override():
    """命令行覆盖只影响显式传入的字段。"""
    from common.config import Config, parse_args

    config = parse_args(["--seed", "43", "--learning_rate", "0.0005"])
    assert config.seed == 43, "seed 未被覆盖"
    assert config.learning_rate == 0.0005, "learning_rate 未被覆盖"
    assert config.board_size == 10, "未传入的字段被意外修改"
    assert Config().seed == 42, "默认值被污染"
    return "覆盖与默认值隔离正常"


def check_config_serializable():
    """配置可序列化为 config.json。"""
    from common.config import Config

    payload = json.dumps(dataclasses.asdict(Config()))
    return f"config.json 可序列化（{len(payload)} 字节）"


def check_directories():
    """项目目录存在。"""
    names = ["env", "algorithms", "common", "experiments", "docs"]
    missing = [name for name in names if not (ROOT / name).is_dir()]
    assert not missing, f"缺少目录 {missing}"
    return "env / algorithms / common / experiments / docs"


CHECKS = [
    ("第三方依赖", check_dependencies),
    ("包结构", check_packages),
    ("配置默认值", check_config_defaults),
    ("配置覆盖", check_config_override),
    ("配置存档", check_config_serializable),
    ("项目目录", check_directories),
]


def main():
    for name, func in CHECKS:
        try:
            RESULTS.append((name, True, func()))
        except Exception as exc:  # noqa: BLE001
            RESULTS.append((name, False, f"{type(exc).__name__}: {exc}"))

    print(f"Snake-RL Stage 0 自检  ({ROOT})")
    print("-" * 68)
    for name, passed, detail in RESULTS:
        print(f"[{'PASS' if passed else 'FAIL'}] {name:<10} {detail}")
    print("-" * 68)

    failed = sum(1 for _, passed, _ in RESULTS if not passed)
    print(f"{len(RESULTS) - failed}/{len(RESULTS)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
