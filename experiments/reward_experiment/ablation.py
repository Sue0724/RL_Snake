"""Audit and combine a 2x3 state/reward grid with explicit source provenance."""

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
from common.metrics import REWARD_FIELDS, write_json
from evaluate import score_summary


REWARDS = ("sparse", "distance", "distance_step")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-7)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_source(comparison_path, state, rewards):
    path = Path(comparison_path).resolve()
    source = read_json(path)
    require(source["status"] == "completed", "Source experiment is incomplete")
    p = source["protocol"]
    require(p["environment_revision"] == "tail_occupancy_fixed", "Environment revision mismatch")
    require(len(p["seeds"]) == len(set(p["seeds"])), "Duplicate training seeds")
    require(p["run_type"] in ("debug", "official"), "Unknown run type")
    require(p["run_type"] != "official" or len(p["seeds"]) >= 3, "Official grid needs >=3 seeds")
    root, records, hashes = path.parent, [], {str(path): fingerprint(path)}

    def track(file):
        file = file.resolve()
        hashes[str(file)] = fingerprint(file)
        return file

    for reward in rewards:
        runs = [run for run in source["training_runs"]
                if run.get("state_mode", p["base_config"]["state_mode"]) == state
                and run.get("reward_mode", p["base_config"]["reward_mode"]) == reward]
        require(len(runs) == len(p["seeds"]) and {run["seed"] for run in runs} == set(p["seeds"]),
                "Source cell has missing or duplicate training seeds")
        evaluation_key = state if "state_modes" in p else reward
        evaluation_dir = root / source["evaluation_dirs"][evaluation_key]
        evaluation = read_json(track(evaluation_dir / "summary.json"))
        settings = read_json(track(evaluation_dir / "config.json"))
        rows = read_rows(track(evaluation_dir / "metrics.csv"))
        expected_seeds = list(range(p["eval_seed"], p["eval_seed"] + p["num_episodes"]))
        require(evaluation["status"] == "completed", "Evaluation incomplete")
        require(settings["protocol"]["evaluation_seeds"] == expected_seeds, "Evaluation protocol seeds mismatch")
        require(all(settings["protocol"][key] is False for key in ("exploration", "network_update", "replay_write")),
                "Evaluation training flags enabled")
        require(len(evaluation["models"]) == len(runs) and len(rows) == len(runs) * p["num_episodes"],
                "Evaluation grid size mismatch")
        for run in sorted(runs, key=lambda item: item["seed"]):
            directory = root / run["run_dir"]
            config = read_json(track(directory / "config.json"))
            summary = read_json(track(directory / "summary.json"))
            logs = read_rows(track(directory / "metrics.csv"))
            checkpoint_path = track(root / run["checkpoint"])
            checkpoint = read_checkpoint(checkpoint_path)
            require(config == checkpoint["config"], "Checkpoint configuration mismatch")
            require((config["algorithm"], config["state_mode"], config["reward_mode"], config["seed"])
                    == ("dqn", state, reward, run["seed"]), "Training configuration identity mismatch")
            require({k: v for k, v in config.items() if k not in ("state_mode", "reward_mode", "seed")}
                    == {k: v for k, v in p["base_config"].items() if k not in ("state_mode", "reward_mode", "seed")},
                    "Run differs from source protocol configuration")
            require(run["status"] == summary["status"] == "completed", "Training incomplete")
            budget = p["total_steps"]
            updates = max(0, budget - max(config["min_buffer_size"], config["batch_size"]) + 1)
            require(summary["global_step"] == checkpoint["global_step"] == budget, "Training budget mismatch")
            require(summary["update_count"] == checkpoint["update_count"] == updates, "Training updates mismatch")
            cumulative = 0
            for row in logs:
                cumulative += int(row["episode_length"])
                require(int(row["global_step"]) == cumulative, "Training cumulative steps mismatch")
                require((row["state_mode"], row["reward_mode"], row["algorithm"], int(row["seed"]))
                        == (state, reward, "dqn", run["seed"]), "Training CSV identity mismatch")
                expected = max(config["epsilon_end"], config["epsilon_start"] *
                               config["epsilon_decay"] ** cumulative)
                require(close(float(row["epsilon"]), expected), "Training epsilon mismatch")
                require(not row["loss"] or math.isfinite(float(row["loss"])), "Training loss is non-finite")
                require(close(sum(float(row[key]) for key in REWARD_FIELDS), float(row["episode_return"])),
                        "Training reward accounting mismatch")
            require(cumulative == budget, "Training CSV budget mismatch")
            require(close(summary["epsilon"], checkpoint["epsilon"]) and
                    close(checkpoint["epsilon"], float(logs[-1]["epsilon"])), "Final epsilon mismatch")
            models = [model for model in evaluation["models"] if model["training_seed"] == run["seed"]]
            require(len(models) == 1, "Evaluation model seed mismatch")
            model = models[0]
            require(Path(model["checkpoint"]).resolve() == checkpoint_path, "Evaluation checkpoint source mismatch")
            require(model["algorithm"] == "dqn", "Evaluation algorithm mismatch")
            matches = [entry for entry in settings["models"] if entry["model_id"] == model["model_id"]]
            require(len(matches) == 1 and matches[0]["config"] == config, "Evaluation config source mismatch")
            selected = [row for row in rows if row["model_id"] == model["model_id"]]
            require(sorted(int(row["evaluation_seed"]) for row in selected) == expected_seeds,
                    "Per-model evaluation seeds mismatch")
            typed = []
            for row in selected:
                require(row["algorithm"] == "dqn" and int(row["training_seed"]) == run["seed"],
                        "Evaluation CSV identity mismatch")
                require(close(sum(float(row[key]) for key in REWARD_FIELDS), float(row["episode_return"])),
                        "Evaluation reward accounting mismatch")
                typed.append({**{key: float(row[key]) for key in
                                 ("score", "episode_return", "episode_length", *REWARD_FIELDS)},
                              "truncated": row["truncated"] == "True"})
            computed = score_summary(typed)
            require(all(close(computed[key], model[key]) for key in computed if key != "mean_reward_components"),
                    "Evaluation score summary mismatch")
            require(all(close(computed["mean_reward_components"][key], model["mean_reward_components"][key])
                        for key in REWARD_FIELDS), "Evaluation component summary mismatch")
            records.append({"state_mode": state, "reward_mode": reward, "training_seed": run["seed"],
                            **{key: value for key, value in computed.items() if key != "mean_reward_components"},
                            "parameter_count": sum(t.numel() for t in checkpoint["online_net"].values()),
                            "training_records": len(logs), "comparison_source": str(path),
                            "checkpoint": str(checkpoint_path), "evaluation_dir": str(evaluation_dir.resolve())})
    return p, records, hashes


