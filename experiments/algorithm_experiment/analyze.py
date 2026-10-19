"""Audit algorithm artifacts and export report-ready tables without training."""

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, pstdev
from uuid import uuid4

from common.checkpoint import read_checkpoint
from common.metrics import write_json


COMPONENTS = ("food_reward", "death_penalty", "distance_reward", "step_reward")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def close(actual, expected):
    return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-7)


def analyze_algorithm_experiment(comparison_path):
    path = Path(comparison_path).resolve()
    comparison = read_json(path)
    require(comparison["status"] == "completed", "Experiment is not completed")
    protocol = comparison["protocol"]
    root = path.parent
    expected_pairs = {(name, seed) for name in protocol["algorithms"] for seed in protocol["seeds"]}
    require(len(comparison["training_runs"]) == len(expected_pairs), "Training grid size mismatch")
    configs, training, known_checkpoints = [], [], {}
    pairs = set()
    for run in comparison["training_runs"]:
        pair = run["algorithm"], run["seed"]
        require(pair not in pairs, "Duplicate training run")
        pairs.add(pair)
        directory = root / run["run_dir"]
        config = read_json(directory / "config.json")
        summary = read_json(directory / "summary.json")
        rows = read_rows(directory / "metrics.csv")
        checkpoint_path = root / run["checkpoint"]
        checkpoint = read_checkpoint(checkpoint_path)
        require(config == checkpoint["config"], "Checkpoint config mismatch")
        require((config["algorithm"], config["seed"]) == pair, "Run identity mismatch")
        configs.append({k: v for k, v in config.items() if k not in ("algorithm", "seed")})
        require(summary["status"] == run["status"] == "completed", "Incomplete training")
        budget = protocol["total_steps"]
        updates = max(0, budget - max(config["min_buffer_size"], config["batch_size"]) + 1)
        require(summary["global_step"] == run["global_step"] == checkpoint["global_step"] == budget,
                "Training budget mismatch")
        require(summary["update_count"] == run["update_count"] == checkpoint["update_count"] == updates,
                "Update budget mismatch")
        require(sum(int(row["episode_length"]) for row in rows) == budget, "CSV budget mismatch")
        cumulative = 0
        for row in rows:
            cumulative += int(row["episode_length"])
            require(int(row["global_step"]) == cumulative, "CSV cumulative steps mismatch")
            require((row["algorithm"], int(row["seed"])) == pair, "CSV training identity mismatch")
            expected = max(config["epsilon_end"], config["epsilon_start"] *
                           config["epsilon_decay"] ** int(row["global_step"]))
            require(close(float(row["epsilon"]), expected), "Epsilon schedule mismatch")
            require(not row["loss"] or math.isfinite(float(row["loss"])), "Non-finite loss")
            require(close(sum(float(row[key]) for key in COMPONENTS), float(row["episode_return"])),
                    "Training reward accounting mismatch")
        require(close(summary["epsilon"], float(rows[-1]["epsilon"])), "Final epsilon mismatch")
        require(close(run["final_epsilon"], checkpoint["epsilon"]) and
                close(summary["epsilon"], checkpoint["epsilon"]), "Checkpoint epsilon mismatch")
        fingerprint = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
        known_checkpoints[str(checkpoint_path.resolve())] = pair
        training.append({"algorithm": pair[0], "training_seed": pair[1], "records": len(rows),
                         "parameter_count": sum(tensor.numel() for tensor in checkpoint["online_net"].values()),
                         "wall_clock_time": summary["wall_clock_time"], "checkpoint": str(checkpoint_path),
                         "sha256": fingerprint})
    require(pairs == expected_pairs, "Training grid mismatch")
    require(all(config == configs[0] for config in configs), "Non-algorithm configuration changed")

    records, groups = [], {}
    for split, key, seed_key in (("development", "evaluation_dir", "eval_seed"),
                                 ("holdout", "holdout_evaluation_dir", "holdout_seed")):
        if key not in comparison:
            continue
        directory = root / comparison[key]
        summary = read_json(directory / "summary.json")
        settings = read_json(directory / "config.json")
        p = settings["protocol"]
        require(summary["status"] == "completed", "Incomplete evaluation")
        require(all(p[key] is False for key in ("exploration", "network_update", "replay_write")),
                "Evaluation training flags enabled")
        expected_seeds = list(range(protocol[seed_key], protocol[seed_key] + protocol["num_episodes"]))
        require(p["evaluation_seeds"] == expected_seeds, "Evaluation seeds mismatch")
        rows = read_rows(directory / "metrics.csv")
        models = summary["models"]
        require(len(models) == len(expected_pairs) + 1, "Evaluation model count mismatch")
        require(len(rows) == len(models) * protocol["num_episodes"], "Evaluation row count mismatch")
        require(len({model["model_id"] for model in models}) == len(models), "Duplicate evaluation model")
        evaluated_pairs = set()
        for model in models:
            selected = [row for row in rows if row["model_id"] == model["model_id"]]
            require(sorted(int(row["evaluation_seed"]) for row in selected) == expected_seeds,
                    "Per-model evaluation seeds mismatch")
            if model["algorithm"] != "random":
                source = str(Path(model["checkpoint"]).resolve())
                pair = model["algorithm"], model["training_seed"]
                require(known_checkpoints.get(source) == pair, "Unknown model source")
                require(pair not in evaluated_pairs, "Duplicate evaluated training identity")
                evaluated_pairs.add(pair)
            for row in selected:
                require(row["algorithm"] == model["algorithm"] and
                        (row["training_seed"] == str(model["training_seed"])
                         if model["training_seed"] is not None else row["training_seed"] == ""),
                        "Evaluation row identity mismatch")
                require(close(sum(float(row[key]) for key in COMPONENTS), float(row["episode_return"])),
                        "Evaluation reward accounting mismatch")
            scores = [float(row["score"]) for row in selected]
            computed = {"mean_score": mean(scores), "std_score": pstdev(scores), "max_score": max(scores),
                        "mean_return": mean(float(row["episode_return"]) for row in selected),
                        "mean_episode_length": mean(int(row["episode_length"]) for row in selected),
                        "truncation_rate": mean(row["truncated"] == "True" for row in selected)}
            require(all(close(value, model[key]) for key, value in computed.items()), "Evaluation summary mismatch")
            records.append({"split": split, "algorithm": model["algorithm"],
                            "training_seed": model["training_seed"], **computed})
        require(evaluated_pairs == expected_pairs, "Evaluated grid mismatch")
        groups[split] = {}
        source_groups = comparison["algorithms" if split == "development" else "holdout_algorithms"]
        for algorithm in protocol["algorithms"] + ["random"]:
            selected = [row for row in records if row["split"] == split and row["algorithm"] == algorithm]
            group = {"mean_score": mean(row["mean_score"] for row in selected),
                     "std_of_model_mean_scores": pstdev(row["mean_score"] for row in selected),
                     "mean_return": mean(row["mean_return"] for row in selected),
                     "mean_episode_length": mean(row["mean_episode_length"] for row in selected),
                     "truncation_rate": mean(row["truncation_rate"] for row in selected),
                     "max_score": max(row["max_score"] for row in selected)}
            if algorithm != "random":
                require(close(group["mean_score"], source_groups[algorithm]["mean_score"]) and
                        close(group["std_of_model_mean_scores"], source_groups[algorithm]["std_of_model_mean_scores"]),
                        "Across-seed summary mismatch")
            groups[split][algorithm] = group
    expected_selection = max(protocol["algorithms"], key=lambda name: groups["development"][name]["mean_score"])
    require(comparison["selected_algorithm"] == expected_selection, "Development selection mismatch")
    destination = root / "analysis" / f"audit_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    destination.mkdir(parents=True, exist_ok=False)
    output = {"status": "completed", "source": str(path), "training": training, "groups": groups,
              "selected_algorithm": expected_selection, "selection_split": "development",
              "training_records": sum(run["records"] for run in training),
              "evaluation_records": len(records) * protocol["num_episodes"],
              "note": "Hashes fingerprint current source files, not a before/after evaluation comparison."}
    write_json(destination / "summary.json", output)
    with (destination / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return destination / "summary.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", required=True)
    args = parser.parse_args(argv)
    try:
        print(analyze_algorithm_experiment(args.comparison))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
