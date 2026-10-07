"""可视化跑一局贪吃蛇。

    python play.py                    # 随机策略
    python play.py --agent human      # 键盘控制
    python play.py --seed 7 --fps 6 --board_size 12

按键（``--agent human``）：``W`` / ``↑`` 直行，``A`` / ``←`` 左转，
``D`` / ``→`` 右转，``Q`` / ``Esc`` 退出。

动作空间是相对的（``docs/INTERFACE.md`` §2），按键表示「相对当前朝向转向」
而不是绝对方位。

本脚本用于环境验证与演示，不承担训练职责（``README.md`` 推荐原则）。
它始终以 ``human`` 模式渲染，传入 ``--render_mode`` 的其它值会被拒绝。
"""
import argparse
import os
import sys
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from common.config import build_parser, config_from_args
from env.random_agent import RandomAgent
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
        if env.renderer is not None and any(e.type == pygame.QUIT for e in pygame.event.get()):
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
    parser.add_argument("--agent", choices=("random", "human"), default="random",
                        help="random = 随机策略，human = 键盘控制")
    parser.add_argument("--fps", type=int, default=10,
                        help="random 模式每秒走几步，默认 10")
    args = build_parser(parser=parser).parse_args(sys.argv[1:] if argv is None else argv)

    config = config_from_args(args)
    if config.render_mode not in (None, "human"):
        parser.error(f"play.py 只支持 human 渲染，收到 --render_mode {config.render_mode}")
    config.render_mode = "human"

    env = SnakeEnv(config)
    agent = None if args.agent == "human" else RandomAgent(env.n_actions, seed=config.seed)
    try:
        run(env, agent, args.fps)
    except KeyboardInterrupt:
        pass
    finally:
        env.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