def summarize_cells(records, seeds):
    expected = {(state, reward, seed) for state in ("v1", "v2") for reward in REWARDS for seed in seeds}
    indexed = {(row["state_mode"], row["reward_mode"], row["training_seed"]): row for row in records}
    require(set(indexed) == expected and len(records) == len(expected), "Incomplete or duplicate factorial grid")
    cells = {}
    for state in ("v1", "v2"):
        for reward in REWARDS:
            rows = [indexed[state, reward, seed] for seed in seeds]
            scores = [row["mean_score"] for row in rows]
            cells[f"{state}/{reward}"] = {"mean_score": mean(scores),
                "std_of_model_mean_scores": pstdev(scores), "per_seed_scores": scores}
    interactions = {}
    for reward in REWARDS[1:]:
        gains = {state: [indexed[state, reward, seed]["mean_score"] -
                         indexed[state, "sparse", seed]["mean_score"] for seed in seeds] for state in ("v1", "v2")}
        paired = [b - a for a, b in zip(gains["v1"], gains["v2"])]
        interactions[reward] = {"v1_gains": gains["v1"], "v2_gains": gains["v2"],
                                "per_seed_interaction": paired, "mean_interaction": mean(paired),
                                "std_of_paired_interactions": pstdev(paired)}
    return cells, interactions


def aggregate_ablation(state_comparison, v2_reward_comparison, v1_reward_comparison,
                       output_dir="results/ablation_experiments"):
    specifications = ((state_comparison, "v1", ("sparse",)),
                      (v2_reward_comparison, "v2", REWARDS),
                      (v1_reward_comparison, "v1", REWARDS[1:]))
    records, protocols, hashes = [], [], {}
    for source, state, rewards in specifications:
        protocol, rows, files = audit_source(source, state, rewards)
        protocols.append(protocol)
        records.extend(rows)
        hashes.update(files)
    common_keys = ("run_type", "seeds", "total_steps", "num_episodes", "eval_seed", "environment_revision", "torch_threads")
    signature = lambda p: ({key: p[key] for key in common_keys},
                           {k: v for k, v in p["base_config"].items() if k not in ("state_mode", "reward_mode", "seed")})
    require(all(signature(p) == signature(protocols[0]) for p in protocols), "Cross-source protocol mismatch")
    cells, interactions = summarize_cells(records, protocols[0]["seeds"])
    require(all(fingerprint(Path(path)) == value for path, value in hashes.items()), "Source changed during audit")
    root = Path(output_dir).resolve() / f"factorial_{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid4().hex[:8]}"
    root.mkdir(parents=True, exist_ok=False)
    result = {"status": "completed", "protocol": {**{key: protocols[0][key] for key in common_keys},
                "base_config": protocols[0]["base_config"], "states": ["v1", "v2"], "rewards": list(REWARDS),
                "interaction_definition": "(V2 shaped - V2 sparse) - (V1 shaped - V1 sparse)", "std_ddof": 0},
              "sources": [str(Path(source).resolve()) for source, _, _ in specifications],
              "new_training_models": len(protocols[0]["seeds"]) * 2,
              "reused_training_models": len(protocols[0]["seeds"]) * 4,
              "training_records": sum(row["training_records"] for row in records),
              "evaluation_records": sum(row["num_episodes"] for row in records),
              "source_unchanged_during_audit": True, "source_sha256": hashes,
              "records": records, "cells": cells, "interactions": interactions}
    write_json(root / "comparison.json", result)
    with (root / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return root / "comparison.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state_comparison", required=True)
    parser.add_argument("--v2_reward_comparison", required=True)
    parser.add_argument("--v1_reward_comparison", required=True)
    parser.add_argument("--output_dir", default="results/ablation_experiments")
    args = parser.parse_args(argv)
    try:
        print(aggregate_ablation(**vars(args)))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
