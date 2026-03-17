import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


Z_SCORE_THRESHOLD = 2.0
IF_CONTAMINATION = 0.2
RANDOM_STATE = 42


def _safe_minmax(values: np.ndarray) -> np.ndarray:
    """Min-max normalize to [0, 1] while handling constant arrays safely."""
    if values.size == 0:
        return values
    min_v = float(np.min(values))
    max_v = float(np.max(values))
    if math.isclose(min_v, max_v):
        return np.ones_like(values, dtype=float)
    return (values - min_v) / (max_v - min_v)


def _compute_z_scores(prices: np.ndarray) -> np.ndarray:
    """Compute classic z-scores, returning zeros when std deviation is near zero."""
    mean_price = float(np.mean(prices))
    std_price = float(np.std(prices, ddof=0))
    if std_price < 1e-12:
        return np.zeros_like(prices, dtype=float)
    return (prices - mean_price) / std_price


def _compute_confidence(
    submissions: List[Dict],
    used_nodes: int,
    rejected_nodes: int,
    final_price: float,
) -> int:
    """
    Build a 0-100 confidence score for AI-DON consensus quality.

    Confidence combines three signals:
    1) Participation ratio (more accepted nodes => higher confidence)
    2) Rejection ratio (more anomalies rejected => lower confidence)
    3) Weighted agreement (lower average relative error among accepted nodes => higher confidence)
    """
    total_nodes = max(len(submissions), 1)
    participation = used_nodes / total_nodes
    rejection_penalty = rejected_nodes / total_nodes

    accepted = [row for row in submissions if not row["is_anomaly"]]
    if not accepted:
        return 0

    # Agreement score uses relative error against consensus among accepted nodes.
    rel_errors = [abs(row["submitted_price"] - final_price) / max(final_price, 1e-9) for row in accepted]
    avg_rel_error = float(np.mean(rel_errors))

    # Convert relative error to a bounded quality term.
    # 0.5% error -> ~0.5 quality, very low error -> near 1.
    agreement = max(0.0, min(1.0, 1.0 - (avg_rel_error / 0.01)))

    raw_conf = (0.55 * participation) + (0.35 * agreement) + (0.10 * (1.0 - rejection_penalty))
    return int(round(max(0.0, min(1.0, raw_conf)) * 100))


