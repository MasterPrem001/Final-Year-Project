import hashlib
import random
import time
from typing import Dict, List, Optional


# Fixed oracle node registry used across AI-DON rounds.
# Reputation scale is 0-1000 as defined in the project spec.
NODE_PROFILES: List[Dict] = [
    {
        "node_id": "node-alpha",
        "name": "AlphaNode",
        "region": "US-East",
        "reputation": 962,
        "is_malicious": False,
    },
    {
        "node_id": "node-beta",
        "name": "BetaNode",
        "region": "EU-West",
        "reputation": 841,
        "is_malicious": False,
    },
    {
        "node_id": "node-gamma",
        "name": "GammaNode",
        "region": "Asia-SG",
        "reputation": 778,
        "is_malicious": False,
    },
    {
        "node_id": "node-delta",
        "name": "DeltaNode",
        "region": "Unknown",
        "reputation": 412,
        "is_malicious": True,
    },
    {
        "node_id": "node-epsilon",
        "name": "EpsilonNode",
        "region": "IN-West",
        "reputation": 893,
        "is_malicious": False,
    },
]


def _generate_tx_hash(node_id: str, coin: str, submitted_price: float) -> str:
    """Generate a deterministic-looking pseudo tx hash for demo rounds."""
    entropy = f"{node_id}|{coin}|{submitted_price:.8f}|{time.time_ns()}|{random.random()}"
    digest = hashlib.sha256(entropy.encode("utf-8")).hexdigest()
    return f"0x{digest}"


def get_node_profiles() -> List[Dict]:
    """Return static node metadata used by the simulator."""
    return [dict(node) for node in NODE_PROFILES]


def simulate_node_submissions(
    true_price: float,
    coin: str = "ETH",
    seed: Optional[int] = None,
) -> List[Dict]:
    """
    Simulate one oracle reporting round for 5 AI-DON nodes.

    AI-DON behavior:
    - Honest nodes submit around true price using Gaussian noise in ±0.2-0.4% range.
    - DeltaNode is malicious and inflates price by +9% to +14%.

    Returns per-node submissions containing:
    node_id, submitted_price, reputation, deviation_from_true, latency_ms, tx_hash
    """
    if true_price <= 0:
        raise ValueError("true_price must be greater than zero")
    if seed is not None:
        random.seed(seed)
        import numpy as np
        np.random.seed(seed)

    submissions: List[Dict] = []

    for node in NODE_PROFILES:
        is_malicious = node["is_malicious"]

        if is_malicious:
            # Malicious node performs manipulation attack by inflating quote.
            inflation_pct = random.uniform(9.0, 14.0)
            submitted_price = true_price * (1 + inflation_pct / 100.0)
            latency_ms = random.randint(220, 900)
        else:
            # Honest nodes add small market micro-noise around true price.
            # sigma is chosen from 0.2%-0.4%, then clipped to avoid unrealistic tails.
            sigma = random.uniform(0.002, 0.004)
            pct_noise = random.gauss(0.0, sigma)
            pct_noise = max(-0.004, min(0.004, pct_noise))
            submitted_price = true_price * (1 + pct_noise)
            latency_ms = random.randint(85, 340)

        deviation_pct = ((submitted_price - true_price) / true_price) * 100.0

        submissions.append(
            {
                "node_id": node["node_id"],
                "node_name": node["name"],
                "region": node["region"],
                "submitted_price": round(submitted_price, 6),
                "reputation": int(node["reputation"]),
                "deviation_from_true": round(deviation_pct, 6),
                "latency_ms": latency_ms,
                "tx_hash": _generate_tx_hash(node["node_id"], coin, submitted_price),
                "is_malicious": is_malicious,
                "asset": coin,
            }
        )

    return submissions


if __name__ == "__main__":
    # Quick standalone test run for local development.
    sample_true_price = 3142.50
    round_submissions = simulate_node_submissions(sample_true_price, coin="ETH")
    for row in round_submissions:
        print(row)