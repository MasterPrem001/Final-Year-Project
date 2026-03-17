import os
import time
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ai_engine.anomaly_detector import detect_anomalies_and_consensus
from ai_engine.fl_simulator import run_fl_simulation
from .blockchain import check_connection, push_price_onchain, read_latest_price
from oracle_nodes.node_simulator import get_node_profiles, simulate_node_submissions
from scraper.scraper import COINS, fetch_all_prices


app = FastAPI(title="AI-DON Backend", version="1.0.0")

# Frontend runs separately (Vite), so permissive CORS simplifies local integration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SUPPORTED_COINS = sorted(COINS.keys())

# In-memory application state (prototype mode, no database).
STATE: Dict = {
    "round_count": 0,
    "latest": None,
    "pipeline_history": [],
    "price_history": [],
    "fl_history": [],
}


def _median(values: List[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        raise ValueError("Cannot compute median of empty list")
    if n % 2 == 1:
        return float(ordered[n // 2])
    return float((ordered[n // 2 - 1] + ordered[n // 2]) / 2.0)


def _get_coin_sources(all_prices: Dict[str, Dict[str, float]], coin: str) -> Dict[str, float]:
    coin_sources = all_prices.get(coin, {})
    return {src: float(price) for src, price in coin_sources.items() if isinstance(price, (int, float))}


def _build_node_status(latest_round: Optional[Dict]) -> List[Dict]:
    """
    Merge static node profile metadata with the latest AI metrics from detection output.
    """
    profiles = get_node_profiles()
    if not latest_round:
        return profiles

    submission_by_node = {
        row["node_id"]: row for row in latest_round.get("submissions", [])
    }

    merged: List[Dict] = []
    for profile in profiles:
        metrics = submission_by_node.get(profile["node_id"], {})
        merged.append(
            {
                **profile,
                "latest_submitted_price": metrics.get("submitted_price"),
                "latest_latency_ms": metrics.get("latency_ms"),
                "latest_deviation_from_true": metrics.get("deviation_from_true"),
                "latest_z_score": metrics.get("z_score"),
                "latest_if_score": metrics.get("if_score"),
                "latest_trust_weight": metrics.get("trust_weight"),
                "latest_is_anomaly": metrics.get("is_anomaly"),
            }
        )
    return merged


@app.get("/api/health")
def health() -> Dict:
    return {
        "status": "ok",
        "service": "ai-don-backend",
        "time": datetime.utcnow().isoformat() + "Z",
        "supported_coins": SUPPORTED_COINS,
    }


@app.get("/api/run-pipeline")
def run_pipeline(coin: str = Query("ETH", description="Asset symbol, e.g., ETH or BTC")) -> Dict:
    coin = coin.upper().strip()
    if coin not in SUPPORTED_COINS:
        raise HTTPException(status_code=400, detail=f"Unsupported coin '{coin}'. Use one of {SUPPORTED_COINS}")

    all_prices, scrape_timestamp = fetch_all_prices()
    coin_sources = _get_coin_sources(all_prices, coin)

    if not coin_sources:
        raise HTTPException(status_code=502, detail=f"No valid price sources available for {coin}")

    # AI-DON truth estimate for node simulation is the source median.
    true_price_estimate = _median(list(coin_sources.values()))

    node_submissions = simulate_node_submissions(true_price=true_price_estimate, coin=coin)
    detection_output = detect_anomalies_and_consensus(node_submissions, asset=coin)

    STATE["round_count"] += 1
    round_id = int(STATE["round_count"])

    consensus = {**detection_output["consensus"], "round_id": round_id, "timestamp": scrape_timestamp}
    submissions = detection_output["submissions"]

    blockchain_status = push_price_onchain(
        asset=coin,
        price=float(consensus["final_price"]),
        confidence=int(consensus["confidence"]),
        nodes_used=int(consensus["nodes_used"]),
        nodes_rejected=int(consensus["nodes_rejected"]),
    )

    round_result = {
        "round_id": round_id,
        "asset": coin,
        "timestamp": scrape_timestamp,
        "source_prices": coin_sources,
        "source_count": len(coin_sources),
        "true_price_estimate": round(float(true_price_estimate), 6),
        "submissions": submissions,
        "consensus": consensus,
        "blockchain": blockchain_status,
        "onchain": blockchain_status,
    }

    STATE["latest"] = round_result
    STATE["pipeline_history"].append(round_result)
    STATE["price_history"].append(
        {
            "round_id": round_id,
            "asset": coin,
            "timestamp": scrape_timestamp,
            "consensus_price": consensus["final_price"],
            "confidence": consensus["confidence"],
            "nodes_used": consensus["nodes_used"],
            "nodes_rejected": consensus["nodes_rejected"],
        }
    )

    return round_result


@app.get("/api/blockchain-status")
def blockchain_status() -> Dict:
    return check_connection()


@app.get("/api/read-price")
def read_price(asset: str = Query("ETH", description="Asset symbol, e.g., ETH or BTC")) -> Dict:
    symbol = asset.upper().strip()
    return read_latest_price(symbol)


@app.get("/api/latest")
def latest() -> Dict:
    if STATE["latest"] is None:
        return {"message": "No pipeline rounds executed yet."}
    return STATE["latest"]


@app.get("/api/nodes")
def nodes() -> Dict:
    latest_round = STATE.get("latest")
    node_rows = _build_node_status(latest_round)

    return {
        "count": len(node_rows),
        "nodes": node_rows,
        "latest_round_id": latest_round.get("round_id") if latest_round else None,
    }


@app.get("/api/fl-simulation")
def fl_simulation(rounds: int = Query(3, ge=1, le=20)) -> Dict:
    simulation = run_fl_simulation(rounds=rounds)
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "result": simulation,
    }
    STATE["fl_history"].append(entry)
    return entry


@app.get("/api/price-history")
def price_history(asset: Optional[str] = Query(None, description="Optional asset filter, e.g., ETH")) -> Dict:
    rows = STATE["price_history"]
    if asset:
        symbol = asset.upper().strip()
        rows = [row for row in rows if row["asset"] == symbol]

    return {
        "count": len(rows),
        "history": rows,
    }


@app.get("/api/stats")
def stats() -> Dict:
    rounds_completed = len(STATE["pipeline_history"])

    total_submissions = 0
    total_anomalies = 0
    for round_item in STATE["pipeline_history"]:
        submissions = round_item.get("submissions", [])
        total_submissions += len(submissions)
        total_anomalies += sum(1 for row in submissions if row.get("is_anomaly"))

    detection_rate = 0.0
    if total_submissions > 0:
        detection_rate = (total_anomalies / total_submissions) * 100.0

    return {
        "rounds_completed": rounds_completed,
        "anomalies_caught": total_anomalies,
        "total_submissions": total_submissions,
        "detection_rate_percent": round(detection_rate, 4),
        "active_nodes": len(get_node_profiles()),
        "data_sources": 10,
        "latest_round_id": STATE["latest"]["round_id"] if STATE["latest"] else None,
        "fl_runs": len(STATE["fl_history"]),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