def run_anomaly_detection(
    submissions: List[Dict],
    asset: str = "ETH",
) -> Tuple[List[Dict], Dict]:
    """
    Execute AI-DON 4-stage anomaly detection and consensus pipeline.

    Stage 1: Z-score screening (> 2.0 sigma from mean => suspicious)
    Stage 2: Isolation Forest on [submitted_price, z_score, deviation_from_true]
    Stage 3: Trust weighting (rep_norm * if_score_norm * z_penalty), 0 if anomaly
    Stage 4: Trust-weighted consensus over non-anomalous submissions

    Returns:
      enriched_submissions, consensus_result
    """
    if not submissions:
        raise ValueError("submissions cannot be empty")

    frame = pd.DataFrame(submissions).copy()

    required_columns = {"node_id", "submitted_price", "reputation", "deviation_from_true"}
    missing_columns = required_columns - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required submission fields: {sorted(missing_columns)}")

    # --- Stage 1: Z-score screening ---
    prices = frame["submitted_price"].astype(float).to_numpy()
    z_scores = _compute_z_scores(prices)
    frame["z_score"] = z_scores
    frame["z_anomaly"] = np.abs(frame["z_score"]) > Z_SCORE_THRESHOLD

    # --- Stage 2: Isolation Forest ---
    feature_matrix = frame[["submitted_price", "z_score", "deviation_from_true"]].astype(float).to_numpy()

    # For very small batches, keep contamination bounded and valid.
    contamination = min(IF_CONTAMINATION, max(0.01, 1.0 / len(frame)))
    if_model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=RANDOM_STATE,
    )
    if_model.fit(feature_matrix)

    # decision_function: higher = more normal
    if_scores = if_model.decision_function(feature_matrix)
    if_preds = if_model.predict(feature_matrix)  # -1 anomaly, 1 normal

    frame["if_score"] = if_scores
    frame["if_anomaly"] = if_preds == -1

    # --- Stage 3: Trust weight formula ---
    rep_norm = np.clip(frame["reputation"].astype(float).to_numpy() / 1000.0, 0.0, 1.0)

    # z_penalty smoothly discounts farther points even if not hard-flagged.
    z_penalty = 1.0 / (1.0 + np.abs(z_scores))

    # AI-DON rule: any anomaly from either detector is excluded from consensus.
    is_anomaly = np.logical_or(frame["z_anomaly"].to_numpy(), frame["if_anomaly"].to_numpy())

    # Normalize IF scores only across non-anomalous rows so anomaly outliers do not skew
    # honest-node scaling; anomalies remain at 0.
    if_score_norm = np.zeros(len(if_scores), dtype=float)
    non_anomaly_mask = ~is_anomaly
    if np.any(non_anomaly_mask):
        honest_scores = if_scores[non_anomaly_mask]
        honest_normalized = _safe_minmax(honest_scores)
        if_score_norm[non_anomaly_mask] = honest_normalized

    trust = rep_norm * if_score_norm * z_penalty
    trust = np.where(is_anomaly, 0.0, trust)
    trust = np.where(trust < 0.0, 0.0, trust)

    frame["rep_norm"] = rep_norm
    frame["if_score_norm"] = if_score_norm
    frame["z_penalty"] = z_penalty
    frame["is_anomaly"] = is_anomaly
    frame["trust_weight"] = trust

    # --- Stage 4: Weighted consensus ---
    non_anomalous = frame[~frame["is_anomaly"]].copy()

    if len(non_anomalous) == 0:
        # Fallback when all nodes are flagged: use median as robust estimate.
        final_price = float(np.median(prices))
        used_nodes = 0
        rejected_nodes = int(len(frame))
    else:
        weighted_sum = float((non_anomalous["submitted_price"] * non_anomalous["trust_weight"]).sum())
        trust_sum = float(non_anomalous["trust_weight"].sum())

        if trust_sum <= 1e-12:
            final_price = float(non_anomalous["submitted_price"].median())
        else:
            final_price = weighted_sum / trust_sum

        used_nodes = int(len(non_anomalous))
        rejected_nodes = int(len(frame) - len(non_anomalous))

    median_price = float(np.median(prices))
    deviation_from_median = ((final_price - median_price) / max(median_price, 1e-9)) * 100.0
    confidence = _compute_confidence(frame.to_dict(orient="records"), used_nodes, rejected_nodes, final_price)

    rejected_node_ids = frame.loc[frame["is_anomaly"], "node_id"].tolist()

    # Round output fields for clean API/frontend rendering.
    round_cols = [
        "submitted_price",
        "deviation_from_true",
        "z_score",
        "if_score",
        "rep_norm",
        "if_score_norm",
        "z_penalty",
        "trust_weight",
    ]
    for col in round_cols:
        frame[col] = frame[col].astype(float).round(6)

    enriched_submissions = frame.to_dict(orient="records")

    consensus_result = {
        "asset": asset,
        "final_price": round(float(final_price), 6),
        "confidence": int(confidence),
        "nodes_used": used_nodes,
        "nodes_rejected": rejected_nodes,
        "rejected_nodes": rejected_node_ids,
        "median_price": round(median_price, 6),
        "deviation_from_median": round(float(deviation_from_median), 6),
    }

    return enriched_submissions, consensus_result


def detect_anomalies_and_consensus(
    submissions: List[Dict],
    asset: str = "ETH",
) -> Dict:
    """
    Convenience wrapper returning a single object for backend routes.
    """
    enriched_submissions, consensus = run_anomaly_detection(submissions=submissions, asset=asset)
    return {
        "submissions": enriched_submissions,
        "consensus": consensus,
    }


if __name__ == "__main__":
    # Local smoke test to verify the full AI pipeline independently.
    from oracle_nodes.node_simulator import simulate_node_submissions

    true_price_estimate = 3142.50
    node_submissions = simulate_node_submissions(true_price=true_price_estimate, coin="ETH", seed=7)

    result = detect_anomalies_and_consensus(node_submissions, asset="ETH")
    print("Consensus:", result["consensus"])
    print("\nNode Decisions:")
    for item in result["submissions"]:
        print(
            item["node_id"],
            "price=", item["submitted_price"],
            "z=", item["z_score"],
            "if=", item["if_score"],
            "trust=", item["trust_weight"],
            "anomaly=", item["is_anomaly"],
        )
