import random
from typing import Dict, List, Optional

import numpy as np

from oracle_nodes.node_simulator import get_node_profiles


def _detect_gradient_outliers(gradient_norms: List[float], threshold: float = 2.5) -> List[bool]:
    """
    Detect suspicious client updates using robust z-score on gradient norms.

    AI-DON FL logic:
    - Honest nodes should have similar gradient magnitudes.
    - Poisoned clients usually send abnormally large norms.
    """
    norms = np.array(gradient_norms, dtype=float)
    median = float(np.median(norms))
    mad = float(np.median(np.abs(norms - median)))

    # If all norms are almost equal, no outliers are flagged.
    if mad < 1e-9:
        return [False] * len(norms)

    robust_z = 0.6745 * (norms - median) / mad
    return (np.abs(robust_z) > threshold).tolist()


def simulate_fl_rounds(
    rounds: int = 3,
    start_accuracy: float = 72.0,
    seed: Optional[int] = None,
) -> Dict:
    """
    Simulate AI-DON Federated Learning rounds across 5 oracle nodes.

    Requirements implemented:
    - 3 rounds by default
    - Honest nodes contribute useful local training
    - DeltaNode sends poisoned (high-norm) gradients
    - Outlier detection on gradient norms
    - Reputation-weighted FedAvg aggregation

    Weighted aggregate formula used:
      global_weight = sum(n_samples_i * rep_norm_i * local_accuracy_i) / total_weight
    """
    if rounds <= 0:
        raise ValueError("rounds must be >= 1")

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    node_profiles = get_node_profiles()
    global_accuracy = float(start_accuracy)
    history: List[Dict] = []

    for round_id in range(1, rounds + 1):
        node_updates: List[Dict] = []
        gradient_norms: List[float] = []

        # --- Local training simulation on each node ---
        for node in node_profiles:
            rep_norm = float(node["reputation"]) / 1000.0
            rep_norm = max(0.0, min(1.0, rep_norm))

            # Each node trains on private local samples only.
            n_samples = random.randint(280, 1200)

            if node["is_malicious"]:
                # Poisoned client: very high gradient norm + degraded local metric.
                gradient_norm = random.uniform(11.0, 17.0)
                local_accuracy = max(50.0, global_accuracy - random.uniform(1.2, 3.6))
            else:
                # Honest clients improve slightly around the current global model.
                gradient_norm = random.uniform(0.9, 2.6)
                local_accuracy = min(99.0, global_accuracy + random.uniform(0.8, 2.4))

            gradient_norms.append(gradient_norm)
            node_updates.append(
                {
                    "node_id": node["node_id"],
                    "node_name": node["name"],
                    "reputation": int(node["reputation"]),
                    "rep_norm": round(rep_norm, 6),
                    "n_samples": int(n_samples),
                    "local_accuracy": round(float(local_accuracy), 6),
                    "gradient_norm": round(float(gradient_norm), 6),
                    "is_malicious": bool(node["is_malicious"]),
                }
            )

        # --- Poisoning detection using gradient norm outlier check ---
        outlier_flags = _detect_gradient_outliers(gradient_norms, threshold=2.5)
        for idx, flagged in enumerate(outlier_flags):
            node_updates[idx]["poisoning_detected"] = bool(flagged)

        # --- Reputation-weighted FedAvg aggregation ---
        # Exclude detected poisoned updates from aggregation.
        valid_updates = [row for row in node_updates if not row["poisoning_detected"]]

        if not valid_updates:
            # Safety fallback if all updates are flagged.
            fedavg_accuracy = global_accuracy
            total_weight = 0.0
        else:
            weighted_terms = [
                row["n_samples"] * row["rep_norm"] * row["local_accuracy"]
                for row in valid_updates
            ]
            weights = [row["n_samples"] * row["rep_norm"] for row in valid_updates]
            total_weight = float(sum(weights))

            if total_weight <= 1e-12:
                fedavg_accuracy = global_accuracy
            else:
                fedavg_accuracy = float(sum(weighted_terms) / total_weight)

        # Smoothly move global model toward aggregated local result.
        # This keeps progression realistic while still showing consistent improvement.
        global_accuracy = (0.55 * global_accuracy) + (0.45 * fedavg_accuracy)
        global_accuracy = max(0.0, min(99.0, global_accuracy))

        # Ensure round-to-round monotonic improvement for the demo signal.
        if history and global_accuracy <= history[-1]["global_accuracy"]:
            global_accuracy = min(99.0, history[-1]["global_accuracy"] + random.uniform(0.15, 0.6))

        round_result = {
            "round": round_id,
            "global_accuracy": round(float(global_accuracy), 6),
            "fedavg_accuracy": round(float(fedavg_accuracy), 6),
            "detected_poisoned_nodes": [
                row["node_id"] for row in node_updates if row["poisoning_detected"]
            ],
            "used_nodes": len(valid_updates),
            "rejected_nodes": len(node_updates) - len(valid_updates),
            "total_weight": round(total_weight, 6),
            "node_updates": node_updates,
        }
        history.append(round_result)

    return {
        "start_accuracy": round(float(start_accuracy), 6),
        "final_accuracy": round(float(global_accuracy), 6),
        "total_rounds": rounds,
        "rounds": history,
    }


def run_fl_simulation(rounds: int = 3, seed: Optional[int] = None) -> Dict:
    """Convenience wrapper used by backend endpoints."""
    return simulate_fl_rounds(rounds=rounds, start_accuracy=72.0, seed=seed)


if __name__ == "__main__":
    output = run_fl_simulation(rounds=3, seed=21)
    print("FL Summary:", {
        "start_accuracy": output["start_accuracy"],
        "final_accuracy": output["final_accuracy"],
        "total_rounds": output["total_rounds"],
    })

    print("\nPer-round results:")
    for item in output["rounds"]:
        print(
            f"Round {item['round']}: "
            f"global={item['global_accuracy']:.3f}% | "
            f"fedavg={item['fedavg_accuracy']:.3f}% | "
            f"rejected={item['rejected_nodes']} | "
            f"detected={item['detected_poisoned_nodes']}"
        )
