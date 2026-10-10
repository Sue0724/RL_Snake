"""DQN 基线训练入口：无渲染交互、经验回放、更新及逐局日志。

例：python3 train.py --num_episodes 100 --seed 42
    python3 train.py --total_steps 50000 --seed 42
"""

import argparse
import re
import time
from pathlib import Path

import torch

from algorithms.factory import create_agent, validate_agent_config
from common.config import build_parser, config_from_args
from common.metrics import RunLogger
from common.replay_buffer import ReplayBuffer
from common.utils import set_global_seed
from env.snake_env import SnakeEnv


def positive_int(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("必须为正整数")
    return value


def validate_training_config(config):
    validate_agent_config(config, training=True)
    if config.render_mode is not None:
        raise ValueError("训练入口采用无渲染模式，请不要传 --render_mode")
    for name in ("num_episodes", "max_steps_per_episode", "batch_size", "buffer_size", "min_buffer_size"):
        if getattr(config, name) <= 0:
            raise ValueError(f"{name} 必须为正整数")
    if config.buffer_size < max(config.min_buffer_size, config.batch_size):
        raise ValueError("buffer_size 必须不小于 min_buffer_size 和 batch_size，否则无法开始更新")
    if not 0 <= config.seed < 2 ** 32:
        raise ValueError("seed 必须在 [0, 2**32) 内")


def save_checkpoint(agent, run_dir):
    """同一次 run 的 checkpoint 为最新快照；其他 run 的文件不受影响。"""
    temporary = Path(run_dir) / "checkpoint.pt.tmp"
    agent.save(temporary)
    temporary.replace(Path(run_dir) / "checkpoint.pt")


def train(config, *, output_dir="results/logs", experiment="debug_baseline",
          total_steps=None, log_every=10, checkpoint_every=100, torch_threads=1):
    validate_training_config(config)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", experiment):
        raise ValueError("experiment 只能包含英文字母、数字、下划线和连字符")
    for name, value in (("log_every", log_every), ("checkpoint_every", checkpoint_every),
                        ("torch_threads", torch_threads)):
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} 必须为正整数")
    if total_steps is not None and (not isinstance(total_steps, int) or total_steps <= 0):
        raise ValueError("total_steps 必须为正整数或 None")

    # 小型 MLP 默认使用一个 CPU 计算线程；此运行设置也写入摘要。
    torch.set_num_threads(torch_threads)
    set_global_seed(config.seed)
    env = SnakeEnv(config)
    logger = None
    started = time.perf_counter()
    try:
        agent = create_agent(env.state_dim, env.n_actions, config, training=True)
        buffer = ReplayBuffer(config.buffer_size, seed=config.seed)
        # 只在第一局显式播种，之后 reset() 延续环境 RNG。
        state, _ = env.reset(seed=config.seed)
        settings = {
            "budget_type": "environment_steps" if total_steps is not None else "episodes",
            "total_steps": total_steps, "log_every": log_every,
            "checkpoint_every": checkpoint_every, "torch_threads": torch_threads,
            "experiment": experiment,
        }
        logger = RunLogger(config, output_dir, experiment, settings)
        print(f"输出目录：{logger.run_dir}", flush=True)
        logger.save_summary("running", agent, 0.0)
        save_checkpoint(agent, logger.run_dir)
        episode = 1
        episode_return = 0.0
        episode_length = 0
        loss_sum = 0.0
        loss_count = 0
        info = {"score": 0}
        terminated = truncated = False

        def log_current_episode(complete):
            logger.log_episode({
                "episode": episode, "global_step": agent.global_step,
                "episode_return": episode_return, "score": info["score"],
                "episode_length": episode_length, "epsilon": agent.epsilon,
                "loss": loss_sum / loss_count if loss_count else None,
                "update_count": agent.update_count, "terminated": terminated,
                "truncated": truncated, "episode_complete": complete,
                "wall_clock_time": time.perf_counter() - started,
            })

        status = "completed"
        try:
            while True:
                action = agent.select_action(state, training=True)
                next_state, reward, terminated, truncated, info = env.step(action)
                buffer.add(state, action, reward, next_state, terminated, truncated)
                agent.on_env_step()
                state = next_state
                episode_return += reward
                episode_length += 1

                ready = len(buffer) >= max(config.min_buffer_size, config.batch_size)
                batch = buffer.sample(config.batch_size) if ready else None
                loss = agent.update(batch)
                if loss is not None:
                    loss_sum += loss
                    loss_count += 1

                complete = terminated or truncated
                budget_reached = (
                    agent.global_step >= total_steps if total_steps is not None
                    else complete and episode >= config.num_episodes
                )
                if complete or budget_reached:
                    log_current_episode(complete)
                    # 已写入日志，防止 Ctrl+C 保存时重复记录这一局。
                    episode_length = 0
                    if episode == 1 or episode % log_every == 0 or budget_reached:
                        loss_text = f"{loss_sum / loss_count:.4f}" if loss_count else "预热"
                        print(
                            f"episode={episode} step={agent.global_step} score={info['score']} "
                            f"return={episode_return:.1f} epsilon={agent.epsilon:.4f} "
                            f"loss={loss_text} updates={agent.update_count}", flush=True,
                        )
                    if complete and episode % checkpoint_every == 0:
                        save_checkpoint(agent, logger.run_dir)
                        logger.save_summary("running", agent, time.perf_counter() - started)
                    if budget_reached:
                        break
                    state, _ = env.reset()
                    episode += 1
                    episode_return = loss_sum = 0.0
                    loss_count = 0
                    terminated = truncated = False
        except KeyboardInterrupt:
            status = "interrupted"
            if episode_length:
                log_current_episode(terminated or truncated)
            print("训练已中断，正在保存当前模型和摘要。", flush=True)
        except Exception as error:
            logger.save_summary("failed", agent, time.perf_counter() - started,
                                error=f"{type(error).__name__}: {error}")
            # 失败时保留此前快照，避免覆盖成损坏的模型。
            raise

        save_checkpoint(agent, logger.run_dir)
        logger.save_summary(status, agent, time.perf_counter() - started)
        print(f"训练状态：{status}；模型：{logger.run_dir / 'checkpoint.pt'}", flush=True)
        return logger.run_dir, status
    finally:
        if logger is not None:
            logger.close()
        env.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Snake-RL DQN 基线训练与日志")
    parser.add_argument("--output_dir", default="results/logs", help="训练输出根目录")
    parser.add_argument("--experiment", default="debug_baseline", help="run 名前缀；默认标记为调试")
    parser.add_argument("--total_steps", type=positive_int, help="精确环境步预算；传入后覆盖 num_episodes")
    parser.add_argument("--log_every", type=positive_int, default=10, help="终端每多少局打印一次，CSV 每局写入")
    parser.add_argument("--checkpoint_every", type=positive_int, default=100, help="每多少完整局保存快照，结束时也保存")
    parser.add_argument("--torch_threads", type=positive_int, default=1, help="Torch CPU 计算线程数")
    args = build_parser(parser=parser).parse_args(argv)
    config = config_from_args(args)
    # 在创建输出目录前报告常见配置错误。
    try:
        validate_training_config(config)
    except ValueError as error:
        parser.error(str(error))
    _, status = train(
        config, output_dir=args.output_dir, experiment=args.experiment,
        total_steps=args.total_steps, log_every=args.log_every,
        checkpoint_every=args.checkpoint_every, torch_threads=args.torch_threads,
    )
    return 130 if status == "interrupted" else 0


if __name__ == "__main__":
    raise SystemExit(main())
