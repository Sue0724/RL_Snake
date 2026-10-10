"""可视化跑一局贪吃蛇。

    python play.py                    # 随机策略
    python play.py --agent human      # 键盘控制
    python play.py --agent model --checkpoint path/to/checkpoint.pt
    python play.py --seed 7 --fps 6 --board_size 12

按键（``--agent human``）：``W`` / ``↑`` 直行，``A`` / ``←`` 左转，
``D`` / ``→`` 右转，``Q`` / ``Esc`` 退出。

动作空间是相对的（``docs/INTERFACE.md`` §2），按键表示「相对当前朝向转向」
而不是绝对方位。

本脚本用于环境验证与演示，不承担训练职责（``README.md`` 推荐原则）。
它始终以 ``human`` 模式渲染，传入 ``--render_mode`` 的其它值会被拒绝。

演示脚本不套用 ``Config.seed`` 的默认值：不传 ``--seed`` 时随机取一个并打印，
否则每次跑出同一条轨迹，演示和人工验证都失去意义。``train.py`` / ``evaluate.py``
等实验脚本不受此影响，仍严格受 ``Config.seed`` 控制。

模型模式复用 algorithms.factory.load_agent，环境/网络参数来自 checkpoint。
只允许指定 seed、device、render_mode 与 fps；选择动作始终 training=False，
不更新网络、不写回放池、不保存模型。
"""
import argparse
import dataclasses
import os
import random
import sys
import time
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from common.config import build_parser, config_from_args
from algorithms.factory import create_agent, load_agent
from common.checkpoint import CheckpointError
from env.snake_env import LEFT, RIGHT, STRAIGHT, SnakeEnv

KEYS = {
    pygame.K_w: STRAIGHT,
    pygame.K_UP: STRAIGHT,
    pygame.K_a: LEFT,
    pygame.K_LEFT: LEFT,
    pygame.K_d: RIGHT,
    pygame.K_RIGHT: RIGHT,
}
QUIT_KEYS = (pygame.K_q, pygame.K_ESCAPE)


def _positive_fps(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("fps 必须为正整数")
    return value


def _pick_seed(seed):
    """选定本次运行的种子。

    传了 ``--seed`` 原样使用，用于复现某一次运行；没传则随机取一个，
    避免每次演示都跑出同一条轨迹。判据是 ``is None`` 而不是真值判断，
    这样 ``--seed 0`` 也能被当成显式取值。
    """
    return seed if seed is not None else random.randrange(1_000_000)


def _report(info, terminated):
    reason = "撞墙或撞蛇" if terminated else "达到步数上限"
    print(f"episode 结束（{reason}）：score={info['score']}  steps={info['steps']}")


def _wait_for_action():
    """阻塞等待一次按键。返回动作；用户要求退出时返回 None。"""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key in QUIT_KEYS:
                    return None
                if event.key in KEYS:
                    return KEYS[event.key]
        pygame.time.wait(20)


def _run_human(env):
    env.reset()
    env.render()
    print("窗口已打开：W/↑ 直行，A/← 左转，D/→ 右转，Q/Esc 退出")
    while True:
        action = _wait_for_action()
        if action is None:
            return False
        _, _, terminated, truncated, info = env.step(action)
        env.render()
        if terminated or truncated:
            _report(info, terminated)
            return True


def _run_agent(env, agent, fps):
    state, _ = env.reset()
    env.render()
    while True:
        time.sleep(1 / fps)
        if env.renderer is not None and any(
            e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key in QUIT_KEYS)
            for e in pygame.event.get()
        ):
            return False
        state, _, terminated, truncated, info = env.step(agent.select_action(state, training=False))
        env.render()
        if terminated or truncated:
            _report(info, terminated)
            return True


def run(env, agent, fps):
    """跑一局。返回 True 表示正常结束，False 表示用户中途退出。

    ``agent`` 为 None 时进入键盘控制模式。
    """
    if agent is None:
        return _run_human(env)
    return _run_agent(env, agent, fps)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="play.py", description="Snake-RL 可视化跑一局")
    parser.add_argument("--agent", choices=("random", "human", "model"), default="random",
                        help="random = 随机策略，human = 键盘控制，model = 已训练模型")
    parser.add_argument("--checkpoint", help="model 模式必需：checkpoint.pt 路径")
    parser.add_argument("--fps", type=_positive_fps, default=10,
                        help="random / model 模式每秒走几步，默认 10")
    args = build_parser(parser=parser).parse_args(sys.argv[1:] if argv is None else argv)

    config = config_from_args(args)
    if config.render_mode not in (None, "human"):
        parser.error(f"play.py 只支持 human 渲染，收到 --render_mode {config.render_mode}")
    if args.seed is not None and not 0 <= args.seed < 2 ** 32:
        parser.error("seed 必须在 [0, 2**32) 内")
    if args.agent == "model":
        if not args.checkpoint:
            parser.error("--agent model 必须提供 --checkpoint")
        forbidden = [
            f"--{field.name}" for field in dataclasses.fields(config)
            if field.name not in ("seed", "device", "render_mode")
            and getattr(args, field.name) is not None
        ]
        if forbidden:
            parser.error("模型模式的环境/网络/训练参数来自 checkpoint，请移除：" + ", ".join(forbidden))
        try:
            agent, config = load_agent(args.checkpoint, device=config.device, render_mode="human")
        except CheckpointError as error:
            parser.error(str(error))
        print(f"模型已加载：{Path(args.checkpoint).expanduser().resolve()} "
              f"（algorithm={config.algorithm}，训练seed={config.seed}）")
    elif args.checkpoint:
        parser.error("--checkpoint 只能用于 --agent model")
    config.render_mode = "human"

    config.seed = _pick_seed(args.seed)
    if args.seed is None:
        print(f"本次随机种子：{config.seed}（加 --seed {config.seed} 可复现本次）")

    env = SnakeEnv(config)
    try:
        if args.agent != "model":
            agent = None if args.agent == "human" else create_agent(
                env.state_dim, env.n_actions, dataclasses.replace(config, algorithm="random")
            )
        run(env, agent, args.fps)
    except KeyboardInterrupt:
        pass
    finally:
        env.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
