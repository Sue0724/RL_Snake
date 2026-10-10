"""每次训练独立保存配置、逐局指标及训练摘要。"""

import csv
import dataclasses
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import numpy as np


METRIC_FIELDS = (
    "run_id", "algorithm", "seed", "state_mode", "reward_mode",
    "episode", "global_step", "episode_return", "score", "episode_length",
    "epsilon", "loss", "update_count", "terminated", "truncated",
    "episode_complete", "wall_clock_time",
)


def write_json(path, data):
    """先写临时文件再替换，避免中断时破坏上一份 JSON。"""
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


class RunLogger:
    def __init__(self, config, output_dir, experiment, run_settings):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.run_id = (
            f"{experiment}_{config.algorithm}_state{config.state_mode}_"
            f"{config.reward_mode}_seed{config.seed}_{timestamp}_{uuid4().hex[:8]}"
        )
        self.run_dir = Path(output_dir).expanduser().resolve() / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.identity = {
            "run_id": self.run_id, "algorithm": config.algorithm,
            "seed": config.seed, "state_mode": config.state_mode,
            "reward_mode": config.reward_mode,
        }
        self.run_settings = run_settings
        self.completed = []
        write_json(self.run_dir / "config.json", dataclasses.asdict(config))
        self._file = (self.run_dir / "metrics.csv").open(
            "w", encoding="utf-8", newline=""
        )
        self._writer = csv.DictWriter(self._file, fieldnames=METRIC_FIELDS)
        self._writer.writeheader()
        self._file.flush()

    def log_episode(self, metrics):
        """无更新时 loss 留空；步数预算导致的未完成局也明确标识。"""
        row = {**self.identity, **metrics}
        self._writer.writerow(row)
        self._file.flush()
        if row["episode_complete"]:
            self.completed.append(row)

    def save_summary(self, status, agent, elapsed, error=None):
        rows = self.completed
        scores = [row["score"] for row in rows]
        summary = {
            **self.identity, "status": status, "metrics_scope": "training",
            "run_settings": self.run_settings,
            "completed_episodes": len(rows), "global_step": agent.global_step,
            "update_count": agent.update_count, "epsilon": agent.epsilon,
            "wall_clock_time": elapsed,
            "mean_score": float(np.mean(scores)) if rows else None,
            "std_score": float(np.std(scores)) if rows else None,
            "max_score": max(scores) if rows else None,
            "mean_return": float(np.mean([r["episode_return"] for r in rows])) if rows else None,
            "mean_episode_length": float(np.mean([r["episode_length"] for r in rows])) if rows else None,
            "error": error,
        }
        write_json(self.run_dir / "summary.json", summary)

    def close(self):
        self._file.close()

