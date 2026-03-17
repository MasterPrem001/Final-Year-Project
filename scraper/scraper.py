import requests
import json
import os
import pandas as pd
from datetime import datetime

# Add at top of scraper.py:
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
JSON_FILE = str(BASE_DIR / 'crypto_master_prices.json')
EXCEL_FILE = str(BASE_DIR / 'crypto_master_history.xlsx')
COINS = {
    'BTC':  {'name': 'Bitcoin',  'coingecko_id': 'bitcoin'},
    'ETH':  {'name': 'Ethereum', 'coingecko_id': 'ethereum'},
    'SOL':  {'name': 'Solana',   'coingecko_id': 'solana'},
    'BNB':  {'name': 'BNB',      'coingecko_id': 'binancecoin'},
    'MATIC':{'name': 'Polygon',  'coingecko_id': 'matic-network'},
}


def fetch_all_prices():
    """
    Fetch prices for all 5 coins from up to 10 exchanges each.
    Returns a nested dict: { 'BTC': {'Binance': 104500.0, ...}, 'ETH': {...}, ... }
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'='*55}")
    print(f"  AI-DON Multi-Coin Scraper  |  {timestamp}")
    print(f"{'='*55}")

    all_prices = {coin: {} for coin in COINS}

    # ── 1. Binance ─────────────────────────────────────────────
    print("\n[1/10] Binance...", end=" ")
    pairs = {'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT', 'SOL': 'SOLUSDT',
             'BNB': 'BNBUSDT', 'MATIC': 'MATICUSDT'}
    ok = 0
    for coin, symbol in pairs.items():
        try:
            r = requests.get(
                f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}",
                timeout=5)
            all_prices[coin]['Binance'] = float(r.json()['price'])
            ok += 1
        except:
            pass
    print(f"{ok}/5 ✓")

    # ── 2. Coinbase ────────────────────────────────────────────
    print("[2/10] Coinbase...", end=" ")
    pairs = {'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'SOL': 'SOL-USD',
             'BNB': 'BNB-USD', 'MATIC': 'MATIC-USD'}
    ok = 0
    for coin, pair in pairs.items():
        try:
            r = requests.get(
                f"https://api.coinbase.com/v2/prices/{pair}/spot",
                timeout=5)
            all_prices[coin]['Coinbase'] = float(r.json()['data']['amount'])
            ok += 1
        except:
            pass
    print(f"{ok}/5 ✓")

    # ── 3. CoinGecko ───────────────────────────────────────────
    print("[3/10] CoinGecko...", end=" ")
    try:
        ids = ','.join(v['coingecko_id'] for v in COINS.values())
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd",
            timeout=8)
        data = r.json()
        ok = 0
        for coin, meta in COINS.items():
            gecko_id = meta['coingecko_id']
            if gecko_id in data and 'usd' in data[gecko_id]:
                all_prices[coin]['CoinGecko'] = float(data[gecko_id]['usd'])
                ok += 1
        print(f"{ok}/5 ✓")
    except Exception as e:
        print(f"0/5 ✗ ({e})")

    # ── 4. Kraken ──────────────────────────────────────────────
    print("[4/10] Kraken...", end=" ")
    # Kraken uses non-standard symbols for BTC
    pairs = {'BTC': 'XBTUSD', 'ETH': 'ETHUSD', 'SOL': 'SOLUSD',
             'BNB': None, 'MATIC': 'MATICUSD'}
    ok = 0
    for coin, pair in pairs.items():
        if pair is None:
            continue  # Kraken does not list BNB
        try:
            r = requests.get(
                f"https://api.kraken.com/0/public/Ticker?pair={pair}",
                timeout=5)
            result = r.json().get('result', {})
            if result:
                first_key = list(result.keys())[0]
                all_prices[coin]['Kraken'] = float(result[first_key]['c'][0])
                ok += 1
        except:
            pass
    print(f"{ok}/4 ✓ (BNB not on Kraken)")

    # ── 5. KuCoin ──────────────────────────────────────────────
    print("[5/10] KuCoin...", end=" ")
    pairs = {'BTC': 'BTC-USDT', 'ETH': 'ETH-USDT', 'SOL': 'SOL-USDT',
             'BNB': 'BNB-USDT', 'MATIC': 'MATIC-USDT'}
    ok = 0
    for coin, symbol in pairs.items():
        try:
            r = requests.get(
                f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}",
                timeout=5)
            price = r.json()['data']['price']
            if price:
                all_prices[coin]['KuCoin'] = float(price)
                ok += 1
        except:
            pass
    print(f"{ok}/5 ✓")

    # ── 6. Gemini ──────────────────────────────────────────────
    print("[6/10] Gemini...", end=" ")
    # Gemini has limited coin support
    pairs = {'BTC': 'btcusd', 'ETH': 'ethusd', 'SOL': 'solusd',
             'BNB': None, 'MATIC': 'maticusd'}
    ok = 0
    for coin, symbol in pairs.items():
        if symbol is None:
            continue
        try:
            r = requests.get(
                f"https://api.gemini.com/v1/pubticker/{symbol}",
                timeout=5)
            all_prices[coin]['Gemini'] = float(r.json()['last'])
            ok += 1
        except:
            pass
    print(f"{ok}/4 ✓ (BNB not on Gemini)")

    # ── 7. Bitstamp ────────────────────────────────────────────
    print("[7/10] Bitstamp...", end=" ")
    pairs = {'BTC': 'btcusd', 'ETH': 'ethusd', 'SOL': None,
             'BNB': None, 'MATIC': None}
    ok = 0
    for coin, symbol in pairs.items():
        if symbol is None:
            continue
        try:
            r = requests.get(
                f"https://www.bitstamp.net/api/v2/ticker/{symbol}/",
                timeout=5)
            all_prices[coin]['Bitstamp'] = float(r.json()['last'])
            ok += 1
        except:
            pass
    print(f"{ok}/2 ✓ (SOL/BNB/MATIC not on Bitstamp)")

    # ── 8. Bybit ───────────────────────────────────────────────
    print("[8/10] Bybit...", end=" ")
    pairs = {'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT', 'SOL': 'SOLUSDT',
             'BNB': 'BNBUSDT', 'MATIC': 'MATICUSDT'}
    ok = 0
    for coin, symbol in pairs.items():
        try:
            r = requests.get(
                f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}",
                timeout=5)
            price = r.json()['result']['list'][0]['lastPrice']
            all_prices[coin]['Bybit'] = float(price)
            ok += 1
        except:
            pass
    print(f"{ok}/5 ✓")

    # ── 9. OKX ─────────────────────────────────────────────────
    print("[9/10] OKX...", end=" ")
    pairs = {'BTC': 'BTC-USDT', 'ETH': 'ETH-USDT', 'SOL': 'SOL-USDT',
             'BNB': 'BNB-USDT', 'MATIC': 'MATIC-USDT'}
    ok = 0
    for coin, inst_id in pairs.items():
        try:
            r = requests.get(
                f"https://www.okx.com/api/v5/market/ticker?instId={inst_id}",
                timeout=5)
            price = r.json()['data'][0]['last']
            all_prices[coin]['OKX'] = float(price)
            ok += 1
        except:
            pass
    print(f"{ok}/5 ✓")

    # ── 10. Huobi (HTX) ────────────────────────────────────────
    print("[10/10] Huobi (HTX)...", end=" ")
    pairs = {'BTC': 'btcusdt', 'ETH': 'ethusdt', 'SOL': 'solusdt',
             'BNB': 'bnbusdt', 'MATIC': 'maticusdt'}
    ok = 0
    for coin, symbol in pairs.items():
        try:
            r = requests.get(
                f"https://api.huobi.pro/market/trade?symbol={symbol}",
                timeout=5)
            price = r.json()['tick']['data'][0]['price']
            all_prices[coin]['Huobi'] = float(price)
            ok += 1
        except:
            pass
    print(f"{ok}/5 ✓")

    return all_prices, timestamp


def compute_stats(coin_prices: dict) -> dict:
    """For each coin, compute median, min, max, spread."""
    stats = {}
    for coin, sources in coin_prices.items():
        values = list(sources.values())
        if not values:
            stats[coin] = {}
            continue
        values_sorted = sorted(values)
        n = len(values_sorted)
        median = (values_sorted[n // 2] if n % 2 != 0
                  else (values_sorted[n // 2 - 1] + values_sorted[n // 2]) / 2)
        stats[coin] = {
            'sources_count': n,
            'median':  round(median, 4),
            'mean':    round(sum(values) / n, 4),
            'min':     round(min(values), 4),
            'max':     round(max(values), 4),
            'spread%': round((max(values) - min(values)) / median * 100, 4),
        }
    return stats


def save_data(all_prices: dict, timestamp: str):
    if not any(all_prices.values()):
        print("\nNo prices retrieved — check your internet connection.")
        return

    stats = compute_stats(all_prices)

    # ── Print summary table ────────────────────────────────────
    print(f"\n{'─'*55}")
    print(f"  {'COIN':<8} {'SOURCES':>7}  {'MEDIAN PRICE':>14}  {'SPREAD':>8}")
    print(f"{'─'*55}")
    for coin, s in stats.items():
        if s:
            print(f"  {coin:<8} {s['sources_count']:>7}  "
                  f"${s['median']:>13,.4f}  {s['spread%']:>7.4f}%")
    print(f"{'─'*55}")

    # ── Update JSON (current prices only) ─────────────────────
    json_data = {}
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            try:
                json_data = json.load(f)
            except:
                json_data = {}

    for coin, sources in all_prices.items():
        json_data[coin] = {
            'name': COINS[coin]['name'],
            'last_updated': timestamp,
            'sources': {src: {'price': price, 'last_updated': timestamp}
                        for src, price in sources.items()},
            'stats': stats.get(coin, {}),
        }

    with open(JSON_FILE, 'w') as f:
        json.dump(json_data, f, indent=4)
    print(f"\n✅ JSON saved  → {JSON_FILE}")

    # ── Update Excel (full history, one row per run) ───────────
    # Build a flat row: Timestamp, BTC_Binance, BTC_Coinbase, ..., ETH_Binance, ...
    row = {'Timestamp': timestamp}
    for coin, sources in all_prices.items():
        for src, price in sources.items():
            row[f"{coin}_{src}"] = price
        # Also store the computed median
        if stats.get(coin):
            row[f"{coin}_MEDIAN"] = stats[coin]['median']

    df_new = pd.DataFrame([row])

    if not os.path.exists(EXCEL_FILE):
        df_new.to_excel(EXCEL_FILE, index=False)
    else:
        df_old = pd.read_excel(EXCEL_FILE)
        df_final = pd.concat([df_old, df_new], ignore_index=True, sort=False)
        df_final.to_excel(EXCEL_FILE, index=False)

    total = sum(len(s) for s in all_prices.values())
    print(f"✅ Excel saved → {EXCEL_FILE}  ({total} data points this run)\n")


if __name__ == "__main__":
    prices, ts = fetch_all_prices()
    save_data(prices, ts)